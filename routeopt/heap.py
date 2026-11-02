"""Day 6 - indexed binary min-heap with decrease-key.

Each item (a node id) can be in the heap at most once. A position map
`item -> index in the array` makes decrease_key O(log n) instead of O(n).

    push          O(log n)
    pop_min       O(log n)
    decrease_key  O(log n)
    peek / len / in   O(1)
"""
from __future__ import annotations

from typing import Any, Dict, Hashable, List, Tuple


class IndexedMinHeap:
    def __init__(self) -> None:
        self._items: List[Hashable] = []
        self._prio: List[Any] = []
        self._pos: Dict[Hashable, int] = {}

    # ---------- inspection ----------
    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, item: Hashable) -> bool:
        return item in self._pos

    def is_empty(self) -> bool:
        return not self._items

    def priority_of(self, item: Hashable) -> Any:
        return self._prio[self._pos[item]]

    def peek(self) -> Tuple[Hashable, Any]:
        if not self._items:
            raise IndexError("peek from empty heap")
        return self._items[0], self._prio[0]

    # ---------- operations ----------
    def push(self, item: Hashable, priority: Any) -> None:
        if item in self._pos:
            raise ValueError(f"{item!r} already in heap; use decrease_key")
        self._items.append(item)
        self._prio.append(priority)
        self._pos[item] = len(self._items) - 1
        self._sift_up(len(self._items) - 1)

    def decrease_key(self, item: Hashable, new_priority: Any) -> None:
        i = self._pos[item]                      # KeyError if absent
        if new_priority > self._prio[i]:
            raise ValueError("decrease_key cannot increase a priority")
        self._prio[i] = new_priority
        self._sift_up(i)

    def push_or_decrease(self, item: Hashable, priority: Any) -> bool:
        """Insert, or lower the priority if it improves. True if the heap changed."""
        if item not in self._pos:
            self.push(item, priority)
            return True
        if priority < self._prio[self._pos[item]]:
            self.decrease_key(item, priority)
            return True
        return False

    def pop_min(self) -> Tuple[Hashable, Any]:
        if not self._items:
            raise IndexError("pop from empty heap")
        top = (self._items[0], self._prio[0])
        last = len(self._items) - 1
        self._swap(0, last)
        self._items.pop()
        self._prio.pop()
        del self._pos[top[0]]
        if self._items:
            self._sift_down(0)
        return top

    # ---------- internals ----------
    def _swap(self, i: int, j: int) -> None:
        self._items[i], self._items[j] = self._items[j], self._items[i]
        self._prio[i], self._prio[j] = self._prio[j], self._prio[i]
        self._pos[self._items[i]] = i
        self._pos[self._items[j]] = j

    def _sift_up(self, i: int) -> None:
        while i > 0:
            parent = (i - 1) // 2
            if self._prio[i] < self._prio[parent]:
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i: int) -> None:
        n = len(self._items)
        while True:
            left, right, smallest = 2 * i + 1, 2 * i + 2, i
            if left < n and self._prio[left] < self._prio[smallest]:
                smallest = left
            if right < n and self._prio[right] < self._prio[smallest]:
                smallest = right
            if smallest == i:
                return
            self._swap(i, smallest)
            i = smallest
