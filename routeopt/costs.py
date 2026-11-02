"""Day 9 - multi-criteria objective functions and matching A* heuristics.

mode "distance": minimise meters. Congestion is ignored, closed roads are blocked.
mode "time"    : minimise seconds = length * congestion / free_flow_speed.

Heuristic = straight-line Haversine distance to the target (divided by the free-flow
speed in "time" mode). It is admissible and consistent as long as every congestion
multiplier is >= 1 (a road is never faster than free flow).
"""
from __future__ import annotations

import math
from typing import Callable

from .graph import Graph
from .haversine import haversine_m
from .models import Edge

FREE_FLOW_SPEED_MPS = 30 * 1000 / 3600   # 30 km/h campus/city speed
MODES = ("distance", "time")


def edge_cost_fn(mode: str) -> Callable[[Edge], float]:
    if mode == "distance":
        return lambda e: math.inf if e.closed else e.length_m
    if mode == "time":
        return lambda e: math.inf if e.closed else e.length_m * e.congestion / FREE_FLOW_SPEED_MPS
    raise ValueError(f"unknown mode {mode!r}; choose from {MODES}")


def heuristic_fn(graph: Graph, target: int, mode: str) -> Callable[[int], float]:
    t = graph.node(target)
    scale = 1.0 if mode == "distance" else 1.0 / FREE_FLOW_SPEED_MPS
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; choose from {MODES}")

    def h(node_id: int) -> float:
        n = graph.node(node_id)
        return haversine_m(n.lat, n.lon, t.lat, t.lon) * scale
    return h
