"""
Geoapify Places Collector
Replaces OSMCollector – fetches tourist POIs via the Geoapify Places API.
Output dict shape is identical to the old OSMCollector so the pipeline
needs zero changes beyond swapping the import.

Requires:  GEOAPIFY_API_KEY in .env
"""

import hashlib
import logging
import os
import time
from typing import Dict, List

import requests
from dotenv import load_dotenv
from api_collectors.geo_utils import distance_meters
from api_collectors.text_utils import token_set_ratio

repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(dotenv_path=os.path.join(repo_root, ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Geoapify category strings we query for – mirrors what the old Overpass
# query fetched (attractions, viewpoints, peaks, waterfalls, parks, …).
# Each entry has been validated against the live API (400 → removed).
_GEO_CATEGORIES = ",".join([
    "tourism.attraction",
    "tourism.sights",
    "tourism.sights.memorial",
    "tourism.sights.place_of_worship",
    "natural",
    "natural.mountain",
    "natural.water",
    "natural.water.hot_spring",
    "natural.forest",
    "entertainment.museum",
    "entertainment.culture",
    "leisure.park",
    "sport",
    "heritage",
    "religion",
    "religion.place_of_worship",
])


class GeoapifyCollector:
    """Collects Points of Interest from Geoapify Places API."""

    BASE_URL = "https://api.geoapify.com/v2/places"

    def __init__(self):
        self.api_key = os.getenv("GEOAPIFY_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError(
                "GEOAPIFY_API_KEY is not set. "
                "Add it to your .env file (free tier: https://myprojects.geoapify.com)."
            )
        self.timeout = 30
        self.rate_limit_delay = 0.5  # seconds between paginated requests

    # ------------------------------------------------------------------
    # Public API – identical signature to old OSMCollector
    # ------------------------------------------------------------------

    def fetch_pois_for_location(
        self,
        location_name: str,
        lat: float,
        lon: float,
        radius_km: int = 10,
    ) -> List[Dict]:
        """
        Fetch tourist POIs from Geoapify around *lat/lon*.

        Returns a list of dicts with the same keys the pipeline expects:
        osm_id, osm_type, name, location_name, latitude, longitude,
        category, activities, osm_tags.
        """
        radius_m = radius_km * 1000

        params = {
            "categories": _GEO_CATEGORIES,
            "filter": f"circle:{lon},{lat},{radius_m}",
            "bias": f"proximity:{lon},{lat}",
            "limit": 100,
            "apiKey": self.api_key,
        }

        try:
            logger.info("Querying Geoapify for POIs near %s (r=%dkm)…", location_name, radius_km)

            resp = requests.get(self.BASE_URL, params=params, timeout=self.timeout)

            if resp.status_code == 401:
                logger.error("Geoapify 401 – invalid API key")
                return []
            if resp.status_code == 429:
                logger.warning("Geoapify 429 – rate-limited; backing off 5 s")
                time.sleep(5)
                resp = requests.get(self.BASE_URL, params=params, timeout=self.timeout)

            resp.raise_for_status()
            data = resp.json()

            raw_pois: List[Dict] = []
            for feature in data.get("features", []):
                poi = self._parse_feature(feature, location_name)
                if poi is not None:
                    raw_pois.append(poi)

            logger.info("Found %d raw POIs from Geoapify for %s", len(raw_pois), location_name)

            deduped = self._deduplicate_pois(raw_pois)

            time.sleep(self.rate_limit_delay)
            return deduped

        except requests.exceptions.Timeout:
            logger.error("Geoapify request timeout for %s", location_name)
            return []
        except requests.exceptions.RequestException as exc:
            logger.error("Geoapify request error for %s: %s", location_name, exc)
            return []
        except Exception as exc:
            logger.error("Unexpected error fetching from Geoapify: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_feature(self, feature: Dict, location_name: str) -> Dict | None:
        """Convert a single GeoJSON Feature into the pipeline dict shape."""
        props = feature.get("properties", {})

        # Prefer the English name; fall back to the default name
        name = props.get("name:en") or props.get("name") or ""
        if not name.strip():
            return None

        # Skip non-Latin names (Urdu, Arabic, Chinese, etc.)
        if not name.isascii():
            return None

        lat = props.get("lat")
        lon = props.get("lon")
        if lat is None or lon is None:
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [])
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
            else:
                return None

        geo_categories = props.get("categories", [])
        category = self._determine_category(geo_categories)
        activities = self._extract_activities(geo_categories, category)

        raw_place_id = props.get("place_id", "")
        # Geoapify place_ids are hex strings that can exceed 100+ chars.
        # Produce a short deterministic ID that fits VARCHAR(100).
        short_hash = hashlib.sha256(raw_place_id.encode()).hexdigest()[:24]
        osm_id = f"geo_{short_hash}"

        return {
            "osm_id": osm_id,
            "osm_type": "node",
            "name": name.strip(),
            "location_name": location_name,
            "latitude": float(lat),
            "longitude": float(lon),
            "category": category,
            "activities": activities,
            "osm_tags": props,
        }

    # ------------------------------------------------------------------
    # Category / activity mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _determine_category(geo_categories: List[str]) -> str:
        """Map Geoapify category strings to our app categories."""
        cats = " ".join(geo_categories).lower()

        if any(k in cats for k in ("mountain", "peak", "glacier", "waterfall",
                                    "hot_spring", "valley", "natural.water",
                                    "natural.forest")):
            return "nature"
        if any(k in cats for k in ("religion", "place_of_worship")):
            return "religious"
        if any(k in cats for k in ("heritage", "castle", "fort", "ruins",
                                    "memorial", "historic")):
            return "historical"
        if any(k in cats for k in ("museum", "gallery", "arts_centre")):
            return "cultural"
        if any(k in cats for k in ("sport", "climbing", "ski")):
            return "adventure"
        if "park" in cats:
            return "nature"
        if any(k in cats for k in ("tourism.attraction", "tourism.sights",
                                    "viewpoint")):
            return "nature"

        return "nature"

    @staticmethod
    def _extract_activities(geo_categories: List[str], category: str) -> List[str]:
        """Derive activity tags from Geoapify categories."""
        cats = " ".join(geo_categories).lower()
        acts: List[str] = []

        if any(k in cats for k in ("mountain", "peak")):
            acts.extend(["hiking", "photography", "trekking"])
        if "waterfall" in cats:
            acts.extend(["photography", "hiking", "sightseeing"])
        if "glacier" in cats:
            acts.extend(["photography", "trekking", "adventure"])
        if "hot_spring" in cats:
            acts.extend(["relaxation", "photography"])
        if "viewpoint" in cats:
            acts.extend(["photography", "sightseeing"])
        if any(k in cats for k in ("museum", "gallery")):
            acts.extend(["cultural", "sightseeing"])
        if "ski" in cats:
            acts.append("skiing")
        if "climbing" in cats:
            acts.extend(["rock_climbing", "adventure"])
        if "park" in cats:
            acts.extend(["picnic", "family", "relaxation"])
        if any(k in cats for k in ("religion", "place_of_worship")):
            acts.extend(["cultural", "religious", "sightseeing"])
        if any(k in cats for k in ("heritage", "castle", "fort", "ruins")):
            acts.extend(["cultural", "sightseeing", "photography"])

        if not acts:
            _defaults = {
                "nature":     ["sightseeing", "photography"],
                "cultural":   ["cultural", "sightseeing"],
                "adventure":  ["adventure", "hiking"],
                "religious":  ["religious", "cultural"],
                "historical": ["cultural", "sightseeing"],
            }
            acts = _defaults.get(category, ["sightseeing"])

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: List[str] = []
        for a in acts:
            if a not in seen:
                seen.add(a)
                unique.append(a)
        return unique

    # ------------------------------------------------------------------
    # Deduplication (unchanged logic from OSMCollector)
    # ------------------------------------------------------------------

    @staticmethod
    def _deduplicate_pois(
        raw_pois: List[Dict],
        distance_threshold_meters: int = 1500,
        fuzz_threshold: int = 80,
    ) -> List[Dict]:
        """
        Remove crowdsourced duplicates that are physically close AND
        have similar names (token_set_ratio handles word-order differences
        like "Rakaposhi View" vs "Viewpoint on Rakaposhi").
        """
        unique: List[Dict] = []

        for poi in raw_pois:
            is_dup = False
            for existing in unique:
                dist = distance_meters(
                    float(poi["latitude"]),
                    float(poi["longitude"]),
                    float(existing["latitude"]),
                    float(existing["longitude"]),
                )

                if dist < distance_threshold_meters:
                    sim = token_set_ratio(poi["name"], existing["name"])
                    if sim > fuzz_threshold:
                        is_dup = True
                        if len(poi.get("osm_tags", {})) > len(
                            existing.get("osm_tags", {})
                        ):
                            existing.update(poi)
                        break

            if not is_dup:
                unique.append(poi)

        removed = len(raw_pois) - len(unique)
        if removed > 0:
            logger.info("Deduplication removed %d redundant POIs.", removed)

        return unique


# -----------------------------------------------------------------------
# Quick smoke test
# -----------------------------------------------------------------------

def test_geoapify_collector():
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    collector = GeoapifyCollector()
    test = {"name": "Hunza", "lat": 36.2993187, "lon": 74.613428}

    print(f"\n{'='*60}")
    print(f"Testing GeoapifyCollector for {test['name']}")
    print(f"{'='*60}\n")

    pois = collector.fetch_pois_for_location(test["name"], test["lat"], test["lon"])
    if pois:
        print(f"\nFound {len(pois)} POIs:")
        for i, p in enumerate(pois[:8], 1):
            print(f"\n{i}. {p['name']}")
            print(f"   Category : {p['category']}")
            print(f"   Activities: {', '.join(p['activities'])}")
            print(f"   Coords   : ({p['latitude']:.4f}, {p['longitude']:.4f})")
            print(f"   osm_id   : {p['osm_id']}")
    else:
        print("No POIs found (check your GEOAPIFY_API_KEY)")


if __name__ == "__main__":
    test_geoapify_collector()
