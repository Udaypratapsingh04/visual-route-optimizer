"""Day 1 - entity definitions."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Node:
    """A road intersection / junction. Immutable, so it is safe as a shared reference."""
    id: int
    name: str
    lat: float
    lon: float


@dataclass(slots=True)
class Edge:
    """A directed road segment source -> target.

    length_m   : real-world length in meters (static, from Haversine / OSM geometry)
    congestion : multiplier > 0 applied to length (1.0 = free flow, 2.0 = twice as costly)
    closed     : True means the road is blocked and the cost becomes infinity
    """
    source: int
    target: int
    length_m: float
    congestion: float = 1.0
    closed: bool = False

    @property
    def cost(self) -> float:
        """Current traversal cost used by the algorithms (Week 2)."""
        return math.inf if self.closed else self.length_m * self.congestion
