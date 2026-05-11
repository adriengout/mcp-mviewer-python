import asyncio
import json
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from shared import mcp, context

from tools.load_xml import load_xml
from tools.list_themes import list_themes
from tools.list_layers_by_theme import list_layers_by_theme
from tools.list_all_layers import list_all_layers
from tools.get_metadata import get_metadata
from tools.spatial_query import spatial_query
from tools.get_bbox import get_bbox
from tools.bbox_to_mviewer_url import bbox_to_mviewer_url

TOOL_DEFS = [
    {
        "name": "load_xml",
        "description": "Charge une config XML mviewer et indexe ses donnéess/thèmes en mémoire. Point d'entrée obligatoire de toute session.",
        "params": [
            {"name": "url", "type": "string", "required": True, "placeholder": "https://example.com/config.xml"},
        ],
    },
    {
        "name": "list_themes",
        "description": "Liste les thèmes (catégories) disponibles dans la config chargée. À appeler après load_xml.",
        "params": [],
    },
    {
        "name": "list_layers_by_theme",
        "description": "Liste les donnéess d'un thème donné. Voie d'exploration normale après list_themes.",
        "params": [
            {"name": "theme", "type": "string", "required": True, "placeholder": "Nom exact du thème (issu de list_themes)"},
        ],
    },
    {
        "name": "list_all_layers",
        "description": "Liste plate de toutes les donnéess, tous thèmes confondus. Utile pour une recherche transversale.",
        "params": [],
    },
    {
        "name": "get_metadata",
        "description": "Récupère les métadonnées CSW d'une données et résout son URL WFS. Obligatoire avant spatial_query.",
        "params": [
            {"name": "layer_id", "type": "string", "required": True, "placeholder": "id exact de la données"},
        ],
    },
    {
        "name": "spatial_query",
        "description": "Interroge des donnéess WFS sur une emprise rectangulaire. À appeler après get_metadata.",
        "params": [
            {"name": "layers", "type": "json", "required": True, "placeholder": '["layer_id1", "layer_id2"]'},
            {"name": "wfs_urls", "type": "json", "required": True, "placeholder": '["https://…/wfs", "https://…/wfs"]'},
            {"name": "wfs_names", "type": "json", "required": False, "placeholder": '["ns:typename1", "ns:typename2"]'},
            {"name": "bbox", "type": "json", "required": True, "placeholder": "[lon_min, lat_min, lon_max, lat_max]"},
        ],
    },
    {
        "name": "get_bbox",
        "description": "Calcule une bbox carrée centrée sur une commune française via geo.api.gouv.fr.",
        "params": [
            {"name": "commune", "type": "string", "required": True, "placeholder": "Ex: Rennes"},
            {"name": "tampon_km", "type": "number", "required": False, "default": 2.0, "placeholder": "2.0"},
        ],
    },
    {
        "name": "bbox_to_mviewer_url",
        "description": "Génère un lien MViewer permalink depuis une bbox EPSG:4326 et une liste de couches. Convertit automatiquement en EPSG:3857 et calcule le zoom. À appeler en fin de workflow.",
        "params": [
            {"name": "bbox", "type": "json", "required": True, "placeholder": "[lon_min, lat_min, lon_max, lat_max]"},
            {"name": "layers", "type": "json", "required": True, "placeholder": '["layer_id1", "layer_id2"]'},
            {"name": "config", "type": "string", "required": False, "placeholder": "https://geobretagne.fr/apps/viz/config.xml"},
            {"name": "mode", "type": "string", "required": False, "placeholder": "d"},
        ],
    },
]

TOOL_FUNCS = {
    "load_xml": load_xml,
    "list_themes": list_themes,
    "list_layers_by_theme": list_layers_by_theme,
    "list_all_layers": list_all_layers,
    "get_metadata": get_metadata,
    "spatial_query": spatial_query,
    "get_bbox": get_bbox,
    "bbox_to_mviewer_url": bbox_to_mviewer_url,
}

_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MCP mviewer — Playground</title>
  <style>
    :root {
      --bg: #0d1117;
      --surface: #161b22;
      --surface2: #1c2128;
      --border: #30363d;
      --text: #e6edf3;
      --muted: #8b949e;
      --accent: #58a6ff;
      --green: #3fb950;
      --red: #f85149;
      --orange: #d29922;
      --font: 'Consolas', 'Monaco', 'Courier New', monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--text); font-family: var(--font); height: 100vh; display: flex; flex-direction: column; font-size: 13px; }

    /* ── Header ── */
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 10px 18px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-shrink: 0;
    }
    header h1 { font-size: 14px; font-weight: 700; color: var(--accent); letter-spacing: 0.3px; }
    header span.sep { color: var(--border); }
    #ctx-badge {
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 7px;
      font-size: 11px;
      color: var(--muted);
    }
    #ctx-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--red); flex-shrink: 0; transition: background 0.3s; }
    #ctx-dot.on { background: var(--green); }

    /* ── Layout ── */
    .layout { display: flex; flex: 1; overflow: hidden; }

    /* ── Sidebar ── */
    aside {
      width: 230px;
      flex-shrink: 0;
      background: var(--surface);
      border-right: 1px solid var(--border);
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }
    .sidebar-label {
      padding: 8px 14px;
      font-size: 10px;
      letter-spacing: 1px;
      color: var(--muted);
      text-transform: uppercase;
      border-bottom: 1px solid var(--border);
      flex-shrink: 0;
    }
    .tool-item {
      padding: 9px 14px;
      cursor: pointer;
      border-bottom: 1px solid var(--border);
      border-left: 3px solid transparent;
      transition: background 0.1s;
    }
    .tool-item:hover { background: var(--surface2); }
    .tool-item.active { background: var(--surface2); border-left-color: var(--accent); }
    .tool-name { color: var(--accent); font-weight: 600; font-size: 12px; }
    .tool-hint { color: var(--muted); font-size: 10px; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    /* ── Main ── */
    main { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 20px; }

    /* Welcome screen */
    .welcome { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; color: var(--muted); text-align: center; }
    .welcome h2 { color: var(--text); font-size: 17px; margin-bottom: 4px; }
    .workflow-steps { margin-top: 16px; text-align: left; display: flex; flex-direction: column; gap: 4px; }
    .wf-step { display: flex; align-items: center; gap: 8px; font-size: 11px; }
    .wf-num { background: var(--border); color: var(--muted); width: 17px; height: 17px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; flex-shrink: 0; }
    .wf-name { color: var(--accent); }
    .wf-desc { color: var(--muted); }

    /* Tool header */
    .tool-header h2 { font-size: 16px; color: var(--accent); }
    .tool-desc { margin-top: 6px; font-size: 11px; color: var(--muted); line-height: 1.6; }

    /* Form */
    .param-group { display: flex; flex-direction: column; gap: 4px; }
    label.param-label { font-size: 11px; color: var(--muted); display: flex; align-items: center; gap: 5px; }
    .badge { font-size: 9px; padding: 1px 5px; border-radius: 3px; }
    .badge.req { background: rgba(248,81,73,.15); color: var(--red); }
    .badge.opt { background: rgba(210,153,34,.12); color: var(--orange); }
    input[type=text], input[type=number], textarea {
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text);
      font-family: var(--font);
      font-size: 12px;
      padding: 7px 10px;
      border-radius: 5px;
      outline: none;
      transition: border-color 0.15s;
      width: 100%;
    }
    input:focus, textarea:focus { border-color: var(--accent); }
    textarea { min-height: 56px; resize: vertical; }

    /* Actions bar */
    .actions { display: flex; align-items: center; gap: 10px; }
    .run-btn {
      background: var(--accent);
      color: #0d1117;
      border: none;
      padding: 7px 18px;
      font-family: var(--font);
      font-size: 12px;
      font-weight: 700;
      border-radius: 5px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .run-btn:hover { opacity: 0.88; }
    .run-btn:disabled { opacity: 0.45; cursor: not-allowed; }
    .elapsed { font-size: 10px; color: var(--muted); }

    /* Result */
    .result-box { border: 1px solid var(--border); border-radius: 5px; overflow: hidden; }
    .result-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 5px 12px;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      font-size: 10px;
      color: var(--muted);
      letter-spacing: 0.5px;
    }
    .result-bar .status { font-weight: 700; }
    .status.ok { color: var(--green); }
    .status.err { color: var(--red); }
    .copy-btn {
      background: none;
      border: 1px solid var(--border);
      color: var(--muted);
      font-family: var(--font);
      font-size: 10px;
      padding: 2px 7px;
      border-radius: 3px;
      cursor: pointer;
    }
    .copy-btn:hover { color: var(--text); border-color: var(--text); }
    .result-content {
      padding: 14px;
      font-size: 11px;
      white-space: pre-wrap;
      overflow-x: auto;
      max-height: 420px;
      overflow-y: auto;
      line-height: 1.5;
    }
    .result-ok { color: var(--green); }
    .result-err { color: var(--red); }

    /* No-param notice */
    .no-params { font-size: 11px; color: var(--muted); font-style: italic; }
  </style>
</head>
<body>

<header>
  <h1>MCP mviewer</h1>
  <span class="sep">·</span>
  <span style="font-size:12px;color:var(--muted);">Playground</span>
  <div id="ctx-badge">
    <div id="ctx-dot"></div>
    <span id="ctx-text">Aucun contexte chargé</span>
  </div>
</header>

<div class="layout">
  <aside>
    <div class="sidebar-label">Outils</div>
    <div id="tool-list"></div>
  </aside>
  <main id="main">
    <div class="welcome">
      <h2>Playground MCP mviewer</h2>
      <p>Sélectionnez un outil dans la barre latérale.</p>
      <div class="workflow-steps">
        <div class="wf-step"><span class="wf-num">1</span><span class="wf-name">load_xml</span><span class="wf-desc">— charger la config</span></div>
        <div class="wf-step"><span class="wf-num">2</span><span class="wf-name">list_themes</span><span class="wf-desc">— explorer les thèmes</span></div>
        <div class="wf-step"><span class="wf-num">3</span><span class="wf-name">list_layers_by_theme</span><span class="wf-desc">— lister les couches</span></div>
        <div class="wf-step"><span class="wf-num">4</span><span class="wf-name">get_metadata</span><span class="wf-desc">— résoudre l'URL WFS</span></div>
        <div class="wf-step"><span class="wf-num">5</span><span class="wf-name">spatial_query</span><span class="wf-desc">— interroger les données</span></div>
        <div class="wf-step"><span class="wf-num">6</span><span class="wf-name">bbox_to_mviewer_url</span><span class="wf-desc">— générer le lien</span></div>
      </div>
    </div>
  </main>
</div>

<script>
const TOOLS = %TOOLS_JSON%;

let activeToolName = null;

// ── Sidebar ──────────────────────────────────────────────────────────────────
function renderSidebar() {
  const list = document.getElementById('tool-list');
  list.innerHTML = '';
  TOOLS.forEach(t => {
    const el = document.createElement('div');
    el.className = 'tool-item';
    el.dataset.name = t.name;
    const hint = t.description.split('.')[0].substring(0, 55);
    el.innerHTML = `<div class="tool-name">${t.name}</div><div class="tool-hint">${hint}</div>`;
    el.addEventListener('click', () => selectTool(t.name));
    list.appendChild(el);
  });
}

function selectTool(name) {
  activeToolName = name;
  document.querySelectorAll('.tool-item').forEach(el => {
    el.classList.toggle('active', el.dataset.name === name);
  });
  const tool = TOOLS.find(t => t.name === name);
  renderToolPanel(tool);
}

// ── Tool panel ───────────────────────────────────────────────────────────────
function renderToolPanel(tool) {
  const main = document.getElementById('main');

  const paramsHtml = tool.params.length === 0
    ? '<p class="no-params">Aucun paramètre requis.</p>'
    : tool.params.map(p => {
        const badge = p.required
          ? '<span class="badge req">requis</span>'
          : '<span class="badge opt">optionnel</span>';

        let input;
        if (p.type === 'json') {
          input = `<textarea id="p-${p.name}" placeholder='${esc(p.placeholder || "")}'></textarea>`;
        } else if (p.type === 'number') {
          const dv = p.default !== undefined ? p.default : '';
          input = `<input type="number" step="any" id="p-${p.name}" value="${dv}" placeholder="${esc(p.placeholder || '')}">`;
        } else {
          input = `<input type="text" id="p-${p.name}" placeholder="${esc(p.placeholder || '')}">`;
        }

        return `<div class="param-group">
          <label class="param-label" for="p-${p.name}">${p.name} ${badge}</label>
          ${input}
        </div>`;
      }).join('');

  main.innerHTML = `
    <div class="tool-header">
      <h2>${tool.name}</h2>
      <p class="tool-desc">${tool.description}</p>
    </div>
    <form id="tool-form" style="display:flex;flex-direction:column;gap:14px;">
      ${paramsHtml}
      <div class="actions">
        <button type="submit" class="run-btn">&#9654; Exécuter</button>
        <span class="elapsed" id="elapsed"></span>
      </div>
    </form>
    <div id="result-area"></div>
  `;

  document.getElementById('tool-form').addEventListener('submit', e => { e.preventDefault(); runTool(tool); });
}

// ── Execution ────────────────────────────────────────────────────────────────
async function runTool(tool) {
  const btn = document.querySelector('.run-btn');
  const elapsed = document.getElementById('elapsed');
  btn.disabled = true;
  btn.innerHTML = '&#8987; En cours…';
  elapsed.textContent = '';
  const t0 = Date.now();

  const params = {};
  let parseErr = null;

  for (const p of tool.params) {
    const el = document.getElementById(`p-${p.name}`);
    if (!el) continue;
    const val = el.value.trim();

    if (p.type === 'json') {
      if (!val && !p.required) continue;
      try { params[p.name] = JSON.parse(val); }
      catch (e) { parseErr = `"${p.name}" : JSON invalide — ${e.message}`; break; }
    } else if (p.type === 'number') {
      if (val === '' && !p.required) continue;
      if (val !== '') params[p.name] = parseFloat(val);
    } else {
      if (!val && !p.required) continue;
      if (val) params[p.name] = val;
    }
  }

  if (parseErr) {
    showResult({ error: parseErr }, false, 0);
    btn.disabled = false;
    btn.innerHTML = '&#9654; Exécuter';
    return;
  }

  try {
    const res = await fetch(`/mcp/mviewer/playground/api/tool/${tool.name}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    const data = await res.json();
    const ms = Date.now() - t0;
    showResult(data, res.ok && !data.error, ms);
    refreshCtx();
  } catch (e) {
    showResult({ error: `Erreur réseau : ${e.message}` }, false, Date.now() - t0);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '&#9654; Exécuter';
  }
}

function showResult(data, ok, ms) {
  const area = document.getElementById('result-area');
  const content = data.result !== undefined ? data.result : data;
  const text = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
  const elapsedLabel = ms > 0 ? `${ms} ms` : '';
  const statusClass = ok ? 'ok' : 'err';
  const statusLabel = ok ? '✓ OK' : '✗ Erreur';

  area.innerHTML = `
    <div class="result-box">
      <div class="result-bar">
        <span>RÉSULTAT <span class="status ${statusClass}">${statusLabel}</span></span>
        <span style="display:flex;align-items:center;gap:8px;">
          <span style="color:var(--muted)">${elapsedLabel}</span>
          <button class="copy-btn" onclick="copyResult()">copier</button>
        </span>
      </div>
      <pre class="result-content ${ok ? 'result-ok' : 'result-err'}" id="result-pre">${escHtml(text)}</pre>
    </div>
  `;

  const elapsed = document.getElementById('elapsed');
  if (elapsed) elapsed.textContent = elapsedLabel;
}

function copyResult() {
  const pre = document.getElementById('result-pre');
  if (!pre) return;
  navigator.clipboard.writeText(pre.textContent).catch(() => {});
}

// ── Context status ───────────────────────────────────────────────────────────
async function refreshCtx() {
  try {
    const res = await fetch('/mcp/mviewer/playground/api/context');
    const d = await res.json();
    const dot = document.getElementById('ctx-dot');
    const txt = document.getElementById('ctx-text');
    if (d.loaded) {
      dot.className = 'on';
      txt.textContent = `${d.title || 'Contexte chargé'} · ${d.layers_count} donnéess · ${d.themes.length} thèmes`;
    } else {
      dot.className = '';
      txt.textContent = 'Aucun contexte chargé';
    }
  } catch (_) {}
}

// ── Utils ────────────────────────────────────────────────────────────────────
function escHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function esc(s) { return s.replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }

// ── Init ─────────────────────────────────────────────────────────────────────
renderSidebar();
refreshCtx();
setInterval(refreshCtx, 6000);
</script>
</body>
</html>
"""


@mcp.custom_route("/mcp/mviewer/playground", methods=["GET"])
async def playground_page(request: Request) -> HTMLResponse:
    html = _HTML.replace("%TOOLS_JSON%", json.dumps(TOOL_DEFS, ensure_ascii=False))
    return HTMLResponse(html)


@mcp.custom_route("/mcp/mviewer/playground/api/tools", methods=["GET"])
async def api_tools(request: Request) -> JSONResponse:
    return JSONResponse(TOOL_DEFS)


@mcp.custom_route("/mcp/mviewer/playground/api/context", methods=["GET"])
async def api_context(request: Request) -> JSONResponse:
    return JSONResponse({
        "loaded": bool(context["layers"]),
        "title": context["title"],
        "layers_count": len(context["layers"]),
        "themes": context["themes"],
    })


@mcp.custom_route("/mcp/mviewer/playground/api/tool/{tool_name}", methods=["POST"])
async def api_run_tool(request: Request) -> JSONResponse:
    tool_name = request.path_params["tool_name"]
    func = TOOL_FUNCS.get(tool_name)
    if func is None:
        return JSONResponse({"error": f"Outil inconnu : {tool_name}"}, status_code=404)

    try:
        body = await request.json()
    except Exception:
        body = {}

    try:
        result = await asyncio.to_thread(func, **body)
        return JSONResponse({"result": result})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)