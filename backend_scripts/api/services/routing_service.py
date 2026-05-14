"""
Routing Service – Geoapify Route Matrix integration.

This module:

1. Builds the pre-LLM N×N drive-time matrix and returns both the
   markdown string injected into the prompt AND a coordinate-keyed cache
   the agent can reuse after the LLM call (no second round-trip).
2. Exposes a batched, parallel-chunked ``get_legs(pairs)`` helper so the
   post-LLM transit recompute can fetch many legs in **one** request
   instead of one HTTP call per leg.
3. Keeps the legacy ``get_poi_matrix`` and ``get_drive_leg_minutes_km``
   entry points so existing callers keep working.
"""

import logging
import math
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# Geoapify route-matrix size cap per request.  Larger sets get chunked
# and dispatched in parallel.
_MAX_MATRIX_POINTS = 25
# Max simultaneous Geoapify requests when chunking.
_MAX_CONCURRENCY = 4

# Below this distance we skip the API entirely and use haversine +
# heuristic speed — far cheaper and indistinguishable for short legs.
SHORT_LEG_KM = 2.0
# Average drive speed (km/h) used to convert km → minutes when falling
# back to haversine.
HEURISTIC_KMH = 35.0

# (la1, lo1, la2, lo2) rounded keys -> (minutes, kilometres).
LegCache = Dict[Tuple[float, float, float, float], Tuple[int, float]]


def _coord_key(la1: float, lo1: float, la2: float, lo2: float) -> Tuple[float, float, float, float]:
    return (round(la1, 6), round(lo1, 6), round(la2, 6), round(lo2, 6))


class RoutingService:
    """Wraps the Geoapify Route Matrix API."""

    def __init__(self):
        self.api_key: str = os.getenv("GEOAPIFY_API_KEY", "")
        if not self.api_key:
            logger.warning("GEOAPIFY_API_KEY not set – routing matrix will be unavailable")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def get_poi_matrix(self, pois: List[Dict]) -> str:
        """Backward-compatible wrapper that only returns the markdown matrix."""
        matrix_str, _ = self.get_poi_matrix_with_cache(pois)
        return matrix_str

    def get_poi_matrix_with_cache(self, pois: List[Dict]) -> Tuple[str, LegCache]:
        """Compute the POI drive matrix once and return both the prompt
        string and a coordinate-keyed leg cache for the post-LLM
        recompute step.
        """
        if not self.api_key:
            logger.info("No Geoapify key – skipping route matrix")
            return "", {}

        coords = self._extract_coords(pois)
        if len(coords) < 2:
            logger.info("Fewer than 2 geo-located POIs – skipping matrix")
            return "", {}

        raw_matrix = self._call_matrix_api(coords)
        if raw_matrix is None:
            return "", {}

        matrix_str = self._format_matrix(pois, coords, raw_matrix)
        cache = self._build_cache_from_matrix(coords, raw_matrix)
        return matrix_str, cache

    def get_legs(
        self, pairs: List[Tuple[float, float, float, float]]
    ) -> List[Optional[Tuple[int, float]]]:
        """Batched + parallel leg lookup.

        For each ``(la1, lo1, la2, lo2)`` in *pairs* returns ``(mins, km)``
        or ``None``.  Duplicates points across pairs are deduplicated so
        many legs typically resolve to one (or a few chunked + parallel)
        Geoapify matrix calls.  Falls back to haversine when the API is
        unavailable.
        """
        results: List[Optional[Tuple[int, float]]] = [None] * len(pairs)
        if not pairs:
            return results

        if not self.api_key:
            return [self._haversine_leg(*p) for p in pairs]

        # Dedupe unique points across all pairs and assign each a matrix
        # index we can later look up.
        point_to_idx: Dict[Tuple[float, float], int] = {}
        for la1, lo1, la2, lo2 in pairs:
            for la, lo in ((la1, lo1), (la2, lo2)):
                key = (round(la, 6), round(lo, 6))
                if key not in point_to_idx:
                    point_to_idx[key] = len(point_to_idx)

        ordered_points = sorted(point_to_idx.items(), key=lambda kv: kv[1])
        coords = [
            {"idx": i, "name": f"P{i}", "lon": lo, "lat": la}
            for (la, lo), i in ordered_points
        ]

        if len(coords) <= _MAX_MATRIX_POINTS:
            raw_matrix = self._call_matrix_api(coords)
            cache: LegCache = (
                self._build_cache_from_matrix(coords, raw_matrix)
                if raw_matrix
                else {}
            )
        else:
            cache = self._call_matrix_in_chunks(coords)

        for i, (la1, lo1, la2, lo2) in enumerate(pairs):
            cached = cache.get(_coord_key(la1, lo1, la2, lo2))
            if cached is not None:
                results[i] = cached
            else:
                # API gave us nothing for this pair (chunk boundary, dead
                # cell, etc) – haversine fallback so the leg still has
                # realistic numbers.
                results[i] = self._haversine_leg(la1, lo1, la2, lo2)
        return results

    def get_drive_leg_minutes_km(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> Optional[Tuple[int, float]]:
        """Single-leg lookup kept for backward compatibility."""
        legs = self.get_legs([(float(lat1), float(lon1), float(lat2), float(lon2))])
        return legs[0] if legs else None

    @staticmethod
    def haversine_km(la1: float, lo1: float, la2: float, lo2: float) -> float:
        """Great-circle distance in kilometres."""
        r = 6371.0
        dlat = math.radians(la2 - la1)
        dlon = math.radians(lo2 - lo1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(la1))
            * math.cos(math.radians(la2))
            * math.sin(dlon / 2) ** 2
        )
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @classmethod
    def haversine_leg(cls, la1: float, lo1: float, la2: float, lo2: float) -> Tuple[int, float]:
        """Haversine distance + heuristic-speed minutes."""
        km = cls.haversine_km(la1, lo1, la2, lo2)
        mins = max(5, int(round(km / HEURISTIC_KMH * 60)))
        return mins, round(km, 1)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _haversine_leg(self, la1: float, lo1: float, la2: float, lo2: float) -> Tuple[int, float]:
        return self.haversine_leg(la1, lo1, la2, lo2)

    def _call_matrix_in_chunks(self, coords: List[Dict]) -> LegCache:
        """Split a large coord set into chunks and call Geoapify in parallel."""
        chunks: List[List[Dict]] = []
        step = _MAX_MATRIX_POINTS
        for i in range(0, len(coords), step):
            chunks.append(coords[i:i + step])

        merged: LegCache = {}
        with ThreadPoolExecutor(max_workers=_MAX_CONCURRENCY) as pool:
            futures = {pool.submit(self._call_matrix_api, c): c for c in chunks}
            for fut in as_completed(futures):
                chunk_coords = futures[fut]
                try:
                    raw = fut.result()
                except Exception as exc:
                    logger.warning("Geoapify matrix chunk failed: %s", exc)
                    raw = None
                if not raw:
                    continue
                merged.update(self._build_cache_from_matrix(chunk_coords, raw))
        return merged

    @staticmethod
    def _build_cache_from_matrix(
        coords: List[Dict],
        matrix: List[List[Dict]],
    ) -> LegCache:
        """Convert the raw Geoapify matrix into a coord-keyed cache."""
        cache: LegCache = {}
        n = len(coords)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
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
                la1 = float(coords[i]["lat"])
                lo1 = float(coords[i]["lon"])
                la2 = float(coords[j]["lat"])
                lo2 = float(coords[j]["lon"])
                mins = max(1, int(round(time_s / 60)))
                km = round(dist_m / 1000, 1)
                cache[_coord_key(la1, lo1, la2, lo2)] = (mins, float(km))
        return cache

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
        """Emit only the consecutive legs along the visit-order chain.

        ``coords`` preserves the order of geo-located POIs in ``pois``,
        which – after :py:meth:`ItineraryAgent._assign_visit_order` – is
        the planned visit sequence.  Emitting only neighbour pairs
        (``i → i+1``) keeps the routing guidance the LLM actually uses
        when scheduling sequentially while drastically shrinking prompt
        tokens versus the previous all-pairs output.

        The full matrix is still kept by the caller as a leg cache for
        post-LLM transit recomputation, so route accuracy is unaffected.
        """
        lines: List[str] = []
        n = len(coords)

        for i in range(n - 1):
            try:
                cell = matrix[i][i + 1]
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
            dst = coords[i + 1]["name"]
            lines.append(f"• {src} → {dst}: {time_min} min, {dist_km} km")

        if not lines:
            return ""

        header = (
            "## Drive-Time Chain (consecutive visit-order legs)\n"
            "Approximate driving estimates between each POI and the next.\n\n"
        )
        return header + "\n".join(lines)
