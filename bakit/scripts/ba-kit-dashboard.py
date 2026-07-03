#!/usr/bin/env python3
"""BA-kit Localhost User Dashboard — token usage viewer.
Usage: python3 ba-kit-dashboard.py [--port PORT]
"""
import webbrowser
import json
import os
import time
import sys
import collections
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PROJECTS_DIR = Path.home() / ".claude" / "projects"
CACHE_FILE = Path.home() / ".claude" / "ba-kit" / ".dashboard-cache.json"
CACHE_TTL = 30  # seconds in-memory, file cache checked by mtime
_cache = {"data": None, "ts": 0}
_file_tracker = {}  # {path: (mtime, [sessions])} — per-file parse cache

# ── Data Layer ───────────────────────────────────────────────────────

MODEL_PRICES = {
    "claude-opus-4-6": (15, 75),      # input/output per 1M tokens
    "claude-sonnet-4-6": (3, 15),
    "claude-haiku-4-5": (0.80, 4),
    "claude-3.5-sonnet": (3, 15),
    "claude-3.5-haiku": (0.80, 4),
    "deepseek-v4-pro": (0.20, 0.60),
    "default": (1.50, 7.50),
}

def parse_jsonl():
    sessions = []
    if not PROJECTS_DIR.is_dir():
        return sessions

    current_files = set()
    for jsonl_path in PROJECTS_DIR.rglob("*.jsonl"):
        current_files.add(str(jsonl_path))
        try:
            mtime = jsonl_path.stat().st_mtime
        except OSError:
            continue

        # Use cached parse if file hasn't changed
        cached = _file_tracker.get(str(jsonl_path))
        if cached and cached[0] == mtime:
            sessions.extend(cached[1])
            continue

        # Parse file
        file_sessions = []
        project = jsonl_path.parent.name if jsonl_path.parent != PROJECTS_DIR else "default"
        try:
            with open(jsonl_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if not isinstance(entry, dict):
                        continue

                    if entry.get("type") == "assistant" and isinstance(entry.get("message"), dict):
                        usage = entry["message"].get("usage", {}) or {}
                        model = entry["message"].get("model", "unknown")
                        session_id = entry["message"].get("id", entry.get("sessionId", ""))
                    else:
                        usage = entry.get("usage", {}) or {}
                        model = entry.get("model", "unknown")
                        session_id = entry.get("id", entry.get("session_id", ""))

                    input_tokens = usage.get("input_tokens", 0) or 0
                    output_tokens = usage.get("output_tokens", 0) or 0
                    total_tokens = input_tokens + output_tokens

                    if total_tokens == 0:
                        continue

                    file_sessions.append({
                        "id": session_id,
                        "project": project,
                        "date": entry.get("date", entry.get("timestamp", ""))[:10],
                        "model": model,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                        "timestamp": entry.get("timestamp", entry.get("date", "")),
                        "cache_read": usage.get("cache_read_input_tokens", 0) or 0,
                        "cache_create": usage.get("cache_creation_input_tokens", 0) or 0,
                    })
        except (IOError, OSError):
            continue

        _file_tracker[str(jsonl_path)] = (mtime, file_sessions)
        sessions.extend(file_sessions)

    # Prune deleted files from tracker
    for stale in list(_file_tracker.keys()):
        if stale not in current_files:
            del _file_tracker[stale]

    sessions.sort(key=lambda s: s["timestamp"], reverse=True)
    return sessions


# ponytail: global tool counter, recomputed with sessions
_tools_cache = {"data": None, "ts": 0}

def parse_tools():
    """Count tool usage across all JSONL files. Cached by mtime like sessions."""
    now = time.time()
    if _tools_cache["data"] is not None and (now - _tools_cache["ts"]) < CACHE_TTL:
        return _tools_cache["data"]

    tools = collections.Counter()
    if not PROJECTS_DIR.is_dir():
        _tools_cache["data"] = tools
        _tools_cache["ts"] = now
        return tools

    for jsonl_path in PROJECTS_DIR.rglob("*.jsonl"):
        try:
            with open(jsonl_path) as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if d.get("type") != "assistant": continue
                    msg = d.get("message", {})
                    if not isinstance(msg, dict): continue
                    content = msg.get("content", [])
                    if not isinstance(content, list): continue
                    for c in content:
                        if not isinstance(c, dict) or c.get("type") != "tool_use": continue
                        name = c.get("name", "?")
                        inp = c.get("input", {}) or {}
                        if name == "Task":
                            tools[f"subagent:{inp.get('subagent_type','?')}"] += 1
                        elif name == "Skill":
                            tools[f"skill:{inp.get('skill','?')}"] += 1
                        elif name.startswith("mcp__"):
                            tools[f"mcp:{name[5:]}"] += 1
                        else:
                            tools[f"tool:{name}"] += 1
        except (IOError, OSError):
            continue

    _tools_cache["data"] = tools
    _tools_cache["ts"] = now
    return tools


def get_data():
    now = time.time()
    if _cache["data"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["data"]

    sessions = parse_jsonl()

    # Aggregate by date
    by_date = {}
    # Aggregate by project
    by_project = {}
    # Aggregate by model
    by_model = {}
    # Total
    total_tokens = 0
    total_input = 0
    total_output = 0

    for s in sessions:
        d = s["date"]
        p = s["project"]
        m = s["model"]

        by_date[d] = by_date.get(d, 0) + s["total_tokens"]
        by_project[p] = by_project.get(p, 0) + s["total_tokens"]
        by_model[m] = by_model.get(m, 0) + s["total_tokens"]
        total_tokens += s["total_tokens"]
        total_input += s["input_tokens"]
        total_output += s["output_tokens"]

    today = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    tokens_today = by_date.get(today, 0)

    # Cache token stats
    total_cache_read = sum(s.get("cache_read", 0) for s in sessions)
    total_cache_create = sum(s.get("cache_create", 0) for s in sessions)
    total_processed = total_input + total_cache_read + total_cache_create
    cache_savings_pct = round(100 * (total_cache_read + total_cache_create) / max(1, total_processed), 1)

    # Calculate cost (billed tokens = input_tokens, not cache hits)
    cost = 0.0
    for s in sessions:
        prices = MODEL_PRICES.get(s["model"], MODEL_PRICES["default"])
        cost += (s["input_tokens"] / 1_000_000) * prices[0]
        cost += (s["output_tokens"] / 1_000_000) * prices[1]

    # Top projects
    top_projects = sorted(by_project.items(), key=lambda x: x[1], reverse=True)[:10]

    # Top models
    top_models = sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:10]

    # Recent sessions
    recent = sessions[:50]

    data = {
        "total_tokens": total_tokens,
        "total_input": total_input,
        "total_output": total_output,
        "tokens_today": tokens_today,
        "session_count": len(sessions),
        "project_count": len(by_project),
        "cost_estimate": round(cost, 2),
        "by_date": dict(sorted(by_date.items())[-30:]),
        "top_projects": top_projects,
        "top_models": top_models,
        "recent": recent,
        "_all": sessions,
        "cache_read": total_cache_read,
        "cache_create": total_cache_create,
        "cache_pct": cache_savings_pct,
        "top_tools": parse_tools().most_common(15),
    }

    _cache["data"] = data
    _cache["ts"] = now
    return data


# ── API Endpoints ────────────────────────────────────────────────────

def api_stats(params):
    data = get_data()
    days = int(params.get("days", [0])[0]) or 0

    # Filter from full session list for accuracy
    all_sessions = data["_all"]
    filtered_sessions = all_sessions
    if days > 0:
        cutoff = time.strftime("%Y-%m-%d", time.localtime(time.time() - days * 86400))
        filtered_sessions = [s for s in all_sessions if s["date"] >= cutoff]

    # Recompute stats for filtered view
    by_date_f = {}
    by_project_f = {}
    by_model_f = {}
    total_f = 0
    input_f = 0
    output_f = 0
    cache_read_f = 0
    cost_f = 0.0
    for s in filtered_sessions:
        by_date_f[s["date"]] = by_date_f.get(s["date"], 0) + s["total_tokens"]
        by_project_f[s["project"]] = by_project_f.get(s["project"], 0) + s["total_tokens"]
        by_model_f[s["model"]] = by_model_f.get(s["model"], 0) + s["total_tokens"]
        total_f += s["total_tokens"]
        input_f += s["input_tokens"]
        output_f += s["output_tokens"]
        cache_read_f += s.get("cache_read", 0)
        prices = MODEL_PRICES.get(s["model"], MODEL_PRICES["default"])
        cost_f += (s["input_tokens"] / 1_000_000) * prices[0]
        cost_f += (s["output_tokens"] / 1_000_000) * prices[1]

    total_processed_f = input_f + cache_read_f + (sum(s.get("cache_create", 0) for s in filtered_sessions))
    cache_savings_pct_f = round(100 * cache_read_f / max(1, total_processed_f), 1)

    top_projects_f = sorted(by_project_f.items(), key=lambda x: x[1], reverse=True)[:10]
    top_models_f = sorted(by_model_f.items(), key=lambda x: x[1], reverse=True)[:10]
    today = time.strftime("%Y-%m-%d", time.localtime(time.time()))

    return json.dumps({
        "total_tokens": total_f if days > 0 else data["total_tokens"],
        "total_input": input_f if days > 0 else data["total_input"],
        "total_output": output_f if days > 0 else data["total_output"],
        "tokens_today": by_date_f.get(today, 0) if days > 0 else data["tokens_today"],
        "session_count": len(filtered_sessions) if days > 0 else data["session_count"],
        "cost_estimate": round(cost_f, 2) if days > 0 else data["cost_estimate"],
        "by_date": dict(sorted(by_date_f.items())[-30:]) if days > 0 else data["by_date"],
        "top_projects": top_projects_f if days > 0 else data["top_projects"],
        "top_models": top_models_f if days > 0 else data["top_models"],
        "recent": (filtered_sessions if days > 0 else data["recent"])[:50],
        "days": days,
        "all_total_tokens": data["total_tokens"],
        "all_cost_estimate": data["cost_estimate"],
        "cache_read": cache_read_f if days > 0 else data["cache_read"],
        "cache_pct": cache_savings_pct_f if days > 0 else data["cache_pct"],
        "top_tools": [[t, c] for t, c in (parse_tools().most_common(15))],
    })


def api_projects():
    data = get_data()
    return json.dumps([{"name": p[0], "tokens": p[1]} for p in data["top_projects"]])


def api_sessions(params):
    data = get_data()
    project = params.get("project", [None])[0]
    days = int(params.get("days", [0])[0]) or 0
    sessions = data["_all"]
    if days > 0:
        cutoff = time.strftime("%Y-%m-%d", time.localtime(time.time() - days * 86400))
        sessions = [s for s in sessions if s["date"] >= cutoff]
    if project:
        sessions = [s for s in sessions if s["project"] == project]
        return json.dumps(sessions)  # all sessions for project detail
    return json.dumps(sessions[:50])


def api_session_detail(session_id):
    data = get_data()
    for s in data["_all"]:
        if s["id"] == session_id:
            return json.dumps(s)
    return json.dumps({"error": "not_found"})


# ── HTML Dashboard ───────────────────────────────────────────────────

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BA-kit — Token Usage</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0d1117;color:#c9d1d9;padding:24px;min-height:100vh}
h1{font-size:22px;color:#58a6ff;margin-bottom:4px}
header p{color:#8b949e;font-size:13px;margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:16px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;cursor:default}
.card h3{font-size:11px;color:#8b949e;text-transform:uppercase;margin-bottom:8px}
.card .val{font-size:28px;font-weight:600;color:#58a6ff}
.card .sub{font-size:12px;color:#8b949e}
.filters{display:flex;gap:8px;margin-bottom:16px}
.filters button{background:#21262d;border:1px solid #30363d;color:#c9d1d9;padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.filters button.active{background:#1f6feb;border-color:#1f6feb;color:#fff}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:16px;margin-bottom:16px}
.chart-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}
.chart-card h3{font-size:13px;color:#8b949e;margin-bottom:12px}
canvas{width:100%!important;max-height:200px}
table{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:12px}
th,td{text-align:left;padding:6px 10px;border-bottom:1px solid #21262d}
th{color:#8b949e}
tr:hover{background:#1c2128}
tr.clickable{cursor:pointer}
tr.clickable:hover{background:#1a3a5c}
.refresh{color:#8b949e;font-size:11px;margin-top:12px}
.back-btn{background:transparent;color:#58a6ff;border:none;cursor:pointer;font-size:14px;margin-bottom:16px}
.hidden{display:none}
@media(max-width:768px){.charts{grid-template-columns:1fr}.grid{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<header>
  <h1>BA-kit Token Usage</h1>
  <p>Dữ liệu từ các phiên làm việc của bạn</p>
</header>

<div class="filters" id="filters">
  <button data-days="7">7 ngày</button>
  <button data-days="30" class="active">30 ngày</button>
  <button data-days="90">90 ngày</button>
  <button data-days="0">Tất cả</button>
</div>

<div id="main-view">
  <div class="grid" id="summary">
    <div class="card"><h3>Tổng token</h3><div class="val" id="total-tokens">-</div><div class="sub" id="all-total"></div></div>
    <div class="card"><h3>Hôm nay</h3><div class="val" id="tokens-today">-</div></div>
    <div class="card"><h3>Cache savings</h3><div class="val" id="cache-pct">-</div><div class="sub" id="cache-detail"></div></div>
    <div class="card"><h3>Chi phí ước tính</h3><div class="val" id="cost">-</div><div class="sub" id="all-cost"></div></div>
    <div class="card"><h3>Phiên làm việc</h3><div class="val" id="sessions">-</div></div>
  </div>

  <div class="charts">
    <div class="chart-card"><h3>Token theo ngày</h3><canvas id="daily-chart"></canvas></div>
    <div class="chart-card"><h3>Top dự án</h3><canvas id="project-chart"></canvas></div>
    <div class="chart-card"><h3>Top kỹ năng / model</h3><canvas id="model-chart"></canvas></div>
    <div class="chart-card"><h3>Top công cụ</h3><canvas id="tools-chart"></canvas></div>
  </div>

  <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px">
    <h3 style="margin:0">Danh sách dự án</h3>
    <input type="text" id="search-input" placeholder="Lọc dự án..." style="background:#161b22;border:1px solid #30363d;color:#c9d1d9;padding:4px 10px;border-radius:6px;font-size:12px;width:200px" oninput="filterProjects()">
  </div>
  <table><thead><tr><th>Dự án</th><th>Phiên</th><th>Input</th><th>Output</th><th>Cache Read</th><th>Tổng token</th></tr></thead>
  <tbody id="projects-table"></tbody></table>
  <p class="refresh">Tự động cập nhật mỗi 30 giây. Click vào dự án để xem chi tiết.</p>
</div>

<div id="session-view" class="hidden">
  <button class="back-btn" onclick="showMainView()">← Quay lại dashboard</button>
  <h2 id="session-title" style="color:#58a6ff;margin-bottom:16px"></h2>
  <div class="grid" id="session-summary"></div>
  <h3 style="margin-bottom:12px">Chi tiết từng lượt</h3>
  <table><thead><tr><th>Thời gian</th><th>Model</th><th>Input</th><th>Cache Read</th><th>Output</th><th>Tổng</th></tr></thead><tbody id="session-turns"></tbody></table>
</div>

<div id="project-view" class="hidden">
  <button class="back-btn" onclick="showMainView()">← Quay lại dashboard</button>
  <h2 id="project-title" style="color:#58a6ff;margin-bottom:16px"></h2>
  <div class="grid" id="project-summary"></div>
  <table><thead><tr><th>Phiên</th><th>Thời gian</th><th>Model</th><th>Input</th><th>Output</th><th>Cache</th><th>Lượt</th></tr></thead>
  <tbody id="project-sessions"></tbody></table>
</div>

<script>
let currentDays = 30;

function shortProject(name) {
  // Claude Code stores paths as: -Users-username-Projects-projectname
  const m = name.match(/-Projects-(.+)/);
  if (m) return m[1];
  // Also handle subagent paths: -Users-...-project/-subagent
  const m2 = name.match(/Projects-(.+)/);
  return m2 ? m2[1] : (name.length > 50 ? '…' + name.slice(-48) : name);
}
function toLocal(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  return isNaN(d.getTime()) ? ts.replace('T',' ').slice(0,16) : d.toLocaleString('sv-SE').replace('T',' ').slice(0,16);
}

document.getElementById('filters').addEventListener('click', e => {
  if (e.target.tagName !== 'BUTTON') return;
  document.querySelectorAll('#filters button').forEach(b => b.classList.remove('active'));
  e.target.classList.add('active');
  currentDays = parseInt(e.target.dataset.days) || 0;
  load();
});

async function load() {
  try {
    const daysParam = currentDays > 0 ? '?days=' + currentDays : '';
    const r = await fetch('/api/stats' + daysParam);
    const d = await r.json();

    document.getElementById('total-tokens').textContent = d.total_tokens.toLocaleString();
    document.getElementById('tokens-today').textContent = d.tokens_today.toLocaleString();
    document.getElementById('cost').textContent = '$' + d.cost_estimate;
    document.getElementById('sessions').textContent = d.session_count;

    // Cache stats
    const cachePct = d.cache_pct || 0;
    document.getElementById('cache-pct').textContent = cachePct + '%';
    document.getElementById('cache-detail').textContent = (d.cache_read||0).toLocaleString() + ' cache read';

    // Show all-time comparison when filtering
    const allTotalEl = document.getElementById('all-total');
    const allCostEl = document.getElementById('all-cost');
    if (d.days > 0 && d.all_total_tokens > d.total_tokens) {
      allTotalEl.textContent = 'tổng: ' + d.all_total_tokens.toLocaleString();
      allCostEl.textContent = 'tổng: $' + d.all_cost_estimate;
    } else {
      allTotalEl.textContent = '';
      allCostEl.textContent = '';
    }

    drawDaily(d.by_date);
    drawBars('project-chart', d.top_projects.map(p => [shortProject(p[0]), p[1]]));
    drawBars('model-chart', d.top_models || []);
    drawBars('tools-chart', d.top_tools || []);
    _projectsData = d.top_projects || [];
    renderProjects(_projectsData);
  } catch(e) { console.error(e); }
}

let _projectsData = [];

function renderProjects(projects) {
  const tbody = document.getElementById('projects-table');
  tbody.innerHTML = '';
  if (!projects.length) { tbody.innerHTML = '<tr><td colspan="6" style="color:#8b949e">Chưa có dữ liệu</td></tr>'; return; }
  projects.forEach(p => {
    const pname = p[0]; const ptokens = p[1];
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = function() { showProject(pname); };
    tr.innerHTML =
      '<td><a href="#" onclick="event.stopPropagation();showProject(\''+pname.replace(/'/g,"\\'")+'\');return false" style="color:#58a6ff">'+shortProject(pname).replace(/</g,'&lt;')+'</a></td>'+
      '<td>-</td><td>-</td><td>-</td><td>-</td><td>'+ptokens.toLocaleString()+'</td>';
    tbody.appendChild(tr);
  });
}

function filterProjects() {
  const q = (document.getElementById('search-input').value || '').toLowerCase();
  if (!q) { renderProjects(_projectsData); return; }
  const filtered = _projectsData.filter(p => p[0].toLowerCase().includes(q));
  renderProjects(filtered);
}

function drawDaily(data) {
  const canvas = document.getElementById('daily-chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const entries = Object.entries(data);
  if (!entries.length) { ctx.fillStyle='#8b949e'; ctx.fillText('Chưa có dữ liệu',10,20); return; }
  const w = canvas.parentElement.clientWidth - 32;
  const h = 200; canvas.width=w*2; canvas.height=h*2;
  canvas.style.width=w+'px'; canvas.style.height=h+'px';
  ctx.scale(2,2);
  const maxV = Math.max(...entries.map(e=>e[1]), 1);
  const pw=w-50, ph=h-30;
  ctx.strokeStyle='#30363d'; ctx.lineWidth=0.5;
  for(let i=0;i<=4;i++){const y=10+ph/4*i;ctx.beginPath();ctx.moveTo(50,y);ctx.lineTo(w-10,y);ctx.stroke()}
  ctx.strokeStyle='#58a6ff';ctx.lineWidth=2;ctx.beginPath();
  entries.forEach((e,i)=>{const x=50+pw/(entries.length-1||1)*i;const y=10+ph-e[1]/maxV*ph;i===0?ctx.moveTo(x,y):ctx.lineTo(x,y)});
  ctx.stroke();
  ctx.fillStyle='#8b949e';ctx.font='9px sans-serif';
  ctx.fillText(maxV.toLocaleString(),5,14);
  if(entries.length>0){ctx.fillText(entries[0][0],50,h-2);ctx.fillText(entries[entries.length-1][0].slice(5),w-55,h-2)}
}

function drawBars(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!data.length) { ctx.fillStyle='#8b949e'; ctx.fillText('Chưa có dữ liệu',10,20); return; }
  const w = canvas.parentElement.clientWidth - 32;
  const n = Math.min(data.length, 8);
  const barH = 16; const gap = 8;
  const labelW = 130; // reserved left column for labels
  const h = n * (barH + gap) + 10;
  canvas.width = w*2; canvas.height = h*2;
  canvas.style.width = w+'px'; canvas.style.height = h+'px';
  ctx.scale(2,2);
  const maxV = Math.max(...data.map(d=>d[1]), 1);
  const colors=['#58a6ff','#3fb950','#d29922','#f85149','#bc8cff','#79c0ff','#ffa657','#7ee787'];
  data.slice(0,n).forEach((d,i)=>{
    const y = 5 + i*(barH+gap);
    const barW = Math.max(2, d[1]/maxV*(w - labelW - 70));
    ctx.fillStyle = colors[i%colors.length];
    ctx.fillRect(labelW, y, barW, barH);
    // Label in left column (right-aligned)
    ctx.fillStyle = '#8b949e'; ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    const label = (d[0]||'').length > 20 ? (d[0]||'').slice(0,18)+'..' : (d[0]||'');
    ctx.fillText(label, labelW - 6, y + barH - 4);
    // Value to right of bar
    ctx.textAlign = 'left';
    ctx.fillStyle = '#c9d1d9'; ctx.font = '10px sans-serif';
    ctx.fillText(d[1].toLocaleString(), labelW + barW + 6, y + barH - 4);
  });
  ctx.textAlign = 'left'; // reset
}

async function showProject(projectName) {
  document.getElementById('main-view').classList.add('hidden');
  document.getElementById('project-view').classList.remove('hidden');
  document.getElementById('session-view').classList.add('hidden');
  document.getElementById('project-title').textContent = 'Dự án: ' + projectName;

  // Fetch sessions for this project from API
  const r = await fetch('/api/sessions?project=' + encodeURIComponent(projectName));
  const sessions = await r.json();

  // Group by session ID for summary row per session
  const byId = {};
  sessions.forEach(s => { const key = s.id || '_'; if (!byId[key]) byId[key] = []; byId[key].push(s); });

  let totalT = 0, totalIn = 0, totalOut = 0, totalCache = 0;
  Object.values(byId).forEach(turns => {
    turns.forEach(t => {
      totalT += t.total_tokens; totalIn += t.input_tokens; totalOut += t.output_tokens; totalCache += (t.cache_read||0);
    });
  });

  document.getElementById('project-summary').innerHTML =
    '<div class="card"><h3>Tổng token</h3><div class="val">' + totalT.toLocaleString() + '</div></div>' +
    '<div class="card"><h3>Phiên</h3><div class="val">' + Object.keys(byId).length + '</div></div>' +
    '<div class="card"><h3>Input</h3><div class="val">' + totalIn.toLocaleString() + '</div></div>' +
    '<div class="card"><h3>Output</h3><div class="val">' + totalOut.toLocaleString() + '</div></div>' +
    '<div class="card"><h3>Cache Read</h3><div class="val">' + totalCache.toLocaleString() + '</div></div>';

  const tbody = document.getElementById('project-sessions');
  tbody.innerHTML = '';
  // Sort sessions by most recent turn timestamp
  const sortedIds = Object.entries(byId).sort((a,b) => {
    const at = Math.max(...a[1].map(t => t.timestamp||''));
    const bt = Math.max(...b[1].map(t => t.timestamp||''));
    return bt < at ? -1 : 1;
  });

  sortedIds.forEach(([sid, turns]) => {
    const inSum = turns.reduce((a,t) => a + t.input_tokens, 0);
    const outSum = turns.reduce((a,t) => a + t.output_tokens, 0);
    const cacheSum = turns.reduce((a,t) => a + (t.cache_read||0), 0);
    const lastTs = turns.map(t => t.timestamp).sort().pop() || '';
    const ts = toLocal(lastTs);
    const model = turns[0].model || '?';
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = function() { showSession(sid, turns); };
    tr.innerHTML = '<td style="max-width:120px;overflow:hidden;text-overflow:ellipsis">'+sid.slice(0,16)+'</td><td>'+ts+'</td><td>'+model+'</td><td>'+inSum.toLocaleString()+'</td><td>'+outSum.toLocaleString()+'</td><td>'+cacheSum.toLocaleString()+'</td><td>'+turns.length+'</td>';
    tbody.appendChild(tr);
  });
}

function showMainView() {
  document.getElementById('main-view').classList.remove('hidden');
  document.getElementById('project-view').classList.add('hidden');
  document.getElementById('session-view').classList.add('hidden');
}

async function showSession(sid, turns) {
  if (!sid) return;
  document.getElementById('main-view').classList.add('hidden');
  document.getElementById('project-view').classList.add('hidden');
  document.getElementById('session-view').classList.remove('hidden');
  document.getElementById('session-title').textContent = 'Session: ' + sid.slice(0,16) + '...';

  if (!turns || !turns.length) {
    document.getElementById('session-summary').innerHTML = '<div class="card"><h3>Không tìm thấy</h3></div>';
    return;
  }

  turns.sort((a,b) => (a.timestamp||'') < (b.timestamp||'') ? -1 : 1);
  const totalIn = turns.reduce((a,s)=>a+s.input_tokens,0);
  const totalOut = turns.reduce((a,s)=>a+s.output_tokens,0);
  const totalCache = turns.reduce((a,s)=>a+(s.cache_read||0),0);
  document.getElementById('session-summary').innerHTML =
    '<div class="card"><h3>Tổng input</h3><div class="val">'+totalIn.toLocaleString()+'</div></div>'+
    '<div class="card"><h3>Tổng output</h3><div class="val">'+totalOut.toLocaleString()+'</div></div>'+
    '<div class="card"><h3>Cache read</h3><div class="val">'+totalCache.toLocaleString()+'</div></div>'+
    '<div class="card"><h3>Lượt</h3><div class="val">'+turns.length+'</div></div>'+
    '<div class="card"><h3>Model</h3><div class="val" style="font-size:16px">'+turns[0].model+'</div></div>';

  const tbody = document.getElementById('session-turns');
  tbody.innerHTML = '';
  turns.forEach(t => {
    const ts = (t.timestamp||'').replace('T',' ').slice(0,19);
    const tr = document.createElement('tr');
    tr.innerHTML = '<td>'+toLocal(t.timestamp)+'</td><td>'+t.model+'</td><td>'+(t.input_tokens||0).toLocaleString()+'</td><td>'+(t.cache_read||0).toLocaleString()+'</td><td>'+(t.output_tokens||0).toLocaleString()+'</td><td>'+(t.total_tokens||0).toLocaleString()+'</td>';
    tbody.appendChild(tr);
  });
}

load();
setInterval(load, 30000);
</script>
</body>
</html>"""


# ── HTTP Handler ─────────────────────────────────────────────────────

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # quiet

    def _send(self, content, content_type="application/json", status=200):
        body = content.encode("utf-8") if isinstance(content, str) else content
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self._send(DASHBOARD_HTML, "text/html; charset=utf-8")
        elif path == "/api/stats":
            self._send(api_stats(params))
        elif path == "/api/projects":
            self._send(api_projects())
        elif path == "/api/sessions":
            self._send(api_sessions(params))
        elif path == "/api/session":
            sid = params.get("id", [None])[0]
            self._send(api_session_detail(sid) if sid else json.dumps({"error": "missing_id"}))
        else:
            self._send(json.dumps({"error": "not_found"}), status=404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()


def main():
    port = 9898
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--port" and i + 1 < len(sys.argv[1:]):
            port = int(sys.argv[i + 2])
        elif arg.startswith("--port="):
            port = int(arg.split("=")[1])

    url = f"http://localhost:{port}"
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"BA-kit Dashboard → {url}")
    print("Press Ctrl+C to stop.")

    # Auto-open browser (skip if --no-browser)
    if "--no-browser" not in sys.argv:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
