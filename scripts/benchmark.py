"""Day 10 - batch benchmark: Dijkstra vs A* over random node pairs -> JSON.

Usage: python scripts/benchmark.py --pairs 200 --mode distance --out data/benchmark.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from routeopt import load_graph                                      # noqa: E402
from routeopt.benchmark import run_batch                             # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", default="data/network.json")
    ap.add_argument("--pairs", type=int, default=200)
    ap.add_argument("--mode", choices=["distance", "time"], default="distance")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="data/benchmark.json")
    args = ap.parse_args()

    g = load_graph(args.network)
    report = run_batch(g, args.pairs, args.mode, args.seed)
    Path(args.out).write_text(json.dumps(report, indent=1))
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved {args.out}")
    if report["summary"]["optimality_mismatches"]:
        print("WARNING: A* and Dijkstra disagreed - check heuristic admissibility!")
        sys.exit(1)


if __name__ == "__main__":
    main()
