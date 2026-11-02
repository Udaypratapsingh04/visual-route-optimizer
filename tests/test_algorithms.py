import math
import random
import pytest
from routeopt import Graph, Node, load_graph
from routeopt.algorithms import astar, dijkstra
from routeopt.service import compute_route, set_congestion


def diamond():
    """0 -> 1 -> 3 (short) and 0 -> 2 -> 3 (longer); nodes spaced along a line."""
    g = Graph()
    for i, (la, lo) in enumerate([(27.000, 77.000), (27.001, 77.001), (27.001, 76.999), (27.002, 77.000)]):
        g.add_node(Node(i, f"n{i}", la, lo))
    g.add_edge(0, 1, 200); g.add_edge(1, 3, 200)
    g.add_edge(0, 2, 300); g.add_edge(2, 3, 300)
    return g


def test_shortest_path_both():
    g = diamond()
    for algo in (dijkstra, astar):
        r = algo(g, 0, 3)
        assert r.found and r.path == [0, 1, 3] and r.cost == pytest.approx(400)
        assert r.visited_order[0] == 0 and r.visited_order[-1] == 3


def test_same_node():
    r = astar(diamond(), 2, 2)
    assert r.found and r.path == [2] and r.cost == 0 and r.nodes_explored == 1


def test_unreachable():
    g = diamond()
    assert dijkstra(g, 3, 0).found is False       # edges are one-way
    assert astar(g, 3, 0).path == []


def test_unknown_node():
    with pytest.raises(KeyError):
        dijkstra(diamond(), 0, 99)


def test_closure_forces_detour():
    g = diamond()
    g.toggle_road_closure(1, 3, True)
    r = astar(g, 0, 3)
    assert r.path == [0, 2, 3] and r.cost == pytest.approx(600)
    g.toggle_road_closure(2, 3, True)
    assert dijkstra(g, 0, 3).found is False


def test_congestion_changes_time_mode_but_not_distance_mode():
    g = diamond()
    g.update_edge_weight(0, 1, 10.0)               # heavy traffic on the short route
    assert dijkstra(g, 0, 3, "distance").path == [0, 1, 3]
    assert dijkstra(g, 0, 3, "time").path == [0, 2, 3]
    assert astar(g, 0, 3, "time").path == [0, 2, 3]


def _bellman_ford(g, s):
    dist = {n: math.inf for n in g.node_ids()}
    dist[s] = 0
    for _ in range(g.node_count):
        changed = False
        for e in g.edges():
            if dist[e.source] + e.length_m < dist[e.target]:
                dist[e.target] = dist[e.source] + e.length_m
                changed = True
        if not changed:
            break
    return dist


def test_optimal_against_bellman_ford_and_astar_agrees():
    g = load_graph("data/network.json")
    ids = sorted(g.node_ids())
    rnd = random.Random(3)
    for _ in range(40):
        s, t = rnd.sample(ids, 2)
        ref = _bellman_ford(g, s)[t]
        d, a = dijkstra(g, s, t), astar(g, s, t)
        assert d.cost == pytest.approx(ref, abs=1e-6)
        assert a.cost == pytest.approx(ref, abs=1e-6)


def test_astar_explores_fewer_nodes_on_average():
    g = load_graph("data/network.json")
    ids = sorted(g.node_ids())
    rnd = random.Random(5)
    d_tot = a_tot = 0
    for _ in range(60):
        s, t = rnd.sample(ids, 2)
        d_tot += dijkstra(g, s, t).nodes_explored
        a_tot += astar(g, s, t).nodes_explored
    assert a_tot < d_tot


def test_service_compute_route_and_congestion():
    g = load_graph("data/network.json")
    out = compute_route(g, 0, 99, "both", "distance")
    assert set(out["results"]) == {"dijkstra", "astar"}
    assert out["results"]["astar"]["metrics"]["nodes_explored"] <= out["results"]["dijkstra"]["metrics"]["nodes_explored"]
    assert "nodes_saved_pct" in out
    first = out["results"]["dijkstra"]["path"]
    u, v = first[0], first[1]
    set_congestion(g, u, v, closed=True)
    again = compute_route(g, 0, 99, "dijkstra")["results"]["dijkstra"]
    assert again["path"][:2] != [u, v]
    with pytest.raises(ValueError):
        compute_route(g, 0, 99, "bfs")
    with pytest.raises(KeyError):
        compute_route(g, 0, 12345)
