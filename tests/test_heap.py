import heapq
import random
import pytest
from routeopt.heap import IndexedMinHeap


def test_pop_order_sorted():
    h = IndexedMinHeap()
    for i, p in enumerate([5, 3, 8, 1, 9, 2]):
        h.push(i, p)
    assert [h.pop_min()[1] for _ in range(6)] == [1, 2, 3, 5, 8, 9]
    assert h.is_empty()


def test_decrease_key_reorders():
    h = IndexedMinHeap()
    h.push("a", 10); h.push("b", 20); h.push("c", 30)
    h.decrease_key("c", 5)
    assert h.pop_min() == ("c", 5)


def test_push_or_decrease():
    h = IndexedMinHeap()
    assert h.push_or_decrease("x", 10) is True
    assert h.push_or_decrease("x", 12) is False       # worse -> ignored
    assert h.push_or_decrease("x", 4) is True
    assert h.priority_of("x") == 4 and len(h) == 1


def test_errors():
    h = IndexedMinHeap()
    with pytest.raises(IndexError):
        h.pop_min()
    h.push(1, 5)
    with pytest.raises(ValueError):
        h.push(1, 3)
    with pytest.raises(ValueError):
        h.decrease_key(1, 9)
    with pytest.raises(KeyError):
        h.decrease_key(42, 1)


def test_matches_heapq_on_random_workload():
    rnd = random.Random(1)
    h = IndexedMinHeap()
    prios = {}
    for i in range(500):
        prios[i] = rnd.random()
        h.push(i, prios[i])
    for i in rnd.sample(range(500), 200):               # decrease a bunch
        prios[i] -= rnd.random()
        h.decrease_key(i, prios[i])
    expected = sorted(prios.values())
    got = [h.pop_min()[1] for _ in range(500)]
    assert got == expected


def test_tuple_priorities():
    h = IndexedMinHeap()
    h.push("a", (5.0, 2.0)); h.push("b", (5.0, 1.0))
    assert h.pop_min()[0] == "b"                          # tie on f broken by h
