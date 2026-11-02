"""Day 7 + Day 8 - Dijkstra and A* on top of the indexed min-heap.

Both share one core loop; Dijkstra is simply A* with h(n) = 0.
Time: O((V + E) log V) with a binary heap (heap never holds more than V items
thanks to decrease_key).  Requires non-negative edge costs.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .costs import edge_cost_fn, heuristic_fn
from .graph import Graph
from .heap import IndexedMinHeap


@dataclass
class SearchResult:
    algorithm: str
    source: int
    target: int
    found: bool
    path: List[int] = field(default_factory=list)
    cost: float = math.inf                    # in the units of the chosen mode
    visited_order: List[int] = field(default_factory=list)   # nodes in the order they were popped
    heap_pushes: int = 0
    edges_relaxed: int = 0

    @property
    def nodes_explored(self) -> int:
        return len(self.visited_order)


def _search(graph: Graph, source: int, target: int, mode: str, use_heuristic: bool,
            name: str) -> SearchResult:
    if not graph.has_node(source) or not graph.has_node(target):
        raise KeyError(f"unknown node in query ({source} -> {target})")

    cost_of = edge_cost_fn(mode)
    h: Callable[[int], float] = heuristic_fn(graph, target, mode) if use_heuristic else (lambda _n: 0.0)

    res = SearchResult(name, source, target, found=False)
    g_score: Dict[int, float] = {source: 0.0}
    parent: Dict[int, Optional[int]] = {source: None}
    closed = set()

    heap = IndexedMinHeap()
    h0 = h(source)
    heap.push(source, (h0, h0))              # priority = (f, h): ties prefer nodes closer to goal
    res.heap_pushes = 1

    while heap:
        u, _ = heap.pop_min()
        closed.add(u)
        res.visited_order.append(u)
        if u == target:
            res.found = True
            res.cost = g_score[u]
            break
        gu = g_score[u]
        for e in graph.neighbors(u):
            v = e.target
            if v in closed:
                continue
            w = cost_of(e)
            if w == math.inf:               # closed road
                continue
            res.edges_relaxed += 1
            tentative = gu + w
            if tentative < g_score.get(v, math.inf):
                g_score[v] = tentative
                parent[v] = u
                hv = h(v)
                if heap.push_or_decrease(v, (tentative + hv, hv)):
                    res.heap_pushes += 1

    if res.found:
        node: Optional[int] = target
        while node is not None:
            res.path.append(node)
            node = parent[node]
        res.path.reverse()
    return res


def dijkstra(graph: Graph, source: int, target: int, mode: str = "distance") -> SearchResult:
    return _search(graph, source, target, mode, use_heuristic=False, name="dijkstra")


def astar(graph: Graph, source: int, target: int, mode: str = "distance") -> SearchResult:
    return _search(graph, source, target, mode, use_heuristic=True, name="astar")


ALGORITHMS = {"dijkstra": dijkstra, "astar": astar}
