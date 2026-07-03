# Re-Audit Workflow

Detailed step-by-step for re-audit when an existing `audit-report.md` is found.

## Preconditions

- Project root resolved and verified to exist
- Existing `audit-report.md` found at `paths.audit_report` path
- `contract.yaml` loaded (paths resolved)
- `references/audit-rules.md` loaded (artifact rules)
- `template/audit-report-template.md` loaded (output format)

## Step 0: Choose Audit Strategy (Same as First-Audit)

Apply same batching decision as `first-audit-workflow.md` Step 0:
- ≤60 files, ≤2 modules → single-agent re-audit
- >60 files or >2 modules → multi-agent batched re-audit (spawn sub-agents per module)

For batched re-audit: the orchestrator loads existing report IDs (Grep for finding IDs only, not full report), then spawns sub-agents per module with the old ID set for comparison. Sub-agents flag `[NEW]` / `Persistent` / `Resolved` in their module finding files. Orchestrator merges at end.

## Step 1: Load Existing Report (Output-Limited)

**DO NOT read the full report.** Use output-limiting strategy to extract metadata + finding IDs only.

1. Read frontmatter only: `offset=0, limit=50` on existing `audit-report.md`.
   - Parse: `audit_version`, `previous_audit`, `total_findings`, `blocking`, `warning`, `info`.
2. Grep for finding IDs to build `old_finding_ids` set:
   - Pattern: `^\| (B|W|I)-[a-f0-9]{6} \|` — matches all finding rows in tables.
   - Store `{id, severity}` pairs from Grep output.
3. Grep for finding descriptions ONLY when needed during comparison (Step 3) — read the specific line range around a matched ID, not the full report.
4. Do NOT read old finding descriptions, locations, or suggested fixes into context unless comparison requires them (e.g., severity bump from Warning to Blocking needs old severity).

## Step 2: Re-Scan All Artifacts (Output-Limited)

Run the full first-audit scan (Steps 1–4 from `first-audit-workflow.md`) with all output-limiting rules in effect:
1. Build file manifest
2. First pass: On-disk ID index via Bash (zero context), `files_with_matches` for discovery
3. Second pass: audit each file with offset+limit reads (frontmatter: 40 lines, sections: TOC + Grep, cross-refs: query on-disk index via `grep -c`)
4. Orphan ID detection via Bash on disk index

Findings appended incrementally to report per file (see Step 4b). Do NOT hold all findings in memory.

## Step 3: Compare & Classify

For each new finding:
- **ID exists in old set** → **Persistent** finding
  - If old severity was Warning, bump to Blocking (repeated issue) → annotate "Persistent (was Warning in v{N})"
  - If old severity was Blocking, keep Blocking → annotate "Persistent (was Blocking in v{N})"
  - If old severity was Info, keep Info → annotate "Persistent (was Info in v{N})"
- **ID NOT in old set** → **`[NEW]`** finding
  - Flag in finding row: `[NEW] B-{hash}`
  - Standard severity per audit-rules.md

For each old finding NOT in new set:
- **Finding resolved** → Move to "Resolved" section of report
  - Record: `{id, original_location, original_severity, resolution: "No longer detected — likely fixed"}`

## Step 4: Assemble Report (Incremental)

**Use same incremental strategy as first-audit Step 6.** Do NOT accumulate all findings in memory before writing.

### 4a: Initialize with Delta Header

Before re-scanning, create report file with delta metadata header (version N+1, previous timestamp).

### 4b: Append Per File During Re-Scan

As Step 2 re-scans each file, immediately append findings to report. Flag `[NEW]` or `Persistent` per Step 3 comparison. Append fix commands alongside each Blocking/Warning finding.

### 4c: Finalize

After all files re-scanned:
1. Collect resolved findings (old IDs not in new set) → append `## Resolved` section
2. Prepend final frontmatter with counts
3. Prepend summary + delta summary tables
4. Append footer with timestamp

## Step 5: Print Chat Summary

```
🔄 Re-audit complete: {slug} (v{new_version})
   [NEW]: {N} | Persistent: {M} | Resolved: {K}
   Blocking: {B} | Warning: {W} | Info: {I}
   Report: {report_path}

🔴 [NEW] Blocking:
   - {id}: {file} {location} — {description}
   ... (max 5)

🔄 Persistent Blocking:
   - {id}: {file} {location} — {description}
   ... (max 5)

🟡 Top [NEW] Warnings:
   ... (max 5)

✅ Resolved: {K} findings (see report for details)
```
