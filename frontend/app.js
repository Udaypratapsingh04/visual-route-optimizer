(() => {
  'use strict';

  const SPEEDS = [1, 2, 5];
  const NODE_STYLE = { radius: 5, color: '#ffffff', weight: 1, fillColor: '#264653', fillOpacity: 0.9 };
  const VISITED_STYLE = { radius: 6, fillColor: '#f4a100', fillOpacity: 0.95 };
  const CURRENT_STYLE = { radius: 9, fillColor: '#ffd60a', fillOpacity: 1 };
  const DIMMED_STYLE = { radius: 4, fillColor: '#f4a100', fillOpacity: 0.3 };
  const PATH_NODE_STYLE = { radius: 6, fillColor: '#1d4ed8', fillOpacity: 1 };

  const $ = (id) => document.getElementById(id);
  const state = {
    nodes: new Map(),        // id -> {id, name, lat, lon}
    nodeLayers: new Map(),   // id -> L.circleMarker
    roads: new Map(),        // "a-b" -> {a, b, fwd, bwd, line, hit}
    start: null, end: null,
    startMarker: null, endMarker: null,
    pathLayer: null,
    lastResult: null,
    runToken: 0,
    currentNode: null,
  };

  // ---------- helpers ----------
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function toast(message, kind = 'info', ms = 4200) {
    const el = document.createElement('div');
    el.className = 'toast ' + kind;
    el.textContent = message;
    $('toasts').appendChild(el);
    setTimeout(() => el.remove(), ms);
  }

  function setStatus(text, warn = false) {
    const el = $('status');
    el.textContent = text;
    el.classList.toggle('warn', warn);
  }

  const nodeName = (id) => (state.nodes.get(id) || {}).name || `Node ${id}`;
  const roadKey = (a, b) => `${Math.min(a, b)}-${Math.max(a, b)}`;
  const currentSpeed = () => SPEEDS[Number($('speed').value)];

  // ---------- Day 11: map ----------
  const map = L.map('map', { zoomControl: true });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20,
  }).addTo(map);
  map.createPane('roads').style.zIndex = 410;
  map.createPane('route').style.zIndex = 420;
  map.createPane('junctions').style.zIndex = 430;
  map.setView([27.4924, 77.6737], 15);
  window.addEventListener('resize', () => map.invalidateSize());

  // ---------- Day 12: graph overlay ----------
  function roadStyle(road) {
    const dirs = [road.fwd, road.bwd].filter(Boolean);
    const closed = dirs.some((e) => e.closed);
    const congestion = Math.max(...dirs.map((e) => e.congestion));
    if (closed) return { color: '#d62828', weight: 5, opacity: 0.95, dashArray: '6 6' };
    if (congestion > 1.01) return { color: congestion >= 3 ? '#e85d04' : '#f4a261', weight: 5, opacity: 0.95, dashArray: null };
    return { color: '#8d99ae', weight: 3, opacity: 0.8, dashArray: dirs.length === 1 ? '2 6' : null };
  }

  function buildRoads(edges) {
    state.roads.forEach((r) => { map.removeLayer(r.line); map.removeLayer(r.hit); });
    state.roads.clear();
    for (const e of edges) {
      const key = roadKey(e.source, e.target);
      let road = state.roads.get(key);
      if (!road) {
        road = { a: Math.min(e.source, e.target), b: Math.max(e.source, e.target), fwd: null, bwd: null };
        state.roads.set(key, road);
      }
      if (e.source === road.a) road.fwd = e; else road.bwd = e;
    }
    for (const road of state.roads.values()) {
      const A = state.nodes.get(road.a), B = state.nodes.get(road.b);
      if (!A || !B) continue;
      const pts = [[A.lat, A.lon], [B.lat, B.lon]];
      road.line = L.polyline(pts, { pane: 'roads', interactive: false, ...roadStyle(road) }).addTo(map);
      road.hit = L.polyline(pts, { pane: 'roads', weight: 16, opacity: 0, color: '#000' }).addTo(map);
      road.hit.on('click', (ev) => { L.DomEvent.stopPropagation(ev); openRoadPopup(road, ev.latlng); });
    }
  }

  function buildNodes() {
    state.nodeLayers.forEach((l) => map.removeLayer(l));
    state.nodeLayers.clear();
    for (const n of state.nodes.values()) {
      const m = L.circleMarker([n.lat, n.lon], { pane: 'junctions', ...NODE_STYLE }).addTo(map);
      m.bindTooltip(`<b>${escapeHtml(n.name)}</b><br>id ${n.id}`);
      m.on('click', () => onNodeClick(n.id));
      state.nodeLayers.set(n.id, m);
    }
  }

  function pinIcon(kind, label) {
    return L.divIcon({ className: '', html: `<div class="pin ${kind}">${label}</div>`, iconSize: [22, 22], iconAnchor: [11, 11] });
  }

  function refreshSelection() {
    if (state.startMarker) { map.removeLayer(state.startMarker); state.startMarker = null; }
    if (state.endMarker) { map.removeLayer(state.endMarker); state.endMarker = null; }
    if (state.start !== null) {
      const n = state.nodes.get(state.start);
      state.startMarker = L.marker([n.lat, n.lon], { icon: pinIcon('start', 'S'), interactive: false, zIndexOffset: 1000 }).addTo(map);
    }
    if (state.end !== null) {
      const n = state.nodes.get(state.end);
      state.endMarker = L.marker([n.lat, n.lon], { icon: pinIcon('end', 'E'), interactive: false, zIndexOffset: 1000 }).addTo(map);
    }
    $('startLabel').textContent = 'Start: ' + (state.start === null ? 'not set' : nodeName(state.start));
    $('endLabel').textContent = 'End: ' + (state.end === null ? 'not set' : nodeName(state.end));
    $('runBtn').disabled = state.start === null || state.end === null;
    if (state.start === null) setStatus('Click a junction to set the START.');
    else if (state.end === null) setStatus('Now click a junction to set the END.');
    else setStatus('Ready. Press "Find route".');
  }

  function onNodeClick(id) {
    animator.stop();
    clearVisuals();
    if (state.start === null) state.start = id;
    else if (state.end === null) {
      if (id === state.start) { toast('End must differ from start.', 'warn'); return; }
      state.end = id;
    } else { state.start = id; state.end = null; }      // third click starts a new selection
    refreshSelection();
  }

  // ---------- Day 13: animation ----------
  function styleNode(id, style) {
    const layer = state.nodeLayers.get(id);
    if (layer) layer.setStyle(style);
  }

  const animator = new ExploreAnimator({
    getSpeed: currentSpeed,
    onVisit: (id) => {
      if (state.currentNode !== null) styleNode(state.currentNode, VISITED_STYLE);
      styleNode(id, CURRENT_STYLE);
      state.currentNode = id;
    },
  });

  function clearVisuals() {
    state.runToken++;
    state.currentNode = null;
    state.nodeLayers.forEach((l) => l.setStyle(NODE_STYLE));
    if (state.pathLayer) { map.removeLayer(state.pathLayer); state.pathLayer = null; }
    $('stats').hidden = true;
    $('skipBtn').disabled = true;
    $('replayBtn').disabled = true;
    state.lastResult = null;
  }

  // ---------- Day 14: final path ----------
  function finishRun(result) {
    $('skipBtn').disabled = true;
    state.currentNode = null;
    result.visited_nodes.forEach((id) => styleNode(id, DIMMED_STYLE));
    if (result.found) {
      const pts = result.path.map((id) => [state.nodes.get(id).lat, state.nodes.get(id).lon]);
      state.pathLayer = L.polyline(pts, { pane: 'route', color: '#1d4ed8', weight: 7, opacity: 0.95, lineCap: 'round' }).addTo(map);
      result.path.forEach((id) => styleNode(id, PATH_NODE_STYLE));
      map.fitBounds(state.pathLayer.getBounds(), { padding: [60, 60], maxZoom: 18 });
      setStatus('Route found. Click any road to block it or add traffic.');
    } else {
      setStatus('No route exists between these junctions (a closed road may be cutting them off).', true);
      toast('No route found.', 'warn');
    }
    $('replayBtn').disabled = false;
  }

  function showStats(m) {
    const el = $('stats');
    el.hidden = false;
    el.innerHTML = [
      `<b>${escapeHtml(m.algorithm === 'astar' ? 'A*' : 'Dijkstra')}</b> (${escapeHtml(m.mode)})`,
      `Nodes explored: <b>${m.nodes_explored}</b>`,
      m.found ? `Route length: <b>${(m.path_length_m / 1000).toFixed(2)} km</b> (${m.path_nodes} junctions)` : 'Route: <b>none</b>',
      `Compute time: ${m.execution_time_us} \u00b5s`,
    ].join('<br>');
  }

  async function runRoute() {
    if (state.start === null || state.end === null) return;
    animator.stop();
    clearVisuals();
    const token = state.runToken;
    const algorithm = $('algo').value;
    $('runBtn').disabled = true;
    setStatus('Computing route...');
    let res;
    try {
      res = await Api.route({ source: state.start, target: state.end, algorithm, mode: $('mode').value });
    } catch (err) {
      if (token === state.runToken) { toast(err.message, 'error', 6000); setStatus('Request failed.', true); }
      $('runBtn').disabled = false;
      return;
    }
    $('runBtn').disabled = false;
    if (token !== state.runToken) return;               // user changed something meanwhile
    const result = res.results[algorithm];
    state.lastResult = result;
    showStats(result.metrics);
    $('skipBtn').disabled = false;
    setStatus('Exploring...');
    animator.start(result.visited_nodes, () => finishRun(result));
  }

  function replay() {
    if (!state.lastResult) return;
    const result = state.lastResult;
    animator.stop();
    state.nodeLayers.forEach((l) => l.setStyle(NODE_STYLE));
    if (state.pathLayer) { map.removeLayer(state.pathLayer); state.pathLayer = null; }
    $('skipBtn').disabled = false;
    $('replayBtn').disabled = true;
    setStatus('Exploring...');
    animator.start(result.visited_nodes, () => finishRun(result));
  }

  // ---------- Day 14: road closures and traffic ----------
  function openRoadPopup(road, latlng) {
    const box = document.createElement('div');
    box.className = 'road-popup';
    const title = document.createElement('div');
    title.className = 'title';
    title.textContent = `${nodeName(road.a)} \u2194 ${nodeName(road.b)}`;
    box.appendChild(title);
    const dirs = [road.fwd, road.bwd].filter(Boolean);
    const info = document.createElement('div');
    info.textContent = dirs.some((e) => e.closed) ? 'Status: BLOCKED'
      : `Traffic: x${Math.max(...dirs.map((e) => e.congestion)).toFixed(1)}`;
    box.appendChild(info);

    const actions = [
      ['Block road', { closed: true }],
      ['Heavy traffic (x3)', { multiplier: 3, closed: false }],
      ['Clear (normal)', { multiplier: 1, closed: false }],
    ];
    for (const [label, change] of actions) {
      const b = document.createElement('button');
      b.textContent = label;
      b.addEventListener('click', () => { map.closePopup(); applyRoadChange(road, change); });
      box.appendChild(b);
    }
    L.popup({ closeButton: true }).setLatLng(latlng).setContent(box).openOn(map);
  }

  async function applyRoadChange(road, change) {
    try {
      const res = await Api.congestion({ source: road.a, target: road.b, both_directions: true, ...change });
      for (const u of res.updated) {
        const e = u.source === road.a ? road.fwd : road.bwd;
        if (e) { e.congestion = u.congestion; e.closed = u.closed; }
      }
      road.line.setStyle(roadStyle(road));
      toast('Road updated.', 'ok', 1800);
      if (state.start !== null && state.end !== null && (state.lastResult || state.pathLayer)) runRoute();   // live re-routing
    } catch (err) {
      toast(err.message, 'error', 6000);
    }
  }

  async function resetRoads() {
    try {
      await Api.reset();
      for (const road of state.roads.values()) {
        [road.fwd, road.bwd].forEach((e) => { if (e) { e.congestion = 1; e.closed = false; } });
        road.line.setStyle(roadStyle(road));
      }
      toast('All roads reset.', 'ok', 1800);
      if (state.start !== null && state.end !== null && state.lastResult) runRoute();
    } catch (err) {
      toast(err.message, 'error', 6000);
    }
  }

  // ---------- Day 15: wiring and startup ----------
  $('runBtn').addEventListener('click', runRoute);
  $('skipBtn').addEventListener('click', () => animator.skip());
  $('replayBtn').addEventListener('click', replay);
  $('clearBtn').addEventListener('click', () => {
    animator.stop(); clearVisuals();
    state.start = null; state.end = null;
    refreshSelection();
  });
  $('resetRoadsBtn').addEventListener('click', resetRoads);
  $('speed').addEventListener('input', () => { $('speedLabel').textContent = currentSpeed() + 'x'; });
  $('algo').addEventListener('change', () => { if (state.start !== null && state.end !== null) { toast('Press "Find route" to apply.', 'info', 1800); } });

  async function init() {
    try {
      const [nodes, edges] = await Promise.all([Api.nodes(), Api.edges()]);
      if (!nodes.length) throw new Error('The network has no nodes. Run the Week 1 data scripts first.');
      nodes.forEach((n) => state.nodes.set(n.id, n));
      buildRoads(edges);
      buildNodes();
      map.fitBounds(L.latLngBounds(nodes.map((n) => [n.lat, n.lon])), { padding: [30, 30] });
      refreshSelection();
    } catch (err) {
      setStatus(err.message, true);
      toast(err.message, 'error', 8000);
    }
  }
  init();
})();
