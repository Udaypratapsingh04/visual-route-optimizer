"""Day 2 (offline fallback) - synthetic ~100-node road network so you can start coding
immediately. It is a PLACEHOLDER grid, not real roads: replace it with the output of
fetch_overpass.py for your actual campus/city before the final demo.

Usage: python scripts/generate_sample_network.py --out data/network.json
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from routeopt import Graph, Node, haversine_m, save_graph           # noqa: E402
from routeopt.connectivity import prune_to_largest_scc              # noqa: E402

CENTER = (27.4924, 77.6737)   # near Mathura; change if you like
ROWS, COLS = 10, 10
D_LAT, D_LON = 0.0011, 0.0012  # ~120 m spacing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/network.json")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rnd = random.Random(args.seed)

    g = Graph()
    nid = {}
    for r in range(ROWS):
        for c in range(COLS):
            i = r * COLS + c
            nid[(r, c)] = i
            lat = CENTER[0] + (r - ROWS / 2) * D_LAT + rnd.uniform(-0.0002, 0.0002)
            lon = CENTER[1] + (c - COLS / 2) * D_LON + rnd.uniform(-0.0002, 0.0002)
            g.add_node(Node(i, f"Sample R{r}C{c}", lat, lon))

    def link(a, b):
        if rnd.random() < 0.10:                       # drop some roads
            return
        na, nb = g.node(a), g.node(b)
        d = haversine_m(na.lat, na.lon, nb.lat, nb.lon)
        if rnd.random() < 0.12:                       # one-way street
            u, v = (a, b) if rnd.random() < 0.5 else (b, a)
            g.add_edge(u, v, d)
        else:
            g.add_edge(a, b, d)
            g.add_edge(b, a, d)

    for r in range(ROWS):
        for c in range(COLS):
            if c + 1 < COLS:
                link(nid[(r, c)], nid[(r, c + 1)])
            if r + 1 < ROWS:
                link(nid[(r, c)], nid[(r + 1, c)])
    for _ in range(6):                                # a few diagonal shortcuts
        r, c = rnd.randrange(ROWS - 1), rnd.randrange(COLS - 1)
        a, b = nid[(r, c)], nid[(r + 1, c + 1)]
        if g.get_edge(a, b) is None and g.get_edge(b, a) is None:
            d = haversine_m(g.node(a).lat, g.node(a).lon, g.node(b).lat, g.node(b).lon)
            g.add_edge(a, b, d)
            g.add_edge(b, a, d)

    g, removed = prune_to_largest_scc(g)
    lats = [n.lat for n in g.nodes()]
    lons = [n.lon for n in g.nodes()]
    bbox = [min(lats), min(lons), max(lats), max(lons)]
    save_graph(g, args.out, meta={"bbox": bbox, "source": "synthetic sample grid"})
    print(f"Saved {args.out}: {g.node_count} nodes, {g.edge_count} directed edges "
          f"({len(removed)} pruned)")


if __name__ == "__main__":
    main()
