# Day 1 - Mathematical Formulation & Schema Design

## Formal model
A road network is a **weighted directed graph** G = (V, E, w):
- V = road intersections (junctions), |V| = n
- E ⊆ V × V = directed road segments, |E| = m (a two-way road = two directed edges)
- w : E → [0, ∞] = traversal cost, `w(e) = length_m × congestion`, or ∞ if the road is closed

All weights are non-negative, which is the precondition for Dijkstra and A*.

## Entities
| Entity | Fields | Notes |
|---|---|---|
| `Node` | `id`, `name`, `lat`, `lon` | immutable (frozen dataclass) |
| `Edge` | `source`, `target`, `length_m`, `congestion = 1.0`, `closed = False` | `cost` is a computed property |
| `Graph` | `Map<NodeId, List<Edge>>` + `(u,v) -> Edge` index | adjacency list |

## Why an adjacency list (complexity rationale)
| Operation | Adjacency list | Adjacency matrix |
|---|---|---|
| Space | **O(V + E)** | O(V²) |
| Iterate neighbours of u | **O(deg u)** | O(V) |
| Edge lookup (u, v) | O(1) via index dict | O(1) |
| Full traversal (BFS/DFS) | **O(V + E)** | O(V²) |

Road networks are **sparse**: each junction touches ~3 roads, so m ≈ 3n, far below n².
Example with our sample file: V = 100, E = 320 -> ~420 stored items vs 10,000 matrix cells (~24× more).
For a city of 100,000 junctions the matrix would need 10¹⁰ cells; the list needs ~4×10⁵ entries.
Dijkstra with a binary heap on this structure runs in O((V + E) log V).

## Design decisions to mention in the viva
- Directed edges model one-way streets exactly.
- `congestion` and `closed` live on the edge, so traffic and closures change cost **without rebuilding** the graph.
- `Edge.length_m` stays the true geometric length, which keeps the Haversine heuristic admissible
  even when congestion multiplies the cost (cost >= length >= straight-line distance, as long as congestion >= 1).
  Note: `update_edge_weight` accepts any multiplier > 0; for A* correctness use multipliers >= 1.
