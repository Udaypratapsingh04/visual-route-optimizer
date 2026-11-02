"""Day 9 - instrumentation wrapper producing clean JSON metrics."""
from __future__ import annotations

import time
import tracemalloc
from typing import Dict

from .algorithms import ALGORITHMS, SearchResult
from .graph import Graph


def path_length_m(graph: Graph, path) -> float:
    return sum(graph.get_edge(a, b).length_m for a, b in zip(path, path[1:]))


def run_with_metrics(graph: Graph, algorithm: str, source: int, target: int,
                     mode: str = "distance", repeats: int = 3):
    """Returns (SearchResult, metrics dict).

    Time is the best of `repeats` runs (less noise); peak memory comes from a separate
    tracemalloc run because tracing slows the code down.
    """
    fn = ALGORITHMS[algorithm]
    best_ns = None
    result: SearchResult = None
    for _ in range(max(1, repeats)):
        t0 = time.perf_counter_ns()
        result = fn(graph, source, target, mode)
        dt = time.perf_counter_ns() - t0
        best_ns = dt if best_ns is None else min(best_ns, dt)

    tracemalloc.start()
    fn(graph, source, target, mode)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metrics: Dict = {
        "algorithm": algorithm,
        "mode": mode,
        "found": result.found,
        "execution_time_us": round(best_ns / 1000, 1),
        "nodes_explored": result.nodes_explored,
        "heap_pushes": result.heap_pushes,
        "edges_relaxed": result.edges_relaxed,
        "peak_memory_kb": round(peak / 1024, 1),
        "path_nodes": len(result.path),
        "path_length_m": round(path_length_m(graph, result.path), 2) if result.found else None,
        "path_cost": round(result.cost, 4) if result.found else None,
    }
    return result, metrics
