# Visual Route & Transit Optimizer - Week 1 (graph engine)

Python 3.10+. No runtime dependencies (only `pytest` for tests).

## Setup
```
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## Day-by-day commands
```
# Day 2 - data (real OSM data; or the offline sample)
python scripts/fetch_overpass.py --bbox SOUTH WEST NORTH EAST --out data/network.json
python scripts/generate_sample_network.py --out data/network.json
python scripts/validate_network.py data/network.json --geojson data/network.geojson

# Day 3 - Haversine + loader tests
pytest tests/test_haversine.py tests/test_loader.py -v

# Day 4 - connectivity (must print RESULT: PASS)
python scripts/check_connectivity.py data/network.json
python scripts/check_connectivity.py data/network.json --prune --out data/network.json

# Day 5 - dynamic weights, then the whole suite
pytest -v
```
