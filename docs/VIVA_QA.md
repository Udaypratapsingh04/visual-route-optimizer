# Day 20 - viva preparation

**1. What is the time complexity of Dijkstra with a binary heap?**
O((V + E) log V). Each node is extracted once (V log V). Each edge relaxes at most once, costing a decrease-key (E log V). Our heap has a position map, so it never holds more than V items. With an unsorted array instead of a heap it is O(V²).

**2. Why a heap and not a plain list?**
Finding the minimum in a list is O(V) per step. The heap gives O(log V) insert, extract-min and decrease-key.

**3. Can Dijkstra handle negative edges? Why not?**
No. It assumes that when a node is popped its distance is final. A negative edge discovered later could improve it. Use Bellman-Ford, O(VE). Road lengths are never negative, so this does not arise here.

**4. What is an admissible heuristic? Is yours?**
h(n) never overestimates the true remaining cost. Straight-line (Haversine) distance is admissible because any road path between two points is at least as long as the great-circle distance. Proof in `docs/DAY8_ADMISSIBILITY.md`.

**5. Admissible vs consistent?**
Consistent means h(u) <= cost(u,v) + h(v) for every edge. Consistent implies admissible, not the reverse. With a consistent heuristic, f never decreases along a path and each node is settled exactly once, so no reopening is needed. Haversine is consistent by the triangle inequality.

**6. When would A* return a wrong answer?**
If h overestimates: e.g. a congestion multiplier below 1 (a road faster than free flow), or edge lengths shorter than the straight line (bad data). Then it can settle a node with a non-optimal g.

**7. How is A* related to Dijkstra?**
Dijkstra is A* with h(n) = 0.

**8. Why does A* explore fewer nodes?**
The priority f = g + h favours nodes that are both cheap to reach and close to the goal, so the frontier is a beam toward the target instead of a circle.

**9. Your A* took more microseconds than Dijkstra in some runs. Why?**
Each A* expansion evaluates Haversine (trigonometry), which costs more than adding two numbers. On a ~100-node graph that overhead can exceed the savings. Nodes explored is the fair metric; wall-clock gains appear on larger graphs.

**10. Why an adjacency list rather than a matrix?**
Road graphs are sparse (~3 roads per junction). The list needs O(V + E) memory and visits neighbours in O(degree). A matrix needs O(V²) memory and O(V) per neighbour scan.

**11. How do road closures and traffic work without rebuilding the graph?**
Each edge stores `congestion` and `closed`. The cost is computed on demand: infinity if closed, else length x congestion. The algorithms skip infinite-cost edges.

**12. How did you make sure the network is usable?**
BFS/DFS plus Kosaraju's strongly connected components. We keep only the largest strongly connected component, so every remaining junction can reach every other one while obeying one-way streets.

**13. How do you know your implementations are correct?**
Unit tests; Dijkstra checked against Bellman-Ford on random pairs; A* checked against Dijkstra on 200 pairs plus a 2000-query stress test with random closures and traffic (`scripts/stress_test.py`).

**14. How would this scale to a whole city?**
Millions of nodes need preprocessing: contraction hierarchies, ALT (landmarks), or bidirectional search. A spatial index would be used for snapping clicks to roads. Python would be replaced by a compiled language or the heap moved to native code.

**15. What are the limits of the Haversine heuristic?**
It ignores one-way streets, rivers and detours, so it can be loose on winding networks. A tighter heuristic means fewer nodes explored. In time mode it divides by the free-flow speed to stay admissible.
