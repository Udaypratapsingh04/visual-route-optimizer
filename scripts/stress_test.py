"""Day 17 - zero-crash verification.

Fires thousands of random and adversarial queries (random road closures, traffic,
same-node queries, isolated destinations, bad input) through the service layer and checks:
  * nothing crashes with an unexpected exception
  * invalid input raises the documented error (KeyError / ValueError)
  * Dijkstra and A* always agree on reachability and cost

Usage: python scripts/stress_test.py --trials 2000
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from routeopt import load_graph                                      # noqa: E402
from routeopt.service import compute_route, set_congestion           # noqa: E402


def expect_error(exc_type, fn, label, failures):
    try:
        fn()
    except exc_type:
        return
    except Exception as e:                                           # wrong exception type
        failures.append(f"{label}: raised {type(e).__name__} instead of {exc_type.__name__}")
        return
    failures.append(f"{label}: expected {exc_type.__name__}, nothing raised")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", default="data/network.json")
    ap.add_argument("--trials", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()

    rnd = random.Random(a.seed)
    g = load_graph(a.network)
    ids = sorted(g.node_ids())
    roads = sorted({(min(e.source, e.target), max(e.source, e.target)) for e in g.edges()})
    failures, stats = [], {"found": 0, "no_route": 0, "same_node": 0, "isolated": 0}

    for trial in range(a.trials):
        g.reset_dynamic_state()
        # random closures / traffic
        for (u, v) in rnd.sample(roads, rnd.randint(0, len(roads) // 3)):
            if rnd.random() < 0.6:
                set_congestion(g, u, v, closed=True)
            else:
                set_congestion(g, u, v, multiplier=rnd.choice([1.5, 2, 3, 5]))
        kind = rnd.random()
        s, t = rnd.sample(ids, 2)
        if kind < 0.08:
            t = s; stats["same_node"] += 1                           # single-node query
        elif kind < 0.2:                                             # isolate the destination
            for e in list(g.edges()):
                if e.target == t or e.source == t:
                    g.toggle_road_closure(e.source, e.target, True)
            stats["isolated"] += 1
        mode = rnd.choice(["distance", "time"])
        try:
            out = compute_route(g, s, t, "both", mode)
        except Exception as e:
            failures.append(f"trial {trial}: {type(e).__name__}: {e} ({s}->{t}, {mode})")
            continue
        d, st = out["results"]["dijkstra"], out["results"]["astar"]
        if d["found"] != st["found"]:
            failures.append(f"trial {trial}: reachability mismatch {s}->{t}")
        elif d["found"]:
            stats["found"] += 1
            if abs(d["metrics"]["path_cost"] - st["metrics"]["path_cost"]) > 1e-3:
                failures.append(f"trial {trial}: cost mismatch {s}->{t} ({mode})")
            if d["path"][0] != s or d["path"][-1] != t:
                failures.append(f"trial {trial}: bad path endpoints")
        else:
            stats["no_route"] += 1
            if d["path"] or st["path"]:
                failures.append(f"trial {trial}: path returned for unreachable pair")

    g.reset_dynamic_state()
    expect_error(KeyError, lambda: compute_route(g, ids[0], 10**9), "unknown target", failures)
    expect_error(KeyError, lambda: compute_route(g, -5, ids[0]), "unknown source", failures)
    expect_error(ValueError, lambda: compute_route(g, ids[0], ids[1], "both", "teleport"), "bad mode", failures)
    expect_error(ValueError, lambda: compute_route(g, ids[0], ids[1], "bfs"), "bad algorithm", failures)
    expect_error(ValueError, lambda: set_congestion(g, roads[0][0], roads[0][1]), "empty update", failures)
    expect_error(ValueError, lambda: set_congestion(g, roads[0][0], roads[0][1], multiplier=-1), "negative multiplier", failures)
    expect_error(KeyError, lambda: set_congestion(g, ids[0], 10**9, closed=True), "no such road", failures)

    print(f"trials={a.trials}  {stats}")
    if failures:
        print(f"FAILED: {len(failures)} problem(s)")
        for f in failures[:20]:
            print("  -", f)
        sys.exit(1)
    print("PASS: zero crashes, A* and Dijkstra always agree.")


if __name__ == "__main__":
    main()
