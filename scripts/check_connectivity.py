"""Day 4 - connectivity verification. Exit code 0 only if there is exactly 1 component.

Usage:
  python scripts/check_connectivity.py data/network.json
  python scripts/check_connectivity.py data/network.json --prune --out data/network.json
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from routeopt import load_graph, save_graph                          # noqa: E402
from routeopt.connectivity import (bfs, dfs, prune_to_largest_scc,   # noqa: E402
                                   strongly_connected_components,
                                   weakly_connected_components)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--prune", action="store_true", help="drop nodes outside the largest SCC")
    ap.add_argument("--out", help="where to save the pruned network (use with --prune)")
    args = ap.parse_args()

    g = load_graph(args.path)
    start = next(iter(g.node_ids()))
    weak = weakly_connected_components(g)
    strong = strongly_connected_components(g)
    print(f"Graph: {g}")
    print(f"BFS reachable from node {start}: {len(bfs(g, start))}/{g.node_count}")
    print(f"DFS reachable from node {start}: {len(dfs(g, start))}/{g.node_count}")
    print(f"Weakly connected components:   {len(weak)}  sizes={[len(c) for c in weak][:8]}")
    print(f"Strongly connected components: {len(strong)}  sizes={[len(c) for c in strong][:8]}")

    if len(strong) != 1 and args.prune:
        g, removed = prune_to_largest_scc(g)
        print(f"Pruned {len(removed)} node(s) -> {g}")
        if args.out:
            save_graph(g, args.out, meta={"note": "pruned to largest SCC"})
            print(f"Saved {args.out}")
        strong = strongly_connected_components(g)
        print(f"Strongly connected components after prune: {len(strong)}")

    ok = len(strong) == 1
    print("RESULT:", "PASS (components == 1)" if ok else "FAIL (components != 1)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
