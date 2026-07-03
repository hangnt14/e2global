---
name: reverse-web
description: Reverse-engineer a live website into BA intake documentation. Crawls with Playwright, then session AI synthesizes evidence into intake-form-template.md format for /ba-start lifecycle.
argument-hint: "<url> [--consent] [--max-pages N] [--slug <slug>] [--date <date>] | synthesize [--slug <slug>] [--date <date>]"
---

# Reverse Web

Reverse-engineer a live website into a BA intake document. The session AI (Claude) IS the synthesis engine — no external API needed.

## Invocation

```text
/reverse-web https://example.com
/reverse-web https://example.com --max-pages 50
/reverse-web synthesize --slug my-project --date 260519
```

## Prerequisites

Before running, ensure:
1. Node.js >= 18 installed: `node --version`
2. Playwright chromium installed: `cd skills/reverse-web && npm run setup`

If Playwright is not installed, run setup first:
```bash
cd skills/reverse-web && npm install && npm run setup
```

## Processing Steps

When invoked, Claude MUST follow these steps in order:

### Step 1 — Resolve slug and date

Ask the user for a project slug (or derive from URL hostname):
- Slug: kebab-case name for the project (e.g. `my-app` from `https://my-app.com`)
- Date: today's date in YYMMDD format (e.g. `260519`)
- Output path will be: `plans/{slug}-{date}/01_intake/intake.md`

### Step 2 — Check evidence folder

Check if `evidence/` exists in CWD:
- If NOT exists → proceed to Step 3 (crawl)
- If exists → read `evidence/manifest.json`, check `timestamp` field
  - If older than 24 hours → warn: "Evidence is {N} hours old. Re-crawl for fresh data? (Y/n)"
  - If user says Y → proceed to Step 3
  - If user says N or evidence is fresh → skip to Step 4

### Step 3 — Crawl (if needed)

Run the crawl script via Bash:
```bash
node skills/reverse-web/scripts/crawl.js <url> --consent --max-pages 30 --output ./evidence
```

For `--continue` mode (more pages):
```bash
node skills/reverse-web/scripts/crawl.js <url> --consent --max-pages 30 --output ./evidence --continue
```

Wait for crawl to complete. Verify `evidence/manifest.json` has `"status": "complete"`.

### Step 4 — PII Gate (MANDATORY HITL)

Before reading ANY screenshots, ask the user:

> "Screenshots in `evidence/screenshots/` will be analyzed by Claude vision.
> Please confirm: do the screenshots contain any sensitive PII, credentials,
> confidential business data, or internal-only information that should NOT
> be processed? (Yes = abort / No = proceed)"

- If user says YES → stop. Do not read screenshots. Offer DOM-only synthesis.
- If user says NO → proceed to Step 5.

### Step 5 — Read evidence-index.md FIRST

Read `evidence/evidence-index.md` — this is the agent-facing index that gives
a full picture of all captured evidence without reading 30+ individual files.

From the index, identify:
- Total pages, screenshots, API endpoints
- Which pages have forms (prioritize for DOM deep-read)
- Which pages have tables (prioritize for screenshot read)
- Navigation structure (depth levels)
- API endpoint patterns

### Step 6 — Selective evidence reads

Based on the index findings:

**Always read:**
- `evidence/manifest.json` — metadata (URL, timestamp, config)
- `evidence/sitemap.json` — navigation graph (pages + edges)

**Selectively read (prioritize pages with forms/tables from index):**
- `evidence/dom/{NNN}-{slug}.json` — for pages flagged as having forms or tables
- `evidence/network.ndjson` — for API patterns (read full file, it's compact NDJSON)

**Read screenshots via vision (max 20, prioritize by index flags):**
- Pages with forms → understand field labels, validation hints
- Pages with tables → understand data structures
- Entry page (depth 0) → understand overall purpose and branding
- Use Read tool on PNG files: `evidence/screenshots/{NNN}-{slug}.png`

### Step 7 — Synthesize intake

Read `skills/reverse-web/references/evidence-to-intake-mapping.md` for
detailed section-by-section guidance.

Read `skills/reverse-web/references/synthesis-prompts.md` for section-specific
extraction instructions.

Fill all 8 sections of `templates/intake-form-template.md` using evidence.

### Step 8 — L1 Approval Gate (MANDATORY)

Before writing the intake file, show the user a plan:

```
[/reverse-web] Sẽ tạo file:
  1 | plans/{slug}-{date}/01_intake/intake.md | create | Intake form từ {N} trang, {M} endpoints

Apply? (Y/n):
```

Wait for user confirmation before writing.

### Step 9 — Write intake file

Create directory `plans/{slug}-{date}/01_intake/` if it doesn't exist.
Write the filled intake form to `plans/{slug}-{date}/01_intake/intake.md`.

### Step 10 — Suggest next step

Print:
```
✓ Intake written: plans/{slug}-{date}/01_intake/intake.md

Next step:
  /ba-start backbone --slug {slug} --date {date}
```

Do NOT auto-run the next step. Let the user decide.

## Guardrails Summary

| Guardrail | When | Behavior |
|-----------|------|----------|
| PII gate | Before screenshot read | Ask user — abort if sensitive data present |
| Stale evidence | Evidence > 24h old | Warn + offer re-crawl |
| L1 approval | Before file write | Show plan, wait for Y/n |
| No auto-next | After write | Suggest only, never auto-run |

## References

- `references/evidence-to-intake-mapping.md` — section mapping table
- `references/synthesis-prompts.md` — section-specific extraction guidance
- `templates/intake-form-template.md` — canonical output format
- `core/contract-behavior.md` — BA-kit approval gate conventions
