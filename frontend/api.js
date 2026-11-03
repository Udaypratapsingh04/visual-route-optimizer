// Thin wrapper around the REST API. Same origin by default; open the page with
// ?api=http://127.0.0.1:8000 if you serve the frontend from somewhere else.
const API_BASE = new URLSearchParams(location.search).get('api') || '';

async function apiFetch(path, options = {}) {
  let resp;
  try {
    resp = await fetch(API_BASE + path, { headers: { 'Content-Type': 'application/json' }, ...options });
  } catch (err) {
    throw new Error('Cannot reach the API server. Is uvicorn running?');
  }
  let data = null;
  try { data = await resp.json(); } catch (_) { /* empty or non-JSON body */ }
  if (!resp.ok) {
    let detail = data && data.detail;
    if (Array.isArray(detail)) detail = detail.map(d => d.msg).join('; ');
    throw new Error(detail || `Request failed (${resp.status})`);
  }
  return data;
}

const Api = {
  nodes: () => apiFetch('/api/nodes'),
  edges: () => apiFetch('/api/edges'),
  route: (body) => apiFetch('/api/route', { method: 'POST', body: JSON.stringify(body) }),
  congestion: (body) => apiFetch('/api/edges/congestion', { method: 'POST', body: JSON.stringify(body) }),
  reset: () => apiFetch('/api/reset', { method: 'POST' }),
};
