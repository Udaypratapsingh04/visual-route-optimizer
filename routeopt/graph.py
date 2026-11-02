"""Day 1 + Day 5 - adjacency-list graph with dynamic edge weights.

Space: O(V + E)   (an adjacency matrix would be O(V^2))
Edge lookup (u, v): O(1) through the _edges index dict.
Neighbour iteration: O(deg(u)).
"""
from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Tuple

from .models import Edge, Node


class Graph:
    def __init__(self) -> None:
        self._nodes: Dict[int, Node] = {}
        self._adj: Dict[int, List[Edge]] = {}          # Map<NodeId, List<Edge>>
        self._edges: Dict[Tuple[int, int], Edge] = {}  # O(1) lookup index
        self.warnings: List[str] = []                  # filled by the loader

    # ---------- construction ----------
    def add_node(self, node: Node) -> None:
        if node.id in self._nodes:
            raise ValueError(f"duplicate node id {node.id}")
        self._nodes[node.id] = node
        self._adj[node.id] = []

    def add_edge(self, source: int, target: int, length_m: float,
                 congestion: float = 1.0, closed: bool = False) -> Edge:
        if source not in self._nodes or target not in self._nodes:
            raise KeyError(f"edge {source}->{target} references an unknown node")
        if source == target:
            raise ValueError(f"self-loop at node {source}")
        if length_m <= 0:
            raise ValueError(f"zero/negative length on edge {source}->{target}")
        if congestion <= 0:
            raise ValueError("congestion multiplier must be > 0")
        if (source, target) in self._edges:
            raise ValueError(f"duplicate edge {source}->{target}")
        edge = Edge(source, target, float(length_m), float(congestion), closed)
        self._adj[source].append(edge)
        self._edges[(source, target)] = edge
        return edge

    # ---------- queries ----------
    def node(self, node_id: int) -> Node:
        return self._nodes[node_id]

    def has_node(self, node_id: int) -> bool:
        return node_id in self._nodes

    def node_ids(self) -> Iterable[int]:
        return self._nodes.keys()

    def nodes(self) -> Iterator[Node]:
        return iter(self._nodes.values())

    def neighbors(self, node_id: int) -> List[Edge]:
        """Outgoing edges of node_id."""
        return self._adj[node_id]

    def edges(self) -> Iterator[Edge]:
        return iter(self._edges.values())

    def get_edge(self, source: int, target: int) -> Edge | None:
        return self._edges.get((source, target))

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    # ---------- Day 5: dynamic edge weights ----------
    def update_edge_weight(self, u: int, v: int, multiplier: float,
                           both_directions: bool = False) -> None:
        """Set the congestion multiplier of u->v (absolute value, not cumulative)."""
        if multiplier <= 0:
            raise ValueError("multiplier must be > 0 (use toggle_road_closure to block a road)")
        for a, b in self._pairs(u, v, both_directions):
            self._require_edge(a, b).congestion = float(multiplier)

    def toggle_road_closure(self, u: int, v: int, is_closed: bool,
                            both_directions: bool = False) -> None:
        """Close/open u->v. A closed edge has cost == math.inf."""
        for a, b in self._pairs(u, v, both_directions):
            self._require_edge(a, b).closed = bool(is_closed)

    def reset_dynamic_state(self) -> None:
        for e in self._edges.values():
            e.congestion = 1.0
            e.closed = False

    def _require_edge(self, u: int, v: int) -> Edge:
        e = self._edges.get((u, v))
        if e is None:
            raise KeyError(f"no edge {u}->{v}")
        return e

    @staticmethod
    def _pairs(u: int, v: int, both: bool):
        yield (u, v)
        if both:
            yield (v, u)

    # ---------- utilities ----------
    def subgraph(self, keep: Iterable[int]) -> "Graph":
        """Induced subgraph on `keep` (keeps congestion/closed state of edges)."""
        keep = set(keep)
        g = Graph()
        for nid in keep:
            g.add_node(self._nodes[nid])
        for e in self._edges.values():
            if e.source in keep and e.target in keep:
                g.add_edge(e.source, e.target, e.length_m, e.congestion, e.closed)
        return g

    def __repr__(self) -> str:
        return f"Graph(V={self.node_count}, E={self.edge_count})"
