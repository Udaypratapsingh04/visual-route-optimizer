import json
from routeopt import load_graph
from routeopt.benchmark import run_batch
from routeopt.metrics import run_with_metrics


def test_metrics_are_json_serialisable_and_complete():
    g = load_graph("data/network.json")
    res, m = run_with_metrics(g, "astar", 0, 99, "distance")
    json.dumps(m)
    for key in ("execution_time_us", "nodes_explored", "peak_memory_kb", "path_length_m"):
        assert key in m
    assert m["nodes_explored"] == res.nodes_explored and m["peak_memory_kb"] > 0


def test_batch_has_no_optimality_mismatch():
    g = load_graph("data/network.json")
    rep = run_batch(g, pairs=30, with_timing=False)
    assert rep["summary"]["optimality_mismatches"] == 0
    assert rep["summary"]["mean_nodes_astar"] <= rep["summary"]["mean_nodes_dijkstra"]
