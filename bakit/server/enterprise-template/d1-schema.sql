-- BA-kit Enterprise Worker — D1 Schema
-- Run: npx wrangler d1 execute ba-kit-enterprise --file=d1-schema.sql

CREATE TABLE IF NOT EXISTS org_members (
    github_user     TEXT PRIMARY KEY,
    install_id      TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'member',  -- "admin" | "member"
    joined_at       TEXT NOT NULL DEFAULT (datetime('now')),
    last_heartbeat  TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS usage_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    install_id      TEXT NOT NULL,
    github_user     TEXT NOT NULL,
    skill           TEXT NOT NULL,
    project_slug    TEXT,
    version         TEXT,
    token_count     INTEGER,                     -- token_delta from client heartbeat
    model_name      TEXT,                        -- Model being used
    session_id      TEXT,                        -- Chat session ID
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    ip_hash         TEXT                         -- SHA-256 of client IP
);

CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_log(github_user);
CREATE INDEX IF NOT EXISTS idx_usage_project ON usage_log(project_slug);
CREATE INDEX IF NOT EXISTS idx_usage_skill ON usage_log(skill);
