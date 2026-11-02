import math
import pytest
from routeopt import Graph, Node


@pytest.fixture
def g():
    g = Graph()
    for i in range(3):
        g.add_node(Node(i, f"n{i}", 27.0 + i * 0.001, 77.0))
    g.add_edge(0, 1, 100.0)
    g.add_edge(1, 2, 50.0)
    return g


def test_counts_and_neighbors(g):
    assert (g.node_count, g.edge_count) == (3, 2)
    assert [e.target for e in g.neighbors(0)] == [1]
    assert g.neighbors(2) == []


def test_edge_lookup_is_directed(g):
    assert g.get_edge(0, 1).length_m == 100.0
    assert g.get_edge(1, 0) is None


def test_rejects_bad_edges(g):
    with pytest.raises(ValueError):
        g.add_edge(0, 0, 10)          # self loop
    with pytest.raises(ValueError):
        g.add_edge(0, 2, 0)           # zero length
    with pytest.raises(ValueError):
        g.add_edge(0, 1, 5)           # duplicate
    with pytest.raises(KeyError):
        g.add_edge(0, 99, 5)          # unknown node


def test_duplicate_node(g):
    with pytest.raises(ValueError):
        g.add_node(Node(0, "dup", 0, 0))


def test_update_edge_weight(g):
    g.update_edge_weight(0, 1, 2.5)
    assert g.get_edge(0, 1).cost == pytest.approx(250.0)
    g.update_edge_weight(0, 1, 1.5)               # absolute, not cumulative
    assert g.get_edge(0, 1).cost == pytest.approx(150.0)
    with pytest.raises(ValueError):
        g.update_edge_weight(0, 1, 0)
    with pytest.raises(KeyError):
        g.update_edge_weight(2, 0, 2.0)           # edge does not exist


def test_road_closure_and_reopen(g):
    g.toggle_road_closure(0, 1, True)
    assert g.get_edge(0, 1).cost == math.inf
    g.toggle_road_closure(0, 1, False)
    assert g.get_edge(0, 1).cost == 100.0


def test_both_directions():
    g = Graph()
    g.add_node(Node(0, "a", 0, 0)); g.add_node(Node(1, "b", 0, 0.001))
    g.add_edge(0, 1, 10); g.add_edge(1, 0, 10)
    g.toggle_road_closure(0, 1, True, both_directions=True)
    assert g.get_edge(1, 0).closed


def test_reset_dynamic_state(g):
    g.update_edge_weight(0, 1, 3); g.toggle_road_closure(1, 2, True)
    g.reset_dynamic_state()
    assert g.get_edge(0, 1).cost == 100.0 and g.get_edge(1, 2).cost == 50.0
