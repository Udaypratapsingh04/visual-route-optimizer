"""Day 4 - BFS / DFS traversals and connected-component analysis.

All traversals are O(V + E). DFS is iterative (no recursion-limit problems).
By default road closures are ignored: we verify the *physical* network.
"""
from __future__ import annotations

from collections import deque
from typing import Dict, List, Set

from .graph import Graph


def _out(graph: Graph, u: int, respect_closures: bool):
    for e in graph.neighbors(u):
        if respect_closures and e.closed:
            continue
        yield e.target


def bfs(graph: Graph, start: int, respect_closures: bool = False) -> List[int]:
    """Nodes reachable from `start`, in BFS visit order."""
    seen = {start}
    order: List[int] = []
    q = deque([start])
    while q:
        u = q.popleft()
        order.append(u)
        for v in _out(graph, u, respect_closures):
            if v not in seen:
                seen.add(v)
                q.append(v)
    return order


def dfs(graph: Graph, start: int, respect_closures: bool = False) -> List[int]:
    """Nodes reachable from `start`, in DFS (pre-order) visit order."""
    seen: Set[int] = set()
    order: List[int] = []
    stack = [start]
    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u)
        order.append(u)
        for v in reversed(list(_out(graph, u, respect_closures))):
            if v not in seen:
                stack.append(v)
    return order


def weakly_connected_components(graph: Graph, respect_closures: bool = False) -> List[Set[int]]:
    """Components when edge direction is ignored (BFS on the undirected view)."""
    und: Dict[int, List[int]] = {n: [] for n in graph.node_ids()}
    for e in graph.edges():
        if respect_closures and e.closed:
            continue
        und[e.source].append(e.target)
        und[e.target].append(e.source)
    seen: Set[int] = set()
    comps: List[Set[int]] = []
    for s in graph.node_ids():
        if s in seen:
            continue
        comp = {s}
        seen.add(s)
        q = deque([s])
        while q:
            u = q.popleft()
            for v in und[u]:
                if v not in seen:
                    seen.add(v)
                    comp.add(v)
                    q.append(v)
        comps.append(comp)
    return sorted(comps, key=len, reverse=True)


def strongly_connected_components(graph: Graph, respect_closures: bool = False) -> List[Set[int]]:
    """Kosaraju's algorithm (two DFS passes). Strongly connected = every node
    can reach every other node while obeying one-way streets."""
    # pass 1: finishing order on the original graph
    visited: Set[int] = set()
    order: List[int] = []
    for s in graph.node_ids():
        if s in visited:
            continue
        visited.add(s)
        stack = [(s, iter(list(_out(graph, s, respect_closures))))]
        while stack:
            u, it = stack[-1]
            for v in it:
                if v not in visited:
                    visited.add(v)
                    stack.append((v, iter(list(_out(graph, v, respect_closures)))))
                    break
            else:
                order.append(u)
                stack.pop()

    # reverse graph
    rev: Dict[int, List[int]] = {n: [] for n in graph.node_ids()}
    for e in graph.edges():
        if respect_closures and e.closed:
            continue
        rev[e.target].append(e.source)

    # pass 2: DFS on reversed graph in decreasing finish time
    assigned: Set[int] = set()
    comps: List[Set[int]] = []
    for s in reversed(order):
        if s in assigned:
            continue
        comp = {s}
        assigned.add(s)
        stack2 = [s]
        while stack2:
            u = stack2.pop()
            for v in rev[u]:
                if v not in assigned:
                    assigned.add(v)
                    comp.add(v)
                    stack2.append(v)
        comps.append(comp)
    return sorted(comps, key=len, reverse=True)


def prune_to_largest_scc(graph: Graph) -> tuple[Graph, Set[int]]:
    """Return (pruned graph, removed node ids). The result is strongly connected."""
    comps = strongly_connected_components(graph)
    if not comps:
        return graph, set()
    keep = comps[0]
    removed = set(graph.node_ids()) - keep
    return graph.subgraph(keep), removed
