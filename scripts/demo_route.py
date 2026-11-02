"""Quick CLI check: python scripts/demo_route.py 0 99 --mode distance"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from routeopt import load_graph                                      # noqa: E402
from routeopt.service import compute_route                           # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("source", type=int)
ap.add_argument("target", type=int)
ap.add_argument("--mode", choices=["distance", "time"], default="distance")
ap.add_argument("--network", default="data/network.json")
a = ap.parse_args()
out = compute_route(load_graph(a.network), a.source, a.target, "both", a.mode)
for name, r in out["results"].items():
    print(name, json.dumps(r["metrics"]))
print("nodes_saved_pct:", out["nodes_saved_pct"])
