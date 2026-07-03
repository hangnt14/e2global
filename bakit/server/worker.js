// BA-kit Central License Server — Cloudflare Worker
// Endpoints: POST /register, POST /validate, POST /revoke, GET /super-admin, GET /api/super-admin-stats
// Usage tracking moved to enterprise worker (server/enterprise-template/worker.js)

const GITHUB_API = "https://api.github.com";
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

// ponytail: constantTimeEqual unused now (verifySuperAdmin uses DB lookup).
// Reserved for single-token mode if DB lookup is replaced later.
function constantTimeEqual(a, b) {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}

// ── Rate Limiting (simple in-memory, per-Worker instance) ────────────
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

// Clean stale rate limit entries periodically
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

// ── Super-admin auth ─────────────────────────────────────────────────

function extractBearerToken(request) {
  const auth = request.headers.get("Authorization") || "";
  if (auth.startsWith("Bearer ")) return auth.slice(7);
  return "";
}

async function verifySuperAdmin(request, env) {
  const token = extractBearerToken(request);
  if (!token) return false;

  // 1. Check D1 super_admin_tokens table (multi-token support)
  const hash = await sha256(token);
  const row = await env.DB.prepare(
    "SELECT token_hash FROM super_admin_tokens WHERE token_hash = ?"
  ).bind(hash).first();
  if (row) return true;

  // 2. Fallback: check SUPER_ADMIN_TOKEN secret (bootstrap)
  if (env.SUPER_ADMIN_TOKEN && constantTimeEqual(token, env.SUPER_ADMIN_TOKEN)) {
    return true;
  }

  return false;
}

// ── Endpoints ────────────────────────────────────────────────────────

async function handleRegister(request, env) {
  cleanRateLimits();
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  if (!checkRateLimit(ip + ":register", 3, 60)) {
    return json({ error: "rate_limited" }, 429);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid_json" }, 400);
  }

  const { install_id, github_token } = body;
  if (!install_id || !github_token) {
    return json({ error: "missing_fields", required: ["install_id", "github_token"] }, 400);
  }
  if (typeof install_id !== "string" || install_id.length > 64) {
    return json({ error: "invalid_install_id" }, 400);
  }
  if (typeof github_token !== "string" || github_token.length > 256) {
    return json({ error: "invalid_token" }, 400);
  }

  const badField = validateFields(body, ["install_id", "github_token"]);
  if (badField) return json({ error: "unknown_field", field: badField }, 400);

  // Step 1: Verify GitHub token → get username
  let github_user;
  try {
    const userRes = await fetch(`${GITHUB_API}/user`, {
      headers: {
        Authorization: `Bearer ${github_token}`,
        "User-Agent": "ba-kit-license/1.0",
        Accept: "application/vnd.github+json",
      },
    });
    if (!userRes.ok) {
      return json({ status: "denied", reason: "invalid_github_token" }, 401);
    }
    const userData = await userRes.json();
    github_user = userData.login;
  } catch {
    return json({ error: "github_api_error" }, 502);
  }

  // Step 2: Verify repo access
  const { GITHUB_REPO_OWNER, GITHUB_REPO_NAME } = env;
  try {
    const repoRes = await fetch(
      `${GITHUB_API}/repos/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}`,
      {
        headers: {
          Authorization: `Bearer ${github_token}`,
          "User-Agent": "ba-kit-license/1.0",
          Accept: "application/vnd.github+json",
        },
      }
    );
    if (repoRes.status !== 200) {
      return json({ status: "denied", reason: "no_repo_access", github_user }, 403);
    }
  } catch {
    return json({ error: "github_api_error" }, 502);
  }

  // Step 3: Revoke old licenses for same github_user (re-register)
  const now = new Date().toISOString();
  await env.DB.prepare(
    `UPDATE licenses SET revoked_at = ?, revoked_by = 'system', revoke_reason = 're-registered with new install_id'
     WHERE github_user = ? AND install_id != ? AND revoked_at IS NULL`
  ).bind(now, github_user, install_id).run();

  // Step 4: Store license
  const tokenHash = await sha256(github_token);

  await env.DB.prepare(
    `INSERT OR REPLACE INTO licenses (install_id, github_user, token_hash, registered_at, last_verified, revoked_at)
     VALUES (?, ?, ?, ?, ?, NULL)`
  )
    .bind(install_id, github_user, tokenHash, now, now)
    .run();

  // Step 5: Audit log
  const ipHash = await sha256(ip);
  await env.DB.prepare(
    `INSERT INTO audit_log (action, install_id, github_user, detail, ip_hash)
     VALUES ('register', ?, ?, ?, ?)`
  )
    .bind(install_id, github_user, JSON.stringify({ version: body.version || null }), ipHash)
    .run();

  return json({ status: "ok", github_user });
}

async function handleValidate(request, env) {
  cleanRateLimits();
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  if (!checkRateLimit(ip + ":validate", 10, 1)) {
    return json({ error: "rate_limited" }, 429);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid_json" }, 400);
  }

  const { install_id, github_token } = body;
  if (!install_id) {
    return json({ error: "missing_fields", required: ["install_id"] }, 400);
  }
  if (typeof install_id !== "string" || install_id.length > 64) {
    return json({ error: "invalid_install_id" }, 400);
  }

  const badField = validateFields(body, ["install_id", "github_token"]);
  if (badField) return json({ error: "unknown_field", field: badField }, 400);

  // Lookup license
  const lic = await env.DB.prepare(
    "SELECT github_user, token_hash, last_verified, revoked_at FROM licenses WHERE install_id = ?"
  )
    .bind(install_id)
    .first();

  if (!lic) {
    return json({ status: "denied", reason: "unregistered" }, 403);
  }
  if (lic.revoked_at) {
    return json({ status: "denied", reason: "revoked" }, 403);
  }

  // Re-verify repo access if >24h since last verification AND github_token provided
  const lastVerified = new Date(lic.last_verified);
  const now = new Date();
  const hoursSinceVerified = (now - lastVerified) / (1000 * 60 * 60);

  if (hoursSinceVerified > 24) {
    if (!github_token) {
      return json({ status: "denied", reason: "reverify_required" }, 403);
    }

    const { GITHUB_REPO_OWNER, GITHUB_REPO_NAME } = env;
    try {
      const repoRes = await fetch(
        `${GITHUB_API}/repos/${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}`,
        {
          headers: {
            Authorization: `Bearer ${github_token}`,
            "User-Agent": "ba-kit-license/1.0",
            Accept: "application/vnd.github+json",
          },
        }
      );
      if (repoRes.status !== 200) {
        await env.DB.prepare(
          "UPDATE licenses SET revoked_at = datetime('now'), revoked_by = 'system', revoke_reason = 'auto: access_revoked' WHERE install_id = ?"
        ).bind(install_id).run();

        const ipHash = await sha256(ip);
        await env.DB.prepare(
          `INSERT INTO audit_log (action, install_id, github_user, detail, ip_hash)
           VALUES ('revoke', ?, ?, 'auto: access_revoked', ?)`
        ).bind(install_id, lic.github_user, ipHash).run();

        return json({ status: "denied", reason: "access_revoked" }, 403);
      }
    } catch {
      // GitHub API error → allow with stale cache (grace period)
    }

    // Update last_verified + token_hash
    const newTokenHash = await sha256(github_token);
    await env.DB.prepare(
      "UPDATE licenses SET last_verified = datetime('now'), token_hash = ? WHERE install_id = ?"
    ).bind(newTokenHash, install_id).run();

    // Audit log: reverify
    const ipHash = await sha256(ip);
    await env.DB.prepare(
      `INSERT INTO audit_log (action, install_id, github_user, detail, ip_hash)
       VALUES ('reverify', ?, ?, ?, ?)`
    ).bind(install_id, lic.github_user, JSON.stringify({ hours: Math.round(hoursSinceVerified) }), ipHash).run();
  }

  // Update last_validated
  await env.DB.prepare(
    "UPDATE licenses SET last_validated = datetime('now') WHERE install_id = ?"
  ).bind(install_id).run();

  return json({ status: "ok", github_user: lic.github_user });
}

async function handleRevoke(request, env) {
  // Verify super-admin
  if (!(await verifySuperAdmin(request, env))) {
    return json({ error: "unauthorized" }, 401);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "invalid_json" }, 400);
  }

  const { install_id, github_user, reason } = body;
  if (!install_id && !github_user) {
    return json({ error: "missing_fields", required: ["install_id or github_user"] }, 400);
  }

  const badField = validateFields(body, ["install_id", "github_user", "reason"]);
  if (badField) return json({ error: "unknown_field", field: badField }, 400);

  // Build WHERE clause
  let whereClause = "";
  let bindParams = [];
  if (install_id) {
    whereClause = "install_id = ? AND revoked_at IS NULL";
    bindParams.push(install_id);
  } else {
    whereClause = "github_user = ? AND revoked_at IS NULL";
    bindParams.push(github_user);
  }

  const token = extractBearerToken(request);
  const tokenHash = await sha256(token);
  const adminRow = await env.DB.prepare(
    "SELECT label FROM super_admin_tokens WHERE token_hash = ?"
  ).bind(tokenHash).first();
  const revokedBy = adminRow?.label || "unknown";

  const revokeReason = reason || "manual_revocation";

  // Query affected install_ids BEFORE update to avoid TOCTOU race
  let affectedIds = [];
  if (install_id) {
    affectedIds = [install_id];
  } else {
    const rows = await env.DB.prepare(
      "SELECT install_id FROM licenses WHERE github_user = ? AND revoked_at IS NULL"
    ).bind(github_user).all();
    affectedIds = (rows?.results || []).map(r => r.install_id);
  }

  const result = await env.DB.prepare(
    `UPDATE licenses SET revoked_at = datetime('now'), revoked_by = ?, revoke_reason = ? WHERE ${whereClause}`
  ).bind(revokedBy, revokeReason, ...bindParams).run();

  // Audit log for each affected license
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const ipHash = await sha256(ip);

  for (const id of affectedIds) {
    const lic = await env.DB.prepare(
      "SELECT github_user FROM licenses WHERE install_id = ?"
    ).bind(id).first();
    await env.DB.prepare(
      `INSERT INTO audit_log (action, install_id, github_user, detail, ip_hash)
       VALUES ('revoke', ?, ?, ?, ?)`
    ).bind(id, lic?.github_user || github_user || "", JSON.stringify({ reason: revokeReason, by: revokedBy }), ipHash).run();
  }

  return json({ status: "ok", revoked_count: result.meta?.changes || 0 });
}

async function handleSuperAdmin(request, env) {
  if (!(await verifySuperAdmin(request, env))) {
    return new Response(LOGIN_HTML, {
      status: 401,
      headers: { "Content-Type": "text/html; charset=utf-8", ...CORS_HEADERS },
    });
  }

  return new Response(SUPER_ADMIN_HTML, {
    headers: { "Content-Type": "text/html; charset=utf-8", ...CORS_HEADERS },
  });
}

async function handleApiSuperAdminStats(request, env) {
  if (!(await verifySuperAdmin(request, env))) {
    return json({ error: "unauthorized" }, 401);
  }

  const url = new URL(request.url);
  const rawDays = parseInt(url.searchParams.get("days"), 10);
  const days = Number.isFinite(rawDays) && rawDays > 0 ? Math.min(rawDays, 365) : 30;
  const cutoff = new Date(Date.now() - days * 86400 * 1000).toISOString();

  const [totalUsers, totalRevoked, activeToday, recentRegistrations, recentRevocations, recentActivity, recentLicenses] =
    await Promise.all([
      env.DB.prepare("SELECT COUNT(*) AS total FROM licenses WHERE revoked_at IS NULL").first(),
      env.DB.prepare("SELECT COUNT(*) AS total FROM licenses WHERE revoked_at IS NOT NULL").first(),
      env.DB.prepare("SELECT COUNT(*) AS total FROM licenses WHERE revoked_at IS NULL AND last_validated >= datetime('now', '+7 hours', '-1 days')").first(),
      env.DB.prepare("SELECT COUNT(*) AS total FROM audit_log WHERE action = 'register' AND timestamp >= ?").bind(cutoff).first(),
      env.DB.prepare("SELECT COUNT(*) AS total FROM audit_log WHERE action = 'revoke' AND timestamp >= ?").bind(cutoff).first(),
      env.DB.prepare("SELECT action, install_id, github_user, detail, timestamp FROM audit_log ORDER BY timestamp DESC LIMIT 50").all(),
      env.DB.prepare("SELECT install_id, github_user, registered_at, last_validated, revoked_at FROM licenses ORDER BY registered_at DESC LIMIT 50").all(),
    ]);

  return json({
    totalUsers: totalUsers?.total || 0,
    totalRevoked: totalRevoked?.total || 0,
    activeToday: activeToday?.total || 0,
    recentRegistrations: recentRegistrations?.total || 0,
    recentRevocations: recentRevocations?.total || 0,
    recentActivity: recentActivity?.results || [],
    recentLicenses: recentLicenses?.results || [],
    days,
  });
}

// ── Login Page (super-admin) ─────────────────────────────────────────

const LOGIN_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BA-kit License — Super Admin Login</title>
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
  <h1>BA-kit License</h1>
  <p>Super Admin Dashboard</p>
  <form id="login-form">
    <input type="password" id="token" placeholder="Super Admin Token" autofocus>
    <button type="submit">Login</button>
    <div class="error" id="error">Invalid token</div>
  </form>
</div>
<script>
// Auto-login if token saved from previous session
(async function() {
  const saved = localStorage.getItem('ba_kit_super_admin_token');
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
    localStorage.setItem('ba_kit_super_admin_token', token);
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

// ── Super Admin Dashboard (skeleton — full UI in Phase 6) ────────────

const SUPER_ADMIN_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BA-kit License — Super Admin</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0d1117;color:#c9d1d9;padding:24px;min-height:100vh}
h1{font-size:24px;color:#58a6ff;margin-bottom:8px}
header{margin-bottom:20px}
header p{color:#8b949e;font-size:14px}
.dashboard-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:20px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}
.card h3{font-size:11px;color:#8b949e;text-transform:uppercase;margin-bottom:8px}
.stat-value{font-size:28px;font-weight:600;color:#58a6ff}
.revoke-box{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin-bottom:20px}
.revoke-box h3{font-size:14px;color:#8b949e;margin-bottom:12px}
.revoke-box input{background:#0d1117;border:1px solid #30363d;color:#c9d1d9;padding:8px 12px;border-radius:6px;font-size:13px;margin-right:8px;width:200px}
.revoke-box button{background:#da3633;border:none;color:#fff;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.revoke-box .result{margin-top:10px;font-size:13px}
.result-ok{color:#3fb950}
.result-err{color:#f85149}
table{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:12px}
th,td{text-align:left;padding:6px 10px;border-bottom:1px solid #21262d}
th{color:#8b949e}
tr:hover{background:#1c2128}
@media(max-width:768px){.dashboard-grid{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<header>
  <h1>BA-kit License — Super Admin</h1>
  <p>Central License Server Dashboard</p>
</header>

<main class="dashboard-grid" id="stats-grid">
  <div class="card"><h3>Active Licenses</h3><div class="stat-value" id="total-users">-</div></div>
  <div class="card"><h3>Revoked Licenses</h3><div class="stat-value" id="total-revoked">-</div></div>
  <div class="card"><h3>Active Today</h3><div class="stat-value" id="active-today">-</div></div>
  <div class="card"><h3>Recent Registrations</h3><div class="stat-value" id="recent-reg">-</div></div>
</main>

<div class="revoke-box">
  <h3>Thu hồi license</h3>
  <input type="text" id="revoke-input" placeholder="github_user hoặc install_id">
  <button onclick="revokeLicense()">Thu hồi</button>
  <div class="result" id="revoke-result"></div>
</div>

<h3>Licenses gần đây</h3>
<table><thead><tr><th>GitHub User</th><th>Install ID</th><th>Đăng ký</th><th>Last Seen</th><th>Trạng thái</th></tr></thead><tbody id="licenses-table"></tbody></table>

<h3>Audit Log</h3>
<table><thead><tr><th>Action</th><th>User</th><th>Detail</th><th>Time</th></tr></thead><tbody id="audit-table"></tbody></table>
<p style="color:#8b949e;font-size:11px;margin-top:12px">Tự động cập nhật mỗi 30 giây</p>

<script>
const token = localStorage.getItem('ba_kit_super_admin_token') || '';
function esc(str) { const d=document.createElement('div'); d.textContent=str||''; return d.innerHTML; }
function fmtTime(iso) {
  if (!iso) return '-';
  const s = iso.includes('T') ? iso : iso.replace(' ','T') + 'Z';
  const d = new Date(s);
  return isNaN(d.getTime()) ? iso.replace('T',' ').slice(0,16) : d.toLocaleString('sv-SE').replace('T',' ').slice(0,16);
}

async function load() {
  if (!token) return;
  try { const res = await fetch('/api/super-admin-stats', { headers: { 'Authorization': 'Bearer ' + token } });
  if (!res.ok) return; const d = await res.json();
  document.getElementById('total-users').textContent = d.totalUsers;
  document.getElementById('total-revoked').textContent = d.totalRevoked;
  document.getElementById('active-today').textContent = d.activeToday;
  document.getElementById('recent-reg').textContent = d.recentRegistrations;
  renderLicenses(d.recentLicenses || []);
  renderAudit(d.recentActivity || []);
  } catch(e) { console.error(e); }
}

function renderLicenses(data) {
  const tbody = document.getElementById('licenses-table');
  tbody.innerHTML = '';
  data.forEach(l => {
    const tr = document.createElement('tr');
    const ls = fmtTime(l.last_validated);
    const st = l.revoked_at ? '<span style="color:#f85149">Revoked</span>' : '<span style="color:#3fb950">Active</span>';
    tr.innerHTML = '<td>@'+esc(l.github_user)+'</td><td>'+esc((l.install_id||'').slice(0,12))+'...</td><td>'+(l.registered_at||'').slice(0,10)+'</td><td>'+ls+'</td><td>'+st+'</td>';
    tbody.appendChild(tr);
  });
}

function renderAudit(data) {
  const tbody = document.getElementById('audit-table');
  tbody.innerHTML = '';
  data.forEach(r => {
    const ts = fmtTime(r.timestamp);
    const tr = document.createElement('tr');
    tr.innerHTML = '<td>'+esc(r.action)+'</td><td>@'+esc(r.github_user)+'</td><td>'+esc((r.detail||'').slice(0,60))+'</td><td>'+ts+'</td>';
    tbody.appendChild(tr);
  });
}

async function revokeLicense() {
  const input = document.getElementById('revoke-input').value.trim();
  if (!input) { document.getElementById('revoke-result').innerHTML = '<span class="result-err">Nhập github_user hoặc install_id</span>'; return; }
  const isInstallId = /^[a-f0-9-]{36}$/.test(input);
  const body = isInstallId ? { install_id: input } : { github_user: input };
  try {
    const res = await fetch('/revoke', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token }, body: JSON.stringify(body) });
    const d = await res.json();
    if (res.ok) { document.getElementById('revoke-result').innerHTML = '<span class="result-ok">Da thu hoi '+d.revoked_count+' license(s)</span>'; load(); }
    else { document.getElementById('revoke-result').innerHTML = '<span class="result-err">'+(d.reason||d.error||'Unknown error')+'</span>'; }
  } catch(e) { document.getElementById('revoke-result').innerHTML = '<span class="result-err">Network error</span>'; }
}

load();
setInterval(load, 30000);
</script>
</body>
</html>`;

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
      case "/register":
        response = await handleRegister(request, env);
        break;
      case "/validate":
        response = await handleValidate(request, env);
        break;
      case "/revoke":
        response = await handleRevoke(request, env);
        break;
      case "/super-admin":
        response = await handleSuperAdmin(request, env);
        break;
      case "/api/super-admin-stats":
        response = await handleApiSuperAdminStats(request, env);
        break;
      default:
        response = new Response("BA-kit Central License Server", { status: 200, headers: CORS_HEADERS });
    }

    return response;
  },
};
