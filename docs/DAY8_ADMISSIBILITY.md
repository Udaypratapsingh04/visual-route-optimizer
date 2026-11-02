# Day 8 - A* heuristic: admissibility and consistency

**Setup.** f(n) = g(n) + h(n), where g(n) is the cost of the best known path from the source to n and
h(n) = d(n, t), the Haversine (great-circle) distance from n to the target t.
d is a metric on the sphere, so it satisfies the **triangle inequality**: d(a, c) <= d(a, b) + d(b, c).

**Data assumption (checked by `scripts/validate_network.py`).** Every road segment is at least as long
as the straight line between its endpoints: length(u, v) >= d(u, v). A road cannot be shorter than the
straight line, and OSM-derived lengths follow the road geometry so they hold this by construction.
Congestion multipliers must be >= 1.

## Admissibility: h(n) <= h*(n)
Let P = (n = v0, v1, ..., vk = t) be any path from n to t, and h*(n) the cost of the cheapest one.
cost(P) = sum of w(v_i, v_i+1) >= sum of d(v_i, v_i+1)   (edge cost >= length >= straight line)
          >= d(v0, vk)                                    (triangle inequality, applied repeatedly)
          = h(n).
This holds for every path, including the cheapest, so h(n) <= h*(n). The heuristic never overestimates.
In "time" mode both sides are divided by the same free-flow speed, so the argument is unchanged.

## Consistency: h(u) <= w(u, v) + h(v)
h(u) = d(u, t) <= d(u, v) + d(v, t) <= w(u, v) + h(v). The first step is the triangle inequality,
the second is length(u, v) >= d(u, v).

## Why it matters
- Admissible -> A* returns an optimal path (it cannot prune the optimal route because f never exceeds the true cost through it).
- Consistent -> f(n) never decreases along a path, so each node is settled once with its final g.
  That is why our implementation keeps a `closed` set and never reopens nodes.
- With h = 0, A* becomes Dijkstra (consistent and admissible but uninformed).

## What breaks it
- Congestion multiplier < 1 (a road "faster than free flow") -> h can overestimate -> A* may return a suboptimal path.
- Negative edge costs -> neither Dijkstra nor this A* is valid (use Bellman-Ford).
- A road shorter than its straight-line distance (bad data).

## Viva cheat sheet
- **Complexity with a binary heap:** O((V + E) log V). Each node is popped once (V x log V); each edge relaxes at most once with a decrease-key (E x log V). Heap size <= V thanks to the position map. Without a heap (linear scan for the minimum) it is O(V^2).
- **Why not negative edges?** Dijkstra assumes that once a node is popped its distance is final; a negative edge later could lower it.
- **Admissible vs consistent:** consistent implies admissible, not the other way round. Admissible guarantees optimality for tree search; consistency guarantees it for graph search without reopening nodes.
- **Why A* can be slower in microseconds even when it explores fewer nodes:** each expansion evaluates Haversine (trig functions). On a ~100-node graph this overhead can outweigh the saving, so the node count is the fair metric; wall-clock wins show on larger graphs.
