"""Day 10 - framework-independent service layer (the REST API is a thin wrapper
around these functions, which keeps them unit-testable without a web server)."""
from __future__ import annotations

from typing import Dict

from .algorithms import ALGORITHMS
from .costs import MODES
from .graph import Graph
from .metrics import run_with_metrics


def efficiency_rating(saved_pct: float) -> str:
    """Heuristic efficiency rating shown in the HUD (share of nodes A* avoided)."""
    if saved_pct >= 60:
        return "Excellent"
    if saved_pct >= 40:
        return "Good"
    if saved_pct >= 20:
        return "Fair"
    return "Low"


def list_nodes(graph: Graph):
    return [{"id": n.id, "name": n.name, "lat": n.lat, "lon": n.lon}
            for n in sorted(graph.nodes(), key=lambda n: n.id)]


def list_edges(graph: Graph):
    return [{"source": e.source, "target": e.target, "length_m": round(e.length_m, 2),
             "congestion": e.congestion, "closed": e.closed}
            for e in graph.edges()]


def compute_route(graph: Graph, source: int, target: int,
                  algorithm: str = "both", mode: str = "distance") -> Dict:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if algorithm not in (*ALGORITHMS, "both"):
        raise ValueError("algorithm must be 'dijkstra', 'astar' or 'both'")
    if not graph.has_node(source) or not graph.has_node(target):
        raise KeyError("unknown source or target node")

    names = list(ALGORITHMS) if algorithm == "both" else [algorithm]
    out: Dict = {"source": source, "target": target, "mode": mode, "results": {}}
    for name in names:
        res, metrics = run_with_metrics(graph, name, source, target, mode)
        out["results"][name] = {
            "found": res.found,
            "path": res.path,
            "visited_nodes": res.visited_order,     # drives the Week 3 animation
            "metrics": metrics,
        }
    if algorithm == "both":
        d = out["results"]["dijkstra"]["metrics"]["nodes_explored"]
        a = out["results"]["astar"]["metrics"]["nodes_explored"]
        out["nodes_saved_pct"] = round(100 * (d - a) / d, 1) if d else 0.0
        out["efficiency_rating"] = efficiency_rating(out["nodes_saved_pct"])
    return out


def set_congestion(graph: Graph, source: int, target: int, multiplier: float | None = None,
                   closed: bool | None = None, both_directions: bool = True) -> Dict:
    pairs = [(source, target)] + ([(target, source)] if both_directions else [])
    edges = [graph.get_edge(a, b) for a, b in pairs]
    edges = [e for e in edges if e is not None]
    if not edges:
        raise KeyError(f"no road between {source} and {target}")
    if multiplier is None and closed is None:
        raise ValueError("provide 'multiplier' and/or 'closed'")
    for e in edges:
        if multiplier is not None:
            graph.update_edge_weight(e.source, e.target, multiplier)
        if closed is not None:
            graph.toggle_road_closure(e.source, e.target, closed)
    return {"updated": [{"source": e.source, "target": e.target,
                         "congestion": e.congestion, "closed": e.closed} for e in edges]}
