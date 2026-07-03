-- BA-kit Central License Server — D1 Schema (v2)
-- Run: npx wrangler d1 execute ba-kit-license --file=server/d1-schema.sql

CREATE TABLE IF NOT EXISTS licenses (
    install_id      TEXT PRIMARY KEY,           -- UUID v4
    github_user     TEXT NOT NULL,              -- GitHub username
    token_hash      TEXT NOT NULL,              -- SHA-256 of GitHub OAuth token
    registered_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_validated  TEXT,                       -- last /validate call (was last_heartbeat)
    last_verified   TEXT NOT NULL DEFAULT (datetime('now')),
    revoked_at      TEXT,                       -- NULL if active
    revoked_by      TEXT,                       -- super-admin handle
    revoke_reason   TEXT,
    version         TEXT                        -- BA-kit version installed
);

CREATE INDEX IF NOT EXISTS idx_licenses_github_user ON licenses(github_user);
CREATE INDEX IF NOT EXISTS idx_licenses_last_validated ON licenses(last_validated);

CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    action          TEXT NOT NULL,              -- "register", "validate", "revoke", "reverify"
    install_id      TEXT,
    github_user     TEXT,
    detail          TEXT,                       -- JSON extra info
    ip_hash         TEXT,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_install_id ON audit_log(install_id);

CREATE TABLE IF NOT EXISTS super_admin_tokens (
    token_hash  TEXT PRIMARY KEY,               -- SHA-256 of super-admin bearer token
    label       TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- DROP legacy tables (run manually after migration):
-- DROP TABLE IF EXISTS usage_log;
