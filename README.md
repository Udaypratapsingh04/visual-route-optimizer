# Visual Route & Transit Optimizer

Python 3.10+.  Week 1 = graph engine, Week 2 = routing algorithms + REST API, Week 3 = interactive map.

## Setup
```
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## Week 1 (data + graph)
```
python scripts/fetch_overpass.py --bbox SOUTH WEST NORTH EAST --out data/network.json
python scripts/generate_sample_network.py --out data/network.json     # offline placeholder
python scripts/validate_network.py data/network.json --geojson data/network.geojson
python scripts/check_connectivity.py data/network.json
```

## Week 2 (algorithms + API)
```
pytest -v                                                  # all tests
python scripts/demo_route.py 0 99 --mode distance          # Dijkstra vs A* for one pair
python scripts/benchmark.py --pairs 200 --mode distance --out data/benchmark.json
uvicorn api.main:app --reload --port 8000                  # then open http://127.0.0.1:8000/docs
```

### API
| Method | Path | Body |
|---|---|---|
| GET | `/api/nodes` | - |
| GET | `/api/edges` | - |
| POST | `/api/route` | `{"source":0,"target":99,"algorithm":"both","mode":"distance"}` |
| POST | `/api/edges/congestion` | `{"source":0,"target":1,"multiplier":2.5,"closed":false}` |
| POST | `/api/reset` | - |

## Week 3 (interactive map)
```
uvicorn api.main:app --reload --port 8000
```
Open http://127.0.0.1:8000/ - click two junctions (start, end), press **Find route**, watch the search expand,
then click any road to block it or add traffic and the route recomputes live.
Files: `frontend/index.html`, `style.css`, `api.js`, `animation.js`, `app.js` (Leaflet is loaded from a CDN, so you need internet for the map tiles).

Docs: `docs/DAY1_DESIGN.md`, `docs/DAY8_ADMISSIBILITY.md`.
