import pytest
from routeopt import Graph, Node
from routeopt.service import compute_route, efficiency_rating


def tiny():
    g = Graph()
    for i in range(4):
        g.add_node(Node(i, f"n{i}", 27 + i * 0.001, 77))
    g.add_edge(0, 1, 100); g.add_edge(1, 0, 100)
    g.add_edge(1, 2, 100); g.add_edge(2, 1, 100)
    return g                                          # node 3 is isolated


def test_isolated_destination():
    out = compute_route(tiny(), 0, 3)
    for r in out["results"].values():
        assert r["found"] is False and r["path"] == []
        assert r["metrics"]["path_length_m"] is None


def test_single_node_query():
    out = compute_route(tiny(), 1, 1)
    for r in out["results"].values():
        assert r["found"] and r["path"] == [1]
        assert r["metrics"]["path_length_m"] == 0


def test_no_path_after_closure():
    g = tiny()
    g.toggle_road_closure(1, 2, True, both_directions=True)
    assert compute_route(g, 0, 2, "astar")["results"]["astar"]["found"] is False


def test_efficiency_rating_bands():
    assert [efficiency_rating(x) for x in (75, 50, 25, 5)] == ["Excellent", "Good", "Fair", "Low"]


def test_both_includes_rating():
    out = compute_route(tiny(), 0, 2)
    assert out["efficiency_rating"] in {"Excellent", "Good", "Fair", "Low"}
