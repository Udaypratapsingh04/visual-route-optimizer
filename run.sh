#!/usr/bin/env bash
# One-command run (macOS/Linux):  bash run.sh
set -e
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install -q -r requirements.txt
[ -f data/network.json ] || .venv/bin/python scripts/generate_sample_network.py --out data/network.json
echo "Open http://127.0.0.1:8000/compare.html"
.venv/bin/python -m uvicorn api.main:app --port 8000
