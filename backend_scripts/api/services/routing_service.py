"""
Routing Service – Geoapify Route Matrix integration.

Fetches an N×N driving-time / distance matrix for a set of POIs so the
itinerary LLM can schedule realistic travel between locations.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

repo_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
load_dotenv(dotenv_path=os.path.join(repo_root, ".env"))

logger = logging.getLogger(__name__)

_MATRIX_URL = "https://api.geoapify.com/v1/routematrix"
_REQUEST_TIMEOUT = 30  # seconds


class RoutingService:
    """Wraps the Geoapify Route Matrix API to produce a human-readable
    drive-time matrix that can be injected into an LLM prompt."""

    def __init__(self):
        self.api_key: str = os.getenv("GEOAPIFY_API_KEY", "")
        if not self.api_key:
            logger.warning("GEOAPIFY_API_KEY not set – routing matrix will be unavailable")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def get_poi_matrix(self, pois: List[Dict]) -> str:
        """Return a markdown-formatted drive-time matrix for *pois*.

        Each dict in *pois* must contain at least ``name``, ``latitude``,
        and ``longitude``.

        On any failure (missing key, API error, timeout) the method logs a
        warning and returns an empty string so the caller can fall back to
        pure LLM estimation.
        """
        if not self.api_key:
            logger.info("No Geoapify key – skipping route matrix")
            return ""

        coords = self._extract_coords(pois)
        if len(coords) < 2:
            logger.info("Fewer than 2 geo-located POIs – skipping matrix")
            return ""

        raw_matrix = self._call_matrix_api(coords)
        if raw_matrix is None:
            return ""

        return self._format_matrix(pois, coords, raw_matrix)

    def get_drive_leg_minutes_km(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> Optional[Tuple[int, float]]:
        """Driving time (minutes) and distance (km) between two WGS84 points.

        Uses a 2×2 Geoapify Route Matrix (source 0 → target 1).
        """
        if not self.api_key:
            return None

        coords = [
            {"idx": 0, "name": "a", "lon": float(lon1), "lat": float(lat1)},
            {"idx": 1, "name": "b", "lon": float(lon2), "lat": float(lat2)},
        ]
        raw_matrix = self._call_matrix_api(coords)
        if raw_matrix is None or len(raw_matrix) < 2:
            return None
        try:
            cell = raw_matrix[0][1]
            dist_m = cell.get("distance")
            time_s = cell.get("time")
        except (IndexError, TypeError, AttributeError):
            return None
        if dist_m is None or time_s is None:
            return None
        if dist_m == 0 and time_s == 0:
            return None

        dist_km = round(dist_m / 1000, 1)
        time_min = max(1, round(time_s / 60))
        return time_min, dist_km

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_coords(pois: List[Dict]) -> List[Dict]:
        """Pull (lon, lat, index, name) for every POI that has valid coords."""
        result: List[Dict] = []
        for idx, poi in enumerate(pois):
            try:
                lat = float(poi["latitude"])
                lon = float(poi["longitude"])
                result.append({
                    "idx": idx,
                    "name": poi.get("name", f"POI-{idx}"),
                    "lon": lon,
                    "lat": lat,
                })
            except (KeyError, TypeError, ValueError):
                logger.debug("POI %s missing valid coords – skipping", poi.get("name"))
        return result

    def _call_matrix_api(self, coords: List[Dict]) -> Optional[List[List[Dict]]]:
        """POST to Geoapify and return the raw ``sources_to_targets`` matrix."""
        locations = [{"location": [c["lon"], c["lat"]]} for c in coords]

        body = {
            "mode": "drive",
            "sources": locations,
            "targets": locations,
        }

        try:
            resp = requests.post(
                _MATRIX_URL,
                params={"apiKey": self.api_key},
                json=body,
                headers={"Content-Type": "application/json"},
                timeout=_REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            matrix = data.get("sources_to_targets")
            if not matrix:
                logger.warning("Geoapify response missing 'sources_to_targets'")
                return None
            return matrix
        except requests.exceptions.Timeout:
            logger.warning("Geoapify Route Matrix request timed out after %ss", _REQUEST_TIMEOUT)
            return None
        except requests.exceptions.HTTPError as exc:
            logger.warning("Geoapify Route Matrix HTTP error: %s", exc)
            return None
        except Exception as exc:
            logger.warning("Geoapify Route Matrix unexpected error: %s", exc)
            return None

    @staticmethod
    def _format_matrix(
        pois: List[Dict],
        coords: List[Dict],
        matrix: List[List[Dict]],
    ) -> str:
        """Convert the raw NxN matrix into a concise markdown table the LLM
        can reason over.

        Produces lines like:
            From Altit Fort → Attabad Lake: 45 min, 12.5 km
        Only unique (i→j where i<j) pairs are emitted to keep prompt size
        manageable.
        """
        lines: List[str] = []
        n = len(coords)

        for i in range(n):
            for j in range(i + 1, n):
                try:
                    cell = matrix[i][j]
                    dist_m = cell.get("distance")
                    time_s = cell.get("time")
                except (IndexError, TypeError, AttributeError):
                    continue

                if dist_m is None or time_s is None:
                    continue
                if dist_m == 0 and time_s == 0:
                    continue

                dist_km = round(dist_m / 1000, 1)
                time_min = max(1, round(time_s / 60))

                src = coords[i]["name"]
                dst = coords[j]["name"]
                lines.append(f"• {src} → {dst}: {time_min} min, {dist_km} km")

        if not lines:
            return ""

        header = (
            "## Drive-Time Matrix (all POI pairs)\n"
            "Distances and times are approximate driving estimates.\n\n"
        )
        return header + "\n".join(lines)
