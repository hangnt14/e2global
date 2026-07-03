---
name: ba-content-audit
description: Cross-artifact format and cross-reference consistency audit for BA-kit projects. Read-only — never mutates artifacts.
argument-hint: "--slug <slug> [--date <date>]"
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# BA Content Audit

Read-only cross-artifact audit for BA-kit lifecycle projects. Scans all artifacts (intake → backbone → modules → compiled → shared), reports format compliance issues and cross-reference integrity breaks. Output goes to `plans/{slug}-{date}/shared/audit-report.md`.

## Invocation

```text
/ba-content-audit --slug warehouse-rfp
/ba-content-audit --slug warehouse-rfp --date 260611-0900
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--slug <slug>` | Yes | Project slug (e.g., `warehouse-rfp`) |
| `--date <date>` | No | Project date token (`YYMMDD-HHmm`). If omitted: glob `plans/{slug}-*`; single match → use; multiple matches → `AskUserQuestion`; zero → error |

## Execution Context

Read `core/contract.yaml` for path resolution and `core/contract-behavior.md` for shared behavior rules.

Read `references/audit-rules.md` for per-artifact-type format rules, severity classification, and cross-reference resolution logic.

Read `template/audit-report-template.md` for output format.

## Process

### Step 1: Resolve Project Path

1. Parse `--slug` (mandatory) and optional `--date` from `$ARGUMENTS`.
2. Read `core/contract.yaml` → resolve `paths.project_root` with `{slug}` and `{date}`.
3. If `--date` provided → use exact path.
4. If `--date` omitted:
   - Glob `plans/{slug}-*` for matching directories.
   - Single match → auto-select.
   - Multiple matches → `AskUserQuestion` to let user pick.
   - Zero matches → error: "No project found for slug '{slug}'".
5. Verify project root exists on disk. If not → Blocking error, stop.

### Step 2: Route to Audit Flow

1. Read `core/contract.yaml` → resolve `paths.audit_report` → full path to expected report.
2. Check if `audit-report.md` exists at that path.
3. **Exists** → Re-audit flow (see `references/re-audit-workflow.md`).
4. **Not found** → First-audit flow (see `references/first-audit-workflow.md`).

### Step 3: Execute Audit Workflow

Detailed steps in the referenced workflow file. Overview:

**Strategy selection** (both flows, `first-audit-workflow.md` Step 0):
- ≤60 files, ≤2 modules → single-agent sequential audit
- >60 files or >2 modules → multi-agent batched: orchestrator handles system files + index, spawns sub-agent per module (fresh context each), merges results

**First audit** (`references/first-audit-workflow.md`):
- Scan artifacts in lifecycle order
- Per-file: frontmatter check, mandatory sections check, cross-reference check
- Classify findings as Blocking / Warning / Info per `references/audit-rules.md`
- Write report per `template/audit-report-template.md`

**Re-audit** (`references/re-audit-workflow.md`):
- Load existing report (frontmatter + Grep for IDs only, not full read)
- Re-scan all artifacts (batched if large project)
- Compare old vs new findings using content-hash IDs
- Flag `[NEW]`, bump severity on persistent, move resolved to "Resolved" section
- Overwrite report preserving trace

### Step 4: Output

1. Write audit report to `paths.audit_report` path (resolved from contract.yaml).
2. Print compact chat summary:
   - Blocking count + top 3-5 Blocking findings
   - Warning count + top 3-5 Warning findings
   - Info count
   - Report file path
   - "Fix commands: see `## Fix Commands` in report — copy-paste per finding."

## Boundaries

- **Read-only**: Never mutate any artifact file.
- **No external calls**: No MCP, no API, no network.
- **.pen files skipped**: Pencil MCP-managed, encrypted — skip without reading.
- **Empty modules**: Skip with Info finding.
- **Output-limiting strategy**:
  - ID collection: Write to disk index via Bash (`grep -rE > .audit-id-index.txt`), zero context load. Use `files_with_matches` for discovery. Never load full ID map into context.
  - Cross-reference check: Per-file Grep for IDs, then query on-disk index (`grep -c "ID" .audit-id-index.txt`). One line result per check.
  - Orphan detection: Bash `sort | uniq -c | awk` on disk index, zero context.
  - Frontmatter check: Read first 40 lines only (`offset=0, limit=40`) — frontmatter always at top.
  - Template section check: Read TOC of template + artifact (first 80 lines) to get `##` headings; compare headings. Grep for missing sections if discrepancy flagged.
  - Wikilink/link collection: `files_with_matches` first, then content Grep only for files with links.
  - Full content read: Only when frontmatter/Grep/TOC indicate a finding requiring content-level verification. Even then, use `offset`+`limit` on files >200 lines.
  - Files >10KB: Never read fully. Always use offset+limit (<5KB per read) or Grep.
  - Never re-read same file section. Cross-reference findings to prior reads.
  - Report writing: Append findings per file incrementally. Initialize report with placeholder, append each file's findings as discovered, prepend frontmatter + summary at end. Never accumulate all findings in memory.
  - Re-audit existing report: Read frontmatter only (first 50 lines), Grep for finding IDs. Do NOT read full report.
  - Temp index cleanup: Remove `.audit-id-index.txt` after report finalized.
- **P2 artifacts deferred**: Tool-lanes, reverse, QC, memory-deep — not audited in v1.

## References

- `references/audit-rules.md` — Per-artifact-type format rules + cross-reference resolution
- `references/first-audit-workflow.md` — First-audit detailed steps
- `references/re-audit-workflow.md` — Re-audit detailed steps
- `template/audit-report-template.md` — Report output format
- `core/contract.yaml` — Path definitions
- `core/contract-behavior.md` — Shared behavior rules
