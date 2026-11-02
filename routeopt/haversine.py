"""Day 3 - geodesic distance engine."""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_M = 6_371_008.8  # IUGG mean Earth radius


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters between two (lat, lon) points in degrees.

    a = sin^2(dphi/2) + cos(phi1) * cos(phi2) * sin^2(dlambda/2)
    d = 2 * R * asin(sqrt(a))
    """
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = phi2 - phi1
    dlmb = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(min(1.0, sqrt(a)))
