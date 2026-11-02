"""Day 2 - download a road network from the OSM Overpass API and build data/network.json.

Usage:
  python scripts/fetch_overpass.py --bbox SOUTH WEST NORTH EAST --out data/network.json

Tip: draw your area on https://geojson.io or https://boundingbox.klokantech.com
and read the south/west/north/east values. Aim for 80-120 nodes in the output;
if you get too many/few, shrink/enlarge the box and run again.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from routeopt import Graph, Node, save_graph, haversine_m          # noqa: E402
from routeopt.connectivity import prune_to_largest_scc              # noqa: E402

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HIGHWAYS = ("motorway|trunk|primary|secondary|tertiary|unclassified|residential|"
            "living_street|service|motorway_link|trunk_link|primary_link|"
            "secondary_link|tertiary_link")


def fetch(bbox):
    s, w, n, e = bbox
    query = f"""[out:json][timeout:90];
(way["highway"~"^({HIGHWAYS})$"]({s},{w},{n},{e}););
out body; >; out skel qt;"""
    req = urllib.request.Request(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": query}).encode(),
        headers={"User-Agent": "route-optimizer-dsa-capstone/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def build_graph(osm, bbox):
    s, w, n, e = bbox
    coords = {el["id"]: (el["lat"], el["lon"]) for el in osm["elements"] if el["type"] == "node"}
    ways = [el for el in osm["elements"] if el["type"] == "way"]

    def inside(nid):
        c = coords.get(nid)
        return c is not None and s <= c[0] <= n and w <= c[1] <= e

    # a node is an intersection if >=2 ways use it, or it is a way endpoint
    use_count = defaultdict(int)
    for way in ways:
        for nid in way["nodes"]:
            use_count[nid] += 1
    street_names = defaultdict(set)
    key_nodes = set()
    for way in ways:
        refs = way["nodes"]
        name = way.get("tags", {}).get("name")
        for i, nid in enumerate(refs):
            if use_count[nid] >= 2 or i in (0, len(refs) - 1):
                key_nodes.add(nid)
                if name:
                    street_names[nid].add(name)

    key_nodes = {nid for nid in key_nodes if inside(nid)}
    index = {osm_id: i for i, osm_id in enumerate(sorted(key_nodes))}
    g = Graph()
    for osm_id, i in index.items():
        names = sorted(street_names[osm_id])[:2]
        label = " & ".join(names) if names else f"Junction {i}"
        lat, lon = coords[osm_id]
        g.add_node(Node(i, label, lat, lon))

    best = {}  # (u, v) -> shortest length, to drop parallel duplicates
    for way in ways:
        tags = way.get("tags", {})
        oneway = tags.get("oneway", "no")
        if tags.get("junction") == "roundabout":
            oneway = "yes"
        refs = way["nodes"]
        seg_start, seg_len, valid = None, 0.0, True
        for i, nid in enumerate(refs):
            if i > 0:
                if nid in coords and refs[i - 1] in coords:
                    a, b = coords[refs[i - 1]], coords[nid]
                    seg_len += haversine_m(a[0], a[1], b[0], b[1])
                else:
                    valid = False
            if nid in key_nodes:
                if seg_start is not None and valid and nid != seg_start and seg_len > 0:
                    u, v = index[seg_start], index[nid]
                    if oneway in ("yes", "true", "1"):
                        dirs = [(u, v)]
                    elif oneway == "-1":
                        dirs = [(v, u)]
                    else:
                        dirs = [(u, v), (v, u)]
                    for d in dirs:
                        if d not in best or seg_len < best[d]:
                            best[d] = seg_len
                seg_start, seg_len, valid = nid, 0.0, True
            elif not inside(nid):
                valid = False
    for (u, v), length in best.items():
        g.add_edge(u, v, length)
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbox", nargs=4, type=float, required=True,
                    metavar=("SOUTH", "WEST", "NORTH", "EAST"))
    ap.add_argument("--out", default="data/network.json")
    args = ap.parse_args()

    print("Downloading from Overpass ...")
    osm = fetch(args.bbox)
    g = build_graph(osm, args.bbox)
    print(f"Raw graph:    {g.node_count} nodes, {g.edge_count} directed edges")
    g, removed = prune_to_largest_scc(g)
    print(f"After prune:  {g.node_count} nodes, {g.edge_count} directed edges "
          f"({len(removed)} nodes removed)")
    save_graph(g, args.out, meta={"bbox": args.bbox, "source": "OSM Overpass API"})
    print(f"Saved {args.out}")
    if not 80 <= g.node_count <= 120:
        print("NOTE: target is 80-120 nodes - adjust the bounding box and re-run.")


if __name__ == "__main__":
    main()
