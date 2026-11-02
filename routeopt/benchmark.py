"""Day 10 - batch comparison of Dijkstra vs A* over random node pairs."""
from __future__ import annotations

import random
import statistics
from typing import Dict

from .algorithms import astar, dijkstra
from .graph import Graph
from .metrics import run_with_metrics


def run_batch(graph: Graph, pairs: int = 200, mode: str = "distance", seed: int = 7,
              with_timing: bool = True) -> Dict:
    rnd = random.Random(seed)
    ids = sorted(graph.node_ids())
    rows, mismatches = [], 0
    for _ in range(pairs):
        s, t = rnd.sample(ids, 2)
        d = dijkstra(graph, s, t, mode)
        a = astar(graph, s, t, mode)
        if d.found != a.found or (d.found and abs(d.cost - a.cost) > 1e-6):
            mismatches += 1
        if not d.found:
            continue
        saved = 100 * (d.nodes_explored - a.nodes_explored) / d.nodes_explored
        row = {"source": s, "target": t,
               "dijkstra_nodes": d.nodes_explored, "astar_nodes": a.nodes_explored,
               "nodes_saved_pct": round(saved, 1)}
        if with_timing:
            row["dijkstra_us"] = run_with_metrics(graph, "dijkstra", s, t, mode, 1)[1]["execution_time_us"]
            row["astar_us"] = run_with_metrics(graph, "astar", s, t, mode, 1)[1]["execution_time_us"]
        rows.append(row)

    saved = [r["nodes_saved_pct"] for r in rows]
    summary = {
        "mode": mode, "pairs_tested": len(rows), "optimality_mismatches": mismatches,
        "mean_nodes_dijkstra": round(statistics.mean(r["dijkstra_nodes"] for r in rows), 1),
        "mean_nodes_astar": round(statistics.mean(r["astar_nodes"] for r in rows), 1),
        "mean_nodes_saved_pct": round(statistics.mean(saved), 1),
        "median_nodes_saved_pct": round(statistics.median(saved), 1),
        "pairs_in_40_70_band_pct": round(100 * sum(40 <= x <= 70 for x in saved) / len(saved), 1),
    }
    return {"summary": summary, "pairs": rows}
