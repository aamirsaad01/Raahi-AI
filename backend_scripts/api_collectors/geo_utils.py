"""Great-circle distance helpers (stdlib only).

Used for POI deduplication thresholds. Matches geodesic behaviour closely
enough for metre-level comparisons without requiring geopy at import time.
"""

from __future__ import annotations

import math

# Mean Earth radius (metres); close to WGS84 for Pakistan-scale distances.
_EARTH_RADIUS_M = 6_371_008.8


def distance_meters(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Haversine great-circle distance between two WGS84 points, in metres."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    )
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return _EARTH_RADIUS_M * c
