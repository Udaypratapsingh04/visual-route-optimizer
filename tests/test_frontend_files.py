import re
from pathlib import Path

FRONTEND = Path("frontend")


def test_index_references_existing_local_assets():
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    local = re.findall(r'(?:src|href)="([^"]+)"', html)
    local = [u for u in local if not u.startswith("http")]
    assert {"style.css", "api.js", "animation.js", "app.js"} <= set(local)
    for name in local:
        assert (FRONTEND / name).exists(), name


def test_every_element_id_used_by_app_js_exists_in_html():
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    js = (FRONTEND / "app.js").read_text(encoding="utf-8")
    ids = set(re.findall(r"\$\('([A-Za-z]+)'\)", js))
    for i in ids:
        assert f'id="{i}"' in html, i
