# First-Audit Workflow

Detailed step-by-step for first-time audit when no existing `audit-report.md` is found.

## Preconditions

- Project root resolved and verified to exist
- `contract.yaml` loaded (paths resolved)
- `references/audit-rules.md` loaded (artifact rules)
- `template/audit-report-template.md` loaded (output format)

## Step 0: Choose Audit Strategy (Batching)

Estimate context budget before starting. Count files and modules from manifest:

| Project Size | Strategy | Context per batch |
|---|---|---|
| ≤60 files, ≤2 modules | **Single-agent**: audit all files sequentially | ~45% of 200K |
| >60 files or >2 modules | **Multi-agent batched**: spawn sub-agents per module | ~45% each, fresh context |

### 0a: Single-Agent Strategy (Small Projects)

Proceed with Steps 1–7 inline. All files audited in one session. Findings appended incrementally. No delegation needed.

### 0b: Multi-Agent Batched Strategy (Large Projects)

**Orchestrator (main agent)** handles:
1. Step 1: Build file manifest for all files
2. Step 2: Build on-disk ID index for ALL files (one Bash, zero context)
3. Step 3A: Audit system-level files (01_intake, 02_backbone, design doc) → append findings
4. **For each module**: Spawn a sub-agent to audit that module's files. Each sub-agent gets:
   - Module path and file list
   - Path to on-disk ID index (`shared/.audit-id-index.txt`)
   - Output: append findings to `shared/.audit-module-{module_slug}.md`
   - Fresh context window (~200K tokens)
5. Step 4: Orphan detection on combined index (Bash, zero context)
6. Merge: Concatenate system findings + all module finding files into final report, prepend summary

**Sub-agent prompt template** (spawn per module):
```
Audit module: {module_slug}
Module path: {module_root}
ID index: {project_root}/shared/.audit-id-index.txt
Output: {project_root}/shared/.audit-module-{module_slug}.md

For each file in module:
- Frontmatter check: Read first 40 lines (offset=0, limit=40)
- Section check: Read TOC (80 lines) + Grep template headings
- Cross-ref check: Grep file for IDs, query disk index via `grep -c "ID"` on .audit-id-index.txt
- Append findings to output file immediately (incremental)

Rules: never read files >10KB fully. Never load index into context. Use offset+limit.
```

### 0c: Final Merge

After all sub-agents complete:
```bash
cat {project_root}/shared/.audit-module-*.md >> {project_root}/shared/audit-report.md
```
Then prepend frontmatter + summary + fix commands. Clean up temp module files.

## Step 1: Build File Manifest

Scan project root to discover all artifacts. For each contract.yaml path key in core lifecycle (P0), resolve with `{slug}`, `{date}`, and `{module_slug}` placeholders.

### 1a: System-Level Artifacts

Scan in order:
1. `01_intake/intake.md`
2. `01_intake/plan.md`
3. `PROJECT-HOME.md`
4. `02_backbone/backbone.md`
5. `02_backbone/backbone-index.md`
6. `02_backbone/common-rules.md` (if exists)
7. `02_backbone/message-list.md` (if exists)
8. `02_backbone/shared-rule-message-index.md` (if exists)
9. `02_backbone/shared-shell-contract.md` (if exists)
10. `02_backbone/shared-shell-index.md` (if exists)
11. `02_backbone/project-memory.md` (if exists)

### 1b: Design Doc

- `designs/{slug}/DESIGN.md` (if exists)

### 1c: Module Artifacts

For each `03_modules/{module_slug}/` directory found:
1. `MODULE-HOME.md` (if exists)
2. `frd.md` (if exists)
3. `srs/spec.md` (if exists)
4. `srs/flows.md` (if exists)
5. `srs/states.md` (if exists)
6. `srs/erd.md` (if exists)
7. `srs.md` (compiled, if exists)
8. `screen-field-contract.yaml` (if exists)
9. `userstories/index.md` + all `us-*.md` files
10. `usecases/index.md` + all `uc-*.md` files
11. `ascii-screen/index.md` + all `*.md` files (except `.pen`)
12. `brainstorms/index.md` + all `*.md` files (if brainstorm root exists)

Skip: `.pen` files, `tool-lanes/` directory, `figma-sync/` directory, `qc-review/` directory (P2).

### 1d: Compiled & Shared

1. `04_compiled/compiled-frd.html` (if exists)
2. `04_compiled/compiled-srs.html` (if exists)
3. Per-module `04_compiled/{module_slug}/compiled-srs.html` (if exists)
4. `shared/traceability.md` (if exists)
5. `shared/staleness.md` (if exists)
6. `shared/definitions.md` (if exists)

### 1e: Changes & Impacts

If `changes/` or `impacts/` directories exist under project root:
1. `changes/CR-*.md` files
2. `impacts/CR-*-impact.md` files

If these directories do not exist → skip silently (no finding emitted). These artifacts are optional extensions.

### Empty Module Handling

If `03_modules/{module_slug}/` exists but has no artifact files → emit one Info finding: "Module '{module_slug}' directory exists but contains no artifacts."

## Step 2: First Pass — Build On-Disk ID Index (Zero Context)

**DO NOT load ID definitions into chat context.** Write them to disk and query from disk. The index file path: `{project_root}/shared/.audit-id-index.txt`.

### 2a: Write ID Index to Disk (Bash, Zero Context)

Run a single Bash command to extract all ID definitions to a disk file:

```bash
grep -rnoE "(FR-\w+-\d{2,3}|NFR-\w+-\d{2,3}|BR-\w+-\d{2,3}|E-\w+-\d{2,3}|UC-\w+-[\w-]+|US-\w+-\d{2,3}|CAP-\w+-\d{2}|BO-\w+-\d{2}|CR-\d{8}-\d{3}|MSG-(?:ERR|WRN|SUC|INF)-\d{2}|CR-(?:DIS|BEH|VAL|MIX)-\d{2})" \
  {project_root}/ > {project_root}/shared/.audit-id-index.txt
```

The Bash output is just exit code (0/1) — zero context load. The index file contains lines like:
```
path/to/file.md:42:FR-admin-001
path/to/file.md:15:UC-admin-login
```

Then get a count for reporting: `wc -l < {project_root}/shared/.audit-id-index.txt` → single number.

### 2b: Discovery — Files With IDs (Grep, Minimal Output)

Use Grep with `output_mode: files_with_matches` to list which files contain IDs:

```
Grep pattern: same ID regex as 2a
output_mode: files_with_matches
path: {project_root}
```

Output is file paths only (~1-2KB for large projects) — no line content. This tells which files define/reference IDs without loading the IDs themselves.

**For files <3KB**: Read fully to capture frontmatter `id:` and `story_id:` fields that regex may miss.

### 2c: Collect Wikilinks & Markdown Links (files_with_matches First)

1. **Wikilinks discovery**: Grep `\[\[` with `files_with_matches` → list of files with wikilinks (~500B)
2. **Wikilinks content**: Grep `\[\[([^\]]+)\]\]` with `output_mode: content` on ONLY files from step 1
3. **Markdown links discovery**: Grep `\[[^]]+\]\(` with `files_with_matches` → list
4. **Markdown links content**: Grep `\[([^\]]+)\]\(([^)]+)\)` on ONLY files with links
5. **Frontmatter links**: Grep `^links:` in first 30 lines of each file

### 2d: Build Resolved Link Map

For each extracted link path:
1. Resolve relative to source file directory
2. Check against file manifest (from Step 1) — does target exist on disk?
3. Flag broken links immediately (Blocking for wikilinks, Warning for markdown links)

### Output of Step 2

After disk-index pass, produce:
- `{project_root}/shared/.audit-id-index.txt` — on-disk ID index (query from Step 3c)
- `{file → [link_path, resolved_target, exists?]}` link map (in context, compact)
- `{file → index_entries}` for index files (in context, compact)

## Step 3: Second Pass — Audit Each File (Output-Limited)

For each file in manifest, run three check groups. **Apply output-limiting rules from SKILL.md Boundaries at every read.**

### 3a: Frontmatter Check (Read: first 40 lines only)

1. Read file with `offset=0, limit=40`. Frontmatter is always within first 20-30 lines.
2. Parse YAML frontmatter (between opening `---` and closing `---`).
3. If no `---` within first 40 lines → read next 40 lines (`offset=40, limit=40`). If still no frontmatter → Blocking.
4. Run standard checks: required fields, `type` value, naming convention per `audit-rules.md`.
5. Do NOT read rest of file.

### 3b: Template Section Check (Read: TOC only, Grep for headings)

**For user_facing artifacts with a template reference:**

1. Grep template file (`templates/{template_name}`) for `^## ` headings → expected section set.
2. Read artifact TOC: `offset=0, limit=80` → parse `## ` headings → actual section set.
3. If artifact >80 lines and more headings expected, Grep artifact for `^## ` to get full heading list.
4. Compare expected vs actual:
   - Template section missing → Blocking
   - Extra section → Info
5. Only read the full section body when a discrepancy requires content-level verification (e.g., section exists but appears empty).

**Skip for**: HTML files, machine_facing artifacts without templates, agent_facing artifacts.

### 3c: Cross-Reference Check (Query On-Disk Index, Per-File)

Leverage the on-disk ID index from Step 2a. Do NOT re-read files. Do NOT load the full index into context.

**For each file being audited:**

1. **Extract this file's ID references** via Grep (`output_mode: content`) — only IDs referenced in this one file. Per-file output is small (~5-15 lines).
2. **For each referenced ID**, query the on-disk index:
   ```bash
   grep -c "ID_STRING" {project_root}/shared/.audit-id-index.txt
   ```
   - Result `> 0` → ID defined somewhere → OK
   - Result `= 0` → Warning: "ID '{id}' referenced but not defined in any file"
3. **Broken links**: Already resolved in Step 2d → emit findings from link map.
4. **Index file entries**: Already parsed in Step 2d → check each `[label](path)` target exists.
5. **Orphan IDs** (deferred to Step 4): Run once after all files scanned via Bash on index file.

**Only read file content when**: A Grep match is ambiguous (e.g., ID appears in code block, not as reference) — then read the specific line range around the match to disambiguate.

## Step 4: Orphan ID Detection (Bash on Disk Index, Zero Context)

After all files audited in Step 3, detect IDs defined but never cross-referenced using the on-disk index:

```bash
# Extract all unique IDs from index, check if referenced more than once (definition only = orphan)
cut -d: -f3 {project_root}/shared/.audit-id-index.txt | sort | uniq -c | awk '$1 == 1 {print $2}'
```

This runs entirely in Bash. Only the orphan ID list shows in context — typically <20 lines even for large projects. Each orphan → Info finding.

Alternative approach if IDs defined with colon-prefix (e.g., `FR-admin-001:`):
```bash
grep -oE "PATTERN" {project_root}/shared/.audit-id-index.txt | sort | uniq -c | awk '$1 == 1 {print $2}'
```

## Step 5: Classify & Assign Finding IDs

For each finding:
1. Determine severity: Blocking / Warning / Info per `audit-rules.md`
2. Generate content-hash ID: `{Prefix}-{first 6 chars of SHA-256("{file_path}:{check_type}:{location_key}")}`
   - `check_type`: `frontmatter`, `section`, `crossref`, `naming`, `id_orphan`
   - `location_key`: section name, field name, link path, or ID string
3. Generate hash using available tools (Bash: `echo -n "string" | shasum -a 256 | cut -c1-6`)

## Step 6: Write Report (Incremental)

**DO NOT accumulate all findings in memory.** Write incrementally — append findings per file as they are discovered during Step 3, then write frontmatter + summary at end.

### 6a: Initialize Report File

Before starting Step 3 (per-file audit), create the report file with a placeholder:

```
Write paths.audit_report: "# Audit Report: {slug}\n\n<!-- Findings appended incrementally -->\n"
```

### 6b: Append Findings Per File

After auditing each file in Step 3, immediately append findings to the report:

```
Edit paths.audit_report (append): findings for {file_path}
```

Group findings by severity within each file's section. Use format from `template/audit-report-template.md`. Findings are short (1-2 lines each) — append cost is minimal.

### 6c: Finalize Report

After all files audited and findings appended:
1. Prepend frontmatter: `type: audit-report`, `audit_version: 1`, `previous_audit: none`, counts
2. Prepend summary table
3. Append `## Fix Commands` section — Map Blocking + Warning findings to commands per `references/audit-rules.md` Finding-to-Fix-Command Mapping. Generate commands per finding as they are appended in 6b, not all at end.
4. Append footer: `*Audit generated by /ba-content-audit --slug {slug} on {iso_timestamp}*`

**Fix Commands generation**: Produce the fix command for each Blocking/Warning finding in 6b (alongside the finding itself). Append to the relevant Fix Commands subsection (Direct Edit / Skill-Based / Manual Actions) in a separate section at the bottom of the report. This avoids re-holding all B+W findings at the end.

## Step 7: Print Chat Summary

```
✅ Audit complete: {slug}
   Blocking: {N} | Warning: {M} | Info: {K}
   Report: {report_path}

🔴 Blocking:
   - {id}: {file} {location} — {description}
   ... (max 5, then "+{remaining} more")

🟡 Top Warnings:
   - {id}: {file} {location} — {description}
   ... (max 5, then "+{remaining} more")

🔵 Info: {K} findings (see report for details)
```
