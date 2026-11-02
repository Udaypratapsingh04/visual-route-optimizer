"""Day 2 - validate network.json and optionally export GeoJSON for geojson.io.

Usage:
  python scripts/validate_network.py data/network.json
  python scripts/validate_network.py data/network.json --geojson data/network.geojson
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from routeopt import haversine_m, load_graph                         # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--geojson", help="write a GeoJSON FeatureCollection to this path")
    args = ap.parse_args()

    raw = json.loads(Path(args.path).read_text(encoding="utf-8"))
    g = load_graph(args.path)
    problems = list(g.warnings)

    bbox = raw.get("meta", {}).get("bbox")
    for n in g.nodes():
        if not (-90 <= n.lat <= 90 and -180 <= n.lon <= 180):
            problems.append(f"node {n.id}: coordinates out of range")
        if bbox and not (bbox[0] - 1e-6 <= n.lat <= bbox[2] + 1e-6 and
                         bbox[1] - 1e-6 <= n.lon <= bbox[3] + 1e-6):
            problems.append(f"node {n.id}: outside declared bbox")
    for e in g.edges():
        a, b = g.node(e.source), g.node(e.target)
        straight = haversine_m(a.lat, a.lon, b.lat, b.lon)
        if e.length_m + 1.0 < straight:   # road can never be shorter than the straight line
            problems.append(f"edge {e.source}->{e.target}: length {e.length_m:.1f} m < "
                            f"straight-line {straight:.1f} m (breaks A* admissibility!)")

    print(f"Nodes: {g.node_count}   Directed edges: {g.edge_count}")
    print(f"Target 80-120 nodes: {'OK' if 80 <= g.node_count <= 120 else 'OUT OF RANGE'}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems[:30]:
            print("  -", p)
    else:
        print("No problems found.")

    if args.geojson:
        feats = [{"type": "Feature",
                  "properties": {"id": n.id, "name": n.name},
                  "geometry": {"type": "Point", "coordinates": [n.lon, n.lat]}}
                 for n in g.nodes()]
        for e in g.edges():
            a, b = g.node(e.source), g.node(e.target)
            feats.append({"type": "Feature",
                          "properties": {"source": e.source, "target": e.target,
                                         "length_m": round(e.length_m, 1)},
                          "geometry": {"type": "LineString",
                                       "coordinates": [[a.lon, a.lat], [b.lon, b.lat]]}})
        Path(args.geojson).write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
        print(f"GeoJSON written to {args.geojson}  (drag it onto https://geojson.io to inspect)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
