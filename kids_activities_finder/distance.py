"""Great-circle distance between two coordinates.

A 10-mile search radius doesn't need anything fancier than the haversine formula,
which is plenty accurate at city scale and has no dependencies.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_MILES = 3958.7613


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in miles between two (lat, lon) points on Earth."""
    rlat1, rlon1, rlat2, rlon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * asin(sqrt(a))
