"""Day 3 - JSON parser: network.json <-> Graph.

File format (directed edges; set "bidirectional": true to auto-add the reverse):
{
  "meta":  {"bbox": [south, west, north, east], "source": "..."},
  "nodes": [{"id": 0, "name": "Main Gate", "lat": 27.49, "lon": 77.67}],
  "edges": [{"source": 0, "target": 1, "length_m": 120.5, "bidirectional": false}]
}
If "length_m" is missing it is computed with the Haversine formula.
"""
from __future__ import annotations

import json
from pathlib import Path

from .graph import Graph
from .haversine import haversine_m
from .models import Node


def load_graph(path: str | Path) -> Graph:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    g = Graph()
    for n in data["nodes"]:
        g.add_node(Node(int(n["id"]), str(n.get("name", f"Node {n['id']}")),
                        float(n["lat"]), float(n["lon"])))

    for e in data["edges"]:
        u, v = int(e["source"]), int(e["target"])
        pairs = [(u, v)] + ([(v, u)] if e.get("bidirectional") else [])
        for a, b in pairs:
            try:
                length = e.get("length_m")
                if length is None:
                    na, nb = g.node(a), g.node(b)
                    length = haversine_m(na.lat, na.lon, nb.lat, nb.lon)
                g.add_edge(a, b, float(length), float(e.get("congestion", 1.0)))
            except (ValueError, KeyError) as exc:   # zero-length, self-loop, duplicate...
                g.warnings.append(f"skipped edge {a}->{b}: {exc}")
    return g


def save_graph(graph: Graph, path: str | Path, meta: dict | None = None) -> None:
    out = {
        "meta": meta or {},
        "nodes": [{"id": n.id, "name": n.name, "lat": round(n.lat, 7), "lon": round(n.lon, 7)}
                  for n in sorted(graph.nodes(), key=lambda n: n.id)],
        "edges": [{"source": e.source, "target": e.target, "length_m": round(e.length_m, 2)}
                  for e in graph.edges()],
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(out, indent=1), encoding="utf-8")
