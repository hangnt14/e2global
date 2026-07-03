// BA-kit Enterprise Worker — Cloudflare Worker
// Endpoints: POST /org-heartbeat, GET /admin
// Usage tracking per organization. Each org deploys their own instance.

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Max-Age": "86400",
};

// ── Helpers ──────────────────────────────────────────────────────────

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...CORS_HEADERS },
  });
}

async function sha256(text) {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function constantTimeEqual(a, b) {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}

// ── Rate Limiting ────────────────────────────────────────────────────

const RATE_LIMIT = new Map();

function checkRateLimit(ip, maxRequests = 10, windowSeconds = 1) {
  const now = Date.now();
  let entry = RATE_LIMIT.get(ip);
  if (!entry || now > entry.resetAt) {
    entry = { count: 0, resetAt: now + windowSeconds * 1000 };
    RATE_LIMIT.set(ip, entry);
  }
  entry.count++;
  return entry.count <= maxRequests;
}

function cleanRateLimits() {
  const now = Date.now();
  for (const [ip, entry] of RATE_LIMIT) {
    if (now > entry.resetAt) RATE_LIMIT.delete(ip);
  }
}

// ── Input Validation ─────────────────────────────────────────────────

function validateFields(body, allowed) {
  for (const key of Object.keys(body)) {
    if (!allowed.includes(key)) return key;
  }
  return null;
}

// ── Auth ─────────────────────────────────────────────────────────────

function extractBearerToken(request) {
  const auth = request.headers.get("Authorization") || "";
  if (auth.startsWith("Bearer ")) return auth.slice(7);
  return "";
}

function verifyOrgToken(request, env) {
  const token = extractBearerToken(request);
  if (token && constantTimeEqual(token, env.ORG_TOKEN)) return true;

  // Also check body for org_token (used by clients that don't send Bearer header)
  return false;
}

// ── Endpoints ────────────────────────────────────────────────────────

async function handleOrgHeartbeat(request, env) {
  cleanRateLimits();
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  if (!checkRateLimit(ip + ":org-heartbeat", 20, 1)) {
    return json({ error: "rate_limited" }, 429);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid_json" }, 400);
  }

  const { install_id, github_user, org_token, skill, project_slug, version, token_count, model_name, session_id, timestamp } = body;

  // Required fields
  if (!install_id || !github_user || !org_token) {
    return json({ error: "missing_fields", required: ["install_id", "github_user", "org_token"] }, 400);
  }
  if (typeof install_id !== "string" || install_id.length > 64) {
    return json({ error: "invalid_install_id" }, 400);
  }
  if (typeof github_user !== "string" || github_user.length > 64) {
    return json({ error: "invalid_github_user" }, 400);
  }

  const badField = validateFields(body, [
    "install_id", "github_user", "org_token", "skill", "project_slug",
    "version", "token_count", "model_name", "session_id", "timestamp",
  ]);
  if (badField) return json({ error: "unknown_field", field: badField }, 400);

  // Verify org_token (constant-time, also check Bearer header)
  const bearerToken = extractBearerToken(request);
  const isBearerValid = bearerToken && constantTimeEqual(bearerToken, env.ORG_TOKEN);
  const isBodyValid = constantTimeEqual(org_token, env.ORG_TOKEN);

  if (!isBearerValid && !isBodyValid) {
    return json({ status: "denied", reason: "invalid_org_token" }, 401);
  }

  // UPSERT org_members + INSERT usage_log (guarded — D1 may be cold-starting)
  try {
    await env.DB.prepare(
      `INSERT INTO org_members (github_user, install_id, last_heartbeat)
       VALUES (?, ?, datetime('now'))
       ON CONFLICT(github_user) DO UPDATE SET
         install_id = excluded.install_id,
         last_heartbeat = excluded.last_heartbeat,
         is_active = 1`
    ).bind(github_user, install_id).run();

    const ipHash = await sha256(ip);
    await env.DB.prepare(
      `INSERT INTO usage_log (install_id, github_user, skill, project_slug, version, token_count, model_name, session_id, timestamp, ip_hash)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      install_id,
      github_user,
      skill || null,
      project_slug || null,
      version || null,
      token_count || null,
      model_name || null,
      session_id || null,
      timestamp || new Date().toISOString(),
      ipHash
    ).run();
  } catch (e) {
    // D1 not ready (cold start) — still return ok, data will come on next heartbeat
    return json({ status: "ok", warning: "db_unavailable" });
  }

  return json({ status: "ok" });
}

async function handleAdmin(request, env) {
  const token = extractBearerToken(request);
  if (!token || !constantTimeEqual(token, env.ADMIN_TOKEN)) {
    return new Response(LOGIN_HTML, {
      status: 401,
      headers: { "Content-Type": "text/html; charset=utf-8", ...CORS_HEADERS },
    });
  }

  return new Response(ADMIN_HTML, {
    headers: { "Content-Type": "text/html; charset=utf-8", ...CORS_HEADERS },
  });
}

// ── Login Page ───────────────────────────────────────────────────────

const LOGIN_HTML = `<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BA-kit Enterprise — Đăng nhập</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
.login-box { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 40px; width: 100%; max-width: 400px; text-align: center; }
h1 { font-size: 20px; color: #58a6ff; margin-bottom: 8px; }
p { color: #8b949e; font-size: 14px; margin-bottom: 24px; }
input { width: 100%; padding: 10px 14px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 15px; margin-bottom: 16px; }
input:focus { outline: none; border-color: #58a6ff; }
button { width: 100%; padding: 10px; background: #1f6feb; border: none; border-radius: 6px; color: #fff; font-size: 15px; cursor: pointer; }
button:hover { background: #388bfd; }
.error { color: #f85149; font-size: 13px; margin-top: 12px; display: none; }
</style>
</head>
<body>
<div class="login-box">
  <h1>BA-kit Enterprise</h1>
  <p>Nhập mã quản trị để xem bảng điều khiển</p>
  <form id="login-form">
    <input type="password" id="token" placeholder="Mã quản trị" autofocus>
    <button type="submit">Đăng nhập</button>
    <div class="error" id="error">Mã không đúng</div>
  </form>
</div>
<script>
// Auto-login if token saved from previous session
(async function() {
  const saved = localStorage.getItem('ba_kit_admin_token');
  if (!saved) return;
  const res = await fetch(window.location.pathname, {
    headers: { 'Authorization': 'Bearer ' + saved }
  });
  if (res.status === 200) {
    document.open();
    document.write(await res.text());
    document.close();
  }
})();

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const token = document.getElementById('token').value;
  const res = await fetch(window.location.pathname, {
    headers: { 'Authorization': 'Bearer ' + token }
  });
  if (res.status === 200) {
    localStorage.setItem('ba_kit_admin_token', token);
    document.open();
    document.write(await res.text());
    document.close();
  } else {
    document.getElementById('error').style.display = 'block';
  }
});
</script>
</body>
</html>`;

// ── Admin Dashboard (skeleton — full UI in Phase 6) ──────────────────

const ADMIN_HTML = `<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BA-kit Enterprise — Quản lý</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0d1117;color:#c9d1d9;padding:24px;min-height:100vh}
h1{font-size:24px;color:#58a6ff;margin-bottom:8px}
header{margin-bottom:20px}
header p{color:#8b949e;font-size:14px}
.filters{display:flex;gap:8px;margin-bottom:16px}
.filters button{background:#21262d;border:1px solid #30363d;color:#c9d1d9;padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.filters button.active{background:#1f6feb;border-color:#1f6feb;color:#fff}
.dashboard-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:20px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}
.card h3{font-size:11px;color:#8b949e;text-transform:uppercase;margin-bottom:8px}
.stat-value{font-size:28px;font-weight:600;color:#58a6ff}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:16px;margin-bottom:20px}
.chart-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}
.chart-card h3{font-size:13px;color:#8b949e;margin-bottom:10px}
canvas{width:100%!important;max-height:200px}
table{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:12px}
th,td{text-align:left;padding:6px 10px;border-bottom:1px solid #21262d}
th{color:#8b949e}
tr:hover{background:#1c2128}
.status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.status-active{background:#3fb950}
.status-idle{background:#d29922}
.status-inactive{background:#f85149}
@media(max-width:768px){.charts{grid-template-columns:1fr}.dashboard-grid{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<header>
  <h1>BA-kit Enterprise — Quản lý đội nhóm</h1>
  <p>Bảng điều khiển theo dõi sử dụng BA-kit</p>
</header>

<div class="filters" id="filters">
  <button data-days="7">7 ngày</button>
  <button data-days="30" class="active">30 ngày</button>
  <button data-days="90">90 ngày</button>
  <button data-days="365">Tất cả</button>
</div>

<main class="dashboard-grid" id="stats-grid">
  <div class="card"><h3>Thành viên</h3><div class="stat-value" id="total-members">-</div></div>
  <div class="card"><h3>Hoạt động hôm nay</h3><div class="stat-value" id="active-today">-</div></div>
  <div class="card"><h3>Kỹ năng đã dùng</h3><div class="stat-value" id="total-skills">-</div></div>
  <div class="card"><h3>Tổng token</h3><div class="stat-value" id="total-tokens">-</div></div>
</main>

<div class="charts">
  <div class="chart-card"><h3>Token theo ngày</h3><canvas id="token-chart"></canvas></div>
  <div class="chart-card"><h3>Top thành viên</h3><canvas id="members-chart"></canvas></div>
  <div class="chart-card"><h3>Top kỹ năng</h3><canvas id="skills-chart"></canvas></div>
  <div class="chart-card"><h3>Top dự án</h3><canvas id="projects-chart"></canvas></div>
</div>

<h3 style="margin-bottom:12px">Danh sách thành viên</h3>
<table><thead><tr><th>Thành viên</th><th>Cuối online</th><th>Trạng thái</th></tr></thead><tbody id="member-table"></tbody></table>

<h3 style="margin-bottom:12px">Hoạt động gần đây</h3>
<table><thead><tr><th>Thành viên</th><th>Kỹ năng</th><th>Dự án</th><th>Token</th><th>Thời gian</th></tr></thead><tbody id="recent-table"></tbody></table>
<p style="color:#8b949e;font-size:11px;margin-top:12px">Tự động cập nhật mỗi 30 giây</p>

<script>
let currentDays = 30;
function esc(str) { const d=document.createElement('div'); d.textContent=str||''; return d.innerHTML; }
function fmtTime(iso) {
  if (!iso) return '-';
  const s = iso.includes('T') ? iso : iso.replace(' ','T') + 'Z';
  const d = new Date(s);
  return isNaN(d.getTime()) ? iso.replace('T',' ').slice(0,16) : d.toLocaleString('sv-SE').replace('T',' ').slice(0,16);
}
document.getElementById('filters').addEventListener('click', e => {
  if (e.target.tagName !== 'BUTTON') return;
  document.querySelectorAll('#filters button').forEach(b => b.classList.remove('active'));
  e.target.classList.add('active');
  currentDays = parseInt(e.target.dataset.days) || 30;
  load();
});

async function load() {
  const token = localStorage.getItem('ba_kit_admin_token') || '';
  if (!token) return;
  try {
    const res = await fetch('/api/admin-stats?days=' + currentDays, { headers: { 'Authorization': 'Bearer ' + token } });
    if (!res.ok) return;
    const d = await res.json();
    document.getElementById('total-members').textContent = d.totalMembers || 0;
    document.getElementById('active-today').textContent = d.activeToday || 0;
    document.getElementById('total-skills').textContent = d.skillCount || 0;
    document.getElementById('total-tokens').textContent = (d.totalTokens || 0).toLocaleString();
    drawLine('token-chart', d.tokenByDay || [], 'dt', 'tk');
    drawBars('members-chart', (d.topMembers || []).map(m => [m.github_user, m.tk || 0]));
    drawBars('skills-chart', (d.topSkills || []).map(s => [s.skill, s.cnt || 0]));
    drawBars('projects-chart', (d.topProjects || []).map(p => [p.project_slug || '-', p.tk || 0]));
    renderMembers(d.memberList || []);
    renderRecent(d.recentActivity || []);
  } catch(e) { console.error(e); }
}

function drawLine(canvasId, data, xKey, yKey) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!data.length) { ctx.fillStyle='#8b949e'; ctx.fillText('Chưa có dữ liệu',10,20); return; }
  const w = canvas.parentElement.clientWidth - 32;
  const h = 200; canvas.width = w*2; canvas.height = h*2;
  canvas.style.width = w+'px'; canvas.style.height = h+'px';
  ctx.scale(2,2);
  const maxV = Math.max(...data.map(d => d[yKey] || 0), 1);
  const pw = w-50, ph = h-30;
  ctx.strokeStyle = '#30363d'; ctx.lineWidth = 0.5;
  for (let i=0;i<=4;i++) { const y=10+ph/4*i; ctx.beginPath(); ctx.moveTo(50,y); ctx.lineTo(w-10,y); ctx.stroke(); }
  ctx.strokeStyle = '#58a6ff'; ctx.lineWidth = 2; ctx.beginPath();
  data.forEach((d,i) => { const x = 50 + pw/(data.length-1||1)*i; const y = 10+ph - (d[yKey]||0)/maxV*ph; i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y); });
  ctx.stroke();
  ctx.fillStyle = '#8b949e'; ctx.font = '9px sans-serif';
  ctx.fillText(maxV.toLocaleString(), 5, 14);
  if (data.length > 0) {
    ctx.fillText(data[0][xKey] || '', 50, h-2);
    const lastLabel = (data[data.length-1][xKey] || '').slice(-5);
    ctx.fillText(lastLabel, w-55, h-2);
  }
}

function drawBars(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!data.length) { ctx.fillStyle='#8b949e'; ctx.fillText('Chưa có dữ liệu',10,20); return; }
  const w = canvas.parentElement.clientWidth - 32;
  const n = Math.min(data.length, 8);
  const barH = 16; const gap = 8;
  const labelW = 130;
  const h = n * (barH + gap) + 10;
  canvas.width = w*2; canvas.height = h*2;
  canvas.style.width = w+'px'; canvas.style.height = h+'px';
  ctx.scale(2,2);
  const maxV = Math.max(...data.map(d => d[1]), 1);
  const colors = ['#58a6ff','#3fb950','#d29922','#f85149','#bc8cff','#79c0ff','#ffa657','#7ee787'];
  data.slice(0,n).forEach((d,i) => {
    const y = 5 + i*(barH+gap);
    const barW = Math.max(2, d[1]/maxV*(w - labelW - 70));
    ctx.fillStyle = colors[i%colors.length];
    ctx.fillRect(labelW, y, barW, barH);
    ctx.fillStyle = '#8b949e'; ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    const label = (d[0]||'').length > 20 ? (d[0]||'').slice(0,18)+'..' : (d[0]||'');
    ctx.fillText(label, labelW - 6, y + barH - 4);
    ctx.textAlign = 'left';
    ctx.fillStyle = '#c9d1d9'; ctx.font = '10px sans-serif';
    ctx.fillText(d[1].toLocaleString(), labelW + barW + 6, y + barH - 4);
  });
  ctx.textAlign = 'left';
}

function renderMembers(data) {
  const tbody = document.getElementById('member-table');
  tbody.innerHTML = '';
  data.forEach(m => {
    const tr = document.createElement('tr');
    const hb = m.last_heartbeat || '';
    const hbDate = hb.slice(0,10);
    const daysSince = hb ? Math.floor((Date.now() - new Date(hb.replace(' ','T')+'Z').getTime()) / 86400000) : 999;
    let status = '<span class="status-dot status-inactive"></span>Không hoạt động';
    if (daysSince < 7) status = '<span class="status-dot status-active"></span>Hoạt động';
    else if (daysSince < 30) status = '<span class="status-dot status-idle"></span>Ít dùng';
    tr.innerHTML = '<td>@'+esc(m.github_user)+'</td><td>'+fmtTime(hb)+'</td><td>'+status+'</td>';
    tbody.appendChild(tr);
  });
}

function renderRecent(data) {
  const tbody = document.getElementById('recent-table');
  tbody.innerHTML = '';
  data.forEach(r => {
    const ts = fmtTime(r.timestamp);
    const tr = document.createElement('tr');
    tr.innerHTML = '<td>@'+esc(r.github_user)+'</td><td>'+esc(r.skill)+'</td><td>'+esc(r.project_slug)+'</td><td>'+(r.token_count||0).toLocaleString()+'</td><td>'+ts+'</td>';
    tbody.appendChild(tr);
  });
}

load();
setInterval(load, 30000);
</script>
</body>
</html>`;

async function handleAdminStats(request, env) {
  const token = extractBearerToken(request);
  if (!token || !constantTimeEqual(token, env.ADMIN_TOKEN)) {
    return json({ error: "unauthorized" }, 401);
  }

  const url = new URL(request.url);
  const rawDays = parseInt(url.searchParams.get("days"), 10);
  const days = Number.isFinite(rawDays) && rawDays > 0 ? Math.min(rawDays, 365) : 30;
  const cutoff = new Date(Date.now() - days * 86400 * 1000).toISOString();

  try {
    const [totalMembers, activeToday, skillCount, totalTokens, recentActivity,
           topMembers, topProjects, topSkills, memberList, tokenByDay] = await Promise.all([
      env.DB.prepare("SELECT COUNT(*) as cnt FROM org_members").first(),
      env.DB.prepare("SELECT COUNT(DISTINCT github_user) as cnt FROM usage_log WHERE date(timestamp, '+7 hours') = date('now', '+7 hours')").first(),
      env.DB.prepare("SELECT COUNT(DISTINCT skill) as cnt FROM usage_log").first(),
      env.DB.prepare("SELECT COALESCE(SUM(token_count), 0) as cnt FROM usage_log").first(),
      env.DB.prepare("SELECT github_user, skill, project_slug, token_count, timestamp FROM usage_log ORDER BY timestamp DESC LIMIT 20").all(),
      env.DB.prepare("SELECT github_user, COALESCE(SUM(token_count),0) as tk, COUNT(*) as sessions FROM usage_log WHERE timestamp >= ? GROUP BY github_user ORDER BY tk DESC LIMIT 10").bind(cutoff).all(),
      env.DB.prepare("SELECT project_slug, COALESCE(SUM(token_count),0) as tk, COUNT(*) as sessions FROM usage_log WHERE timestamp >= ? GROUP BY project_slug ORDER BY tk DESC LIMIT 10").bind(cutoff).all(),
      env.DB.prepare("SELECT skill, COUNT(*) as cnt, COALESCE(SUM(token_count),0) as tk FROM usage_log WHERE timestamp >= ? GROUP BY skill ORDER BY cnt DESC LIMIT 10").bind(cutoff).all(),
      env.DB.prepare("SELECT github_user, last_heartbeat, is_active FROM org_members ORDER BY last_heartbeat DESC").all(),
      env.DB.prepare("SELECT date(timestamp, '+7 hours') as dt, COALESCE(SUM(token_count),0) as tk FROM usage_log WHERE timestamp >= ? GROUP BY dt ORDER BY dt ASC").bind(cutoff).all(),
    ]);

    return json({
      totalMembers: totalMembers?.cnt || 0,
      activeToday: activeToday?.cnt || 0,
      skillCount: skillCount?.cnt || 0,
      totalTokens: totalTokens?.cnt || 0,
      recentActivity: recentActivity?.results || [],
      topMembers: topMembers?.results || [],
      topProjects: topProjects?.results || [],
      topSkills: topSkills?.results || [],
      memberList: memberList?.results || [],
      tokenByDay: tokenByDay?.results || [],
    });
  } catch (e) {
    return json({ error: "db_unavailable" }, 503);
  }
}

// ── Router ───────────────────────────────────────────────────────────

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    let response;
    switch (path) {
      case "/org-heartbeat":
        response = await handleOrgHeartbeat(request, env);
        break;
      case "/admin":
        response = await handleAdmin(request, env);
        break;
      case "/api/admin-stats":
        response = await handleAdminStats(request, env);
        break;
      default:
        response = new Response("BA-kit Enterprise Server", { status: 200, headers: CORS_HEADERS });
    }

    return response;
  },
};
