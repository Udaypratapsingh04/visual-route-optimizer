from routeopt import Graph, Node
from routeopt.connectivity import (bfs, dfs, prune_to_largest_scc,
                                   strongly_connected_components,
                                   weakly_connected_components)


def make(n, edges, two_way=()):
    g = Graph()
    for i in range(n):
        g.add_node(Node(i, f"n{i}", 27 + i * 0.001, 77))
    for u, v in edges:
        g.add_edge(u, v, 10)
    for u, v in two_way:
        g.add_edge(u, v, 10); g.add_edge(v, u, 10)
    return g


def test_bfs_dfs_reach_same_set():
    g = make(5, [], two_way=[(0, 1), (1, 2), (2, 3), (3, 4)])
    assert bfs(g, 0) == [0, 1, 2, 3, 4]
    assert set(dfs(g, 0)) == {0, 1, 2, 3, 4}


def test_single_component():
    g = make(4, [], two_way=[(0, 1), (1, 2), (2, 3)])
    assert len(weakly_connected_components(g)) == 1
    assert len(strongly_connected_components(g)) == 1


def test_isolated_node_detected_and_pruned():
    g = make(5, [], two_way=[(0, 1), (1, 2), (2, 3)])   # node 4 isolated
    assert len(weakly_connected_components(g)) == 2
    pruned, removed = prune_to_largest_scc(g)
    assert removed == {4} and pruned.node_count == 4
    assert len(strongly_connected_components(pruned)) == 1


def test_one_way_trap_breaks_strong_but_not_weak():
    # 0 <-> 1 -> 2 : you can enter 2 but never leave
    g = make(3, [(1, 2)], two_way=[(0, 1)])
    assert len(weakly_connected_components(g)) == 1
    assert len(strongly_connected_components(g)) == 2
    pruned, removed = prune_to_largest_scc(g)
    assert removed == {2}


def test_closure_awareness():
    g = make(3, [], two_way=[(0, 1), (1, 2)])
    g.toggle_road_closure(1, 2, True, both_directions=True)
    assert len(strongly_connected_components(g)) == 1                       # physical network
    assert len(strongly_connected_components(g, respect_closures=True)) == 2


def test_deep_chain_no_recursion_error():
    n = 5000
    g = make(n, [], two_way=[(i, i + 1) for i in range(n - 1)])
    assert len(strongly_connected_components(g)) == 1
    assert len(dfs(g, 0)) == n
