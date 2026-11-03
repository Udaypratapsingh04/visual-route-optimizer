(() => {
  'use strict';
  const SPEEDS = [1, 2, 5];
  const NODE_STYLE = { radius: 4, color: '#ffffff', weight: 1, fillColor: '#264653', fillOpacity: 0.9 };
  const VISITED = { radius: 5, fillColor: '#f4a100', fillOpacity: 0.95 };
  const CURRENT = { radius: 8, fillColor: '#ffd60a', fillOpacity: 1 };
  const DIMMED = { radius: 3, fillColor: '#f4a100', fillOpacity: 0.3 };
  const ON_PATH = { radius: 5, fillColor: '#1d4ed8', fillOpacity: 1 };

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const speed = () => SPEEDS[Number($('speed').value)];
  const roadKey = (a, b) => `${Math.min(a, b)}-${Math.max(a, b)}`;

  function toast(msg, kind = 'info', ms = 4200) {
    const el = document.createElement('div');
    el.className = 'toast ' + kind; el.textContent = msg;
    $('toasts').appendChild(el); setTimeout(() => el.remove(), ms);
  }
  function setStatus(t, warn = false) { $('status').textContent = t; $('status').classList.toggle('warn', warn); }

  const S = { nodes: new Map(), roads: new Map(), start: null, end: null, token: 0, last: null, finished: 0 };
  const nodeName = (id) => (S.nodes.get(id) || {}).name || `Node ${id}`;

  function roadStyle(r) {
    const dirs = [r.fwd, r.bwd].filter(Boolean);
    if (dirs.some((e) => e.closed)) return { color: '#d62828', weight: 4, opacity: 0.95, dashArray: '6 6' };
    const c = Math.max(...dirs.map((e) => e.congestion));
    if (c > 1.01) return { color: c >= 3 ? '#e85d04' : '#f4a261', weight: 4, opacity: 0.95, dashArray: null };
    return { color: '#8d99ae', weight: 2, opacity: 0.8, dashArray: dirs.length === 1 ? '2 6' : null };
  }

  // One View = one Leaflet map + its overlay layers + its HUD + its animator.
  class View {
    constructor(mapId, hudId, algo, title) {
      this.algo = algo; this.title = title; this.hud = $(hudId);
      this.map = L.map(mapId);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO', subdomains: 'abcd', maxZoom: 20 }).addTo(this.map);
      ['roads:410', 'route:420', 'junctions:430'].forEach((p) => { const [n, z] = p.split(':'); this.map.createPane(n).style.zIndex = z; });
      this.map.setView([27.4924, 77.6737], 15);
      this.lines = new Map(); this.layers = new Map(); this.pins = []; this.path = null; this.cur = null; this.count = 0;
      this.animator = new ExploreAnimator({
        getSpeed: speed,
        onVisit: (id) => {
          if (this.cur !== null) this.style(this.cur, VISITED);
          this.style(id, CURRENT); this.cur = id; this.count++; this.renderHud({ live: true });
        },
      });
    }
    style(id, st) { const l = this.layers.get(id); if (l) l.setStyle(st); }
    build() {
      for (const r of S.roads.values()) {
        const A = S.nodes.get(r.a), B = S.nodes.get(r.b);
        if (!A || !B) continue;
        const pts = [[A.lat, A.lon], [B.lat, B.lon]];
        this.lines.set(roadKey(r.a, r.b), L.polyline(pts, { pane: 'roads', interactive: false, ...roadStyle(r) }).addTo(this.map));
        const hit = L.polyline(pts, { pane: 'roads', weight: 14, opacity: 0, color: '#000' }).addTo(this.map);
        hit.on('click', (ev) => { L.DomEvent.stopPropagation(ev); roadPopup(this, r, ev.latlng); });
      }
      for (const n of S.nodes.values()) {
        const m = L.circleMarker([n.lat, n.lon], { pane: 'junctions', ...NODE_STYLE }).addTo(this.map);
        m.bindTooltip(`<b>${esc(n.name)}</b><br>id ${n.id}`);
        m.on('click', () => onNodeClick(n.id));
        this.layers.set(n.id, m);
      }
    }
    restyleRoads() { for (const r of S.roads.values()) { const l = this.lines.get(roadKey(r.a, r.b)); if (l) l.setStyle(roadStyle(r)); } }
    drawPins() {
      this.pins.forEach((p) => this.map.removeLayer(p)); this.pins = [];
      [[S.start, 'start', 'S'], [S.end, 'end', 'E']].forEach(([id, cls, lab]) => {
        if (id === null) return;
        const n = S.nodes.get(id);
        this.pins.push(L.marker([n.lat, n.lon], { interactive: false, zIndexOffset: 1000,
          icon: L.divIcon({ className: '', html: `<div class="pin ${cls}">${lab}</div>`, iconSize: [22, 22], iconAnchor: [11, 11] }) }).addTo(this.map));
      });
    }
    reset() {
      this.animator.stop(); this.cur = null; this.count = 0;
      this.layers.forEach((l) => l.setStyle(NODE_STYLE));
      if (this.path) { this.map.removeLayer(this.path); this.path = null; }
      this.result = null; this.renderHud({});
    }
    finish(result) {
      this.cur = null;
      result.visited_nodes.forEach((id) => this.style(id, DIMMED));
      if (result.found) {
        const pts = result.path.map((id) => [S.nodes.get(id).lat, S.nodes.get(id).lon]);
        this.path = L.polyline(pts, { pane: 'route', color: '#1d4ed8', weight: 6, opacity: 0.95, lineCap: 'round' }).addTo(this.map);
        result.path.forEach((id) => this.style(id, ON_PATH));
      }
      this.result = result; this.renderHud({});
    }
    renderHud({ live = false } = {}) {
      const m = this.result && this.result.metrics;
      const explored = live || !m ? this.count : m.nodes_explored;
      let html = `<h3>${this.title}</h3>Nodes explored<div class="big">${explored}</div>`;
      if (m && !live) {
        html += `Execution time: <b>${(m.execution_time_us / 1000).toFixed(3)} ms</b><br>`;
        html += m.found ? `Path length: <b>${(m.path_length_m / 1000).toFixed(2)} km</b> (${m.path_nodes} junctions)` : '<b>No route found</b>';
        if (this.algo === 'astar' && S.compare) html += `<div class="rating">${S.compare.saved}% fewer nodes &middot; ${esc(S.compare.rating)}</div>`;
      }
      this.hud.innerHTML = html;
    }
  }

  const L_VIEW = new View('mapL', 'hudL', 'dijkstra', 'Dijkstra');
  const R_VIEW = new View('mapR', 'hudR', 'astar', 'A* (Haversine)');
  const views = [L_VIEW, R_VIEW];

  // keep both maps in lock-step
  let syncing = false;
  function link(a, b) {
    a.map.on('moveend', () => {
      if (syncing) return;
      syncing = true; b.map.setView(a.map.getCenter(), a.map.getZoom(), { animate: false }); syncing = false;
    });
  }
  link(L_VIEW, R_VIEW); link(R_VIEW, L_VIEW);
  window.addEventListener('resize', () => views.forEach((v) => v.map.invalidateSize()));

  function refreshSelection() {
    views.forEach((v) => v.drawPins());
    $('runBtn').disabled = S.start === null || S.end === null;
    setStatus(S.start === null ? 'Click a junction on either map to set START.'
      : S.end === null ? `Start: ${nodeName(S.start)}. Now click the END.`
      : `${nodeName(S.start)} \u2192 ${nodeName(S.end)}. Press "Run both".`);
  }
  function clearAll() {
    S.token++; views.forEach((v) => v.reset()); $('summary').hidden = true; S.last = null; S.compare = null;
    $('skipBtn').disabled = true; $('replayBtn').disabled = true;
  }
  function onNodeClick(id) {
    clearAll();
    if (S.start === null) S.start = id;
    else if (S.end === null) { if (id === S.start) { toast('End must differ from start.', 'warn'); return; } S.end = id; }
    else { S.start = id; S.end = null; }
    refreshSelection();
  }

  function animateBoth(res) {
    S.finished = 0;
    $('skipBtn').disabled = false; $('replayBtn').disabled = true;
    setStatus('Exploring...');
    views.forEach((v) => {
      const r = res.results[v.algo];
      v.reset();
      v.animator.start(r.visited_nodes, () => {
        v.finish(r); S.finished++;
        if (S.finished === views.length) allDone(res);
      });
    });
  }
  function allDone(res) {
    $('skipBtn').disabled = true; $('replayBtn').disabled = false;
    const d = res.results.dijkstra, a = res.results.astar;
    if (!d.found) { setStatus('No route exists between these junctions (closed roads?).', true); toast('No route found.', 'warn'); return; }
    S.compare = { saved: res.nodes_saved_pct, rating: res.efficiency_rating };
    R_VIEW.renderHud({});
    const sum = $('summary'); sum.hidden = false;
    sum.textContent = `A* explored ${a.metrics.nodes_explored} nodes vs Dijkstra ${d.metrics.nodes_explored} \u2014 ${res.nodes_saved_pct}% fewer \u00b7 same route length: ${(a.metrics.path_length_m / 1000).toFixed(2)} km`;
    setStatus('Done. Click a road to block it or add traffic.');
    const bounds = L.latLngBounds(a.path.map((id) => [S.nodes.get(id).lat, S.nodes.get(id).lon]));
    L_VIEW.map.fitBounds(bounds, { padding: [60, 60], maxZoom: 18 });
  }

  async function run() {
    if (S.start === null || S.end === null) return;
    clearAll();
    const token = S.token;
    $('runBtn').disabled = true; setStatus('Computing...');
    let res;
    try { res = await Api.route({ source: S.start, target: S.end, algorithm: 'both', mode: $('mode').value }); }
    catch (err) { if (token === S.token) { toast(err.message, 'error', 6000); setStatus('Request failed.', true); } $('runBtn').disabled = false; return; }
    $('runBtn').disabled = false;
    if (token !== S.token) return;
    S.last = res; animateBoth(res);
  }

  // ----- road closures / traffic (applies to both maps) -----
  function roadPopup(view, r, latlng) {
    const box = document.createElement('div'); box.className = 'road-popup';
    box.innerHTML = `<div class="title">${esc(nodeName(r.a))} \u2194 ${esc(nodeName(r.b))}</div>`;
    [['Block road', { closed: true }], ['Heavy traffic (x3)', { multiplier: 3, closed: false }], ['Clear (normal)', { multiplier: 1, closed: false }]]
      .forEach(([label, change]) => {
        const b = document.createElement('button'); b.textContent = label;
        b.addEventListener('click', () => { view.map.closePopup(); changeRoad(r, change); });
        box.appendChild(b);
      });
    L.popup().setLatLng(latlng).setContent(box).openOn(view.map);
  }
  async function changeRoad(r, change) {
    try {
      const res = await Api.congestion({ source: r.a, target: r.b, both_directions: true, ...change });
      res.updated.forEach((u) => { const e = u.source === r.a ? r.fwd : r.bwd; if (e) { e.congestion = u.congestion; e.closed = u.closed; } });
      views.forEach((v) => v.restyleRoads());
      toast('Road updated.', 'ok', 1500);
      if (S.last) run();
    } catch (err) { toast(err.message, 'error', 6000); }
  }
  async function resetRoads() {
    try {
      await Api.reset();
      S.roads.forEach((r) => [r.fwd, r.bwd].forEach((e) => { if (e) { e.congestion = 1; e.closed = false; } }));
      views.forEach((v) => v.restyleRoads()); toast('All roads reset.', 'ok', 1500);
      if (S.last) run();
    } catch (err) { toast(err.message, 'error', 6000); }
  }

  $('runBtn').addEventListener('click', run);
  $('skipBtn').addEventListener('click', () => views.forEach((v) => v.animator.skip()));
  $('replayBtn').addEventListener('click', () => { if (S.last) animateBoth(S.last); });
  $('clearBtn').addEventListener('click', () => { clearAll(); S.start = null; S.end = null; refreshSelection(); });
  $('resetRoadsBtn').addEventListener('click', resetRoads);
  $('speed').addEventListener('input', () => { $('speedLabel').textContent = speed() + 'x'; });

  (async function init() {
    try {
      const [nodes, edges] = await Promise.all([Api.nodes(), Api.edges()]);
      if (!nodes.length) throw new Error('The network has no nodes. Run the Week 1 data scripts first.');
      nodes.forEach((n) => S.nodes.set(n.id, n));
      for (const e of edges) {
        const k = roadKey(e.source, e.target);
        let r = S.roads.get(k);
        if (!r) { r = { a: Math.min(e.source, e.target), b: Math.max(e.source, e.target), fwd: null, bwd: null }; S.roads.set(k, r); }
        if (e.source === r.a) r.fwd = e; else r.bwd = e;
      }
      views.forEach((v) => v.build());
      const bounds = L.latLngBounds(nodes.map((n) => [n.lat, n.lon]));
      views.forEach((v) => v.map.invalidateSize());
      L_VIEW.map.fitBounds(bounds, { padding: [30, 30] });
      views.forEach((v) => v.renderHud({}));
      refreshSelection();
    } catch (err) { setStatus(err.message, true); toast(err.message, 'error', 8000); }
  })();
})();
