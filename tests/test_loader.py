import json
from routeopt import haversine_m, load_graph, save_graph


def test_load_computes_haversine_and_bidirectional(tmp_path):
    p = tmp_path / "n.json"
    p.write_text(json.dumps({
        "nodes": [{"id": 0, "lat": 27.0, "lon": 77.0}, {"id": 1, "lat": 27.001, "lon": 77.0}],
        "edges": [{"source": 0, "target": 1, "bidirectional": True}],
    }))
    g = load_graph(p)
    assert g.edge_count == 2
    assert g.get_edge(0, 1).length_m == haversine_m(27.0, 77.0, 27.001, 77.0)


def test_bad_edges_are_skipped_with_warnings(tmp_path):
    p = tmp_path / "n.json"
    p.write_text(json.dumps({
        "nodes": [{"id": 0, "lat": 27.0, "lon": 77.0}, {"id": 1, "lat": 27.0, "lon": 77.0}],
        "edges": [{"source": 0, "target": 1, "length_m": 0},
                  {"source": 0, "target": 0, "length_m": 5}],
    }))
    g = load_graph(p)
    assert g.edge_count == 0 and len(g.warnings) == 2


def test_roundtrip(tmp_path):
    g = load_graph("data/network.json")
    save_graph(g, tmp_path / "copy.json")
    g2 = load_graph(tmp_path / "copy.json")
    assert (g.node_count, g.edge_count) == (g2.node_count, g2.edge_count)
