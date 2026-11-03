"""Day 10 - REST API (FastAPI) + Day 11 static frontend.  Run from the project root:

    uvicorn api.main:app --reload --port 8000
App:     http://127.0.0.1:8000/
API docs: http://127.0.0.1:8000/docs
"""
import os
import sys
from pathlib import Path
from typing import Literal, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException                           # noqa: E402
from fastapi.middleware.cors import CORSMiddleware                   # noqa: E402
from fastapi.staticfiles import StaticFiles                          # noqa: E402
from pydantic import BaseModel                                       # noqa: E402

from routeopt import load_graph, service                             # noqa: E402

NETWORK_PATH = os.environ.get("NETWORK_PATH", "data/network.json")
graph = load_graph(NETWORK_PATH)

app = FastAPI(title="Visual Route & Transit Optimizer")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class RouteRequest(BaseModel):
    source: int
    target: int
    algorithm: Literal["dijkstra", "astar", "both"] = "both"
    mode: Literal["distance", "time"] = "distance"


class CongestionRequest(BaseModel):
    source: int
    target: int
    multiplier: Optional[float] = None      # >= 1 keeps A* optimal
    closed: Optional[bool] = None
    both_directions: bool = True


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'\""))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/nodes")
def get_nodes():
    return service.list_nodes(graph)


@app.get("/api/edges")
def get_edges():
    return service.list_edges(graph)


@app.post("/api/route")
def post_route(req: RouteRequest):
    return _call(service.compute_route, graph, req.source, req.target, req.algorithm, req.mode)


@app.post("/api/edges/congestion")
def post_congestion(req: CongestionRequest):
    return _call(service.set_congestion, graph, req.source, req.target,
                 req.multiplier, req.closed, req.both_directions)


@app.post("/api/reset")
def reset():
    graph.reset_dynamic_state()
    return {"status": "ok"}


# Day 11: serve the Leaflet frontend. Mounted last so the /api routes take priority.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
