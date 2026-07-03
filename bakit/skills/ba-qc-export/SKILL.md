---
name: ba-qc-export
description: Export BA-kit module canon into QC-kit per-UC input format. One-way bridge — BA-kit canon remains source of truth. Output goes to 04_compiled/qc-kit/docs/BA/ by default.
argument-hint: "--slug <slug> --date <YYMMDD-HHmm> --module <module_slug> [--external-output <dir>] [--usecase-list]"
---

# BA QC Export

Use this skill when the user asks to export BA artifacts for QC-kit handoff, prepare QC input, or send requirements to QC review.

## Invocation

```text
/ba-qc-export --slug warehouse-rfp --date 260529-2100 --module payment
/ba-qc-export --slug warehouse-rfp --date 260529-2100 --module payment --usecase-list
/ba-qc-export --slug warehouse-rfp --date 260529-2100 --module payment --external-output ../qc-kit
/ba-do xuất QC cho module payment của dự án warehouse-rfp
/ba-do export to QC for the auth module
```

## Required Read Order

1. Read `~/.claude/core/contract.yaml`. If missing, fall back to `core/contract.yaml` from the BA-kit repo root.
2. Read `~/.claude/core/contract-behavior.md`. If missing, fall back.
3. Read `~/.claude/ba-kit/docs/ba-qc-export-bridge-note.md` for design context. If missing, read `docs/ba-qc-export-bridge-note.md` from the BA-kit repo root.
4. Resolve slug, date, and module from PROJECT-HOME.md, MODULE-HOME.md, or explicit arguments.
5. If slug/date not provided, read `PROJECT-HOME.md` in the current plan root to auto-resolve.

## Source Inputs

Required (read from BA-kit canon):

- `plans/{slug}-{date}/03_modules/{module_slug}/usecases/uc-*.md`
- `plans/{slug}-{date}/03_modules/{module_slug}/ascii-screen/*.md`
- `plans/{slug}-{date}/03_modules/{module_slug}/userstories/us-*.md`
- `plans/{slug}-{date}/02_backbone/common-rules.md`
- `plans/{slug}-{date}/02_backbone/message-list.md`

Optional:

- `plans/{slug}-{date}/03_modules/{module_slug}/srs.md`
- `plans/{slug}-{date}/03_modules/{module_slug}/srs/spec.md`
- `plans/{slug}-{date}/02_backbone/backbone.md`
- PNG assets next to screen files

## Write Scope

Allowed writes:

- `plans/{slug}-{date}/04_compiled/qc-kit/` (all generated output)
- External directory specified via `--external-output` (explicit opt-in only)

Forbidden writes:

- `plans/{slug}-{date}/03_modules/{module_slug}/usecases/`
- `plans/{slug}-{date}/03_modules/{module_slug}/ascii-screen/`
- `plans/{slug}-{date}/03_modules/{module_slug}/userstories/`
- `plans/{slug}-{date}/03_modules/{module_slug}/srs/`
- `plans/{slug}-{date}/02_backbone/`

Before writing inside the BA-kit repo, validate scope with:

```bash
ba-kit check-write-scope --command qc-export <target-path>
```

External output (`--external-output`) bypasses this check — the user explicitly opts into writing outside
the repo. The exporter still refuses to mutate canon paths regardless of output target.

## Process

1. Validate slug, date, and module are resolved. Ask user for missing values.
2. Run the export command:

```bash
ba-kit qc-export --slug <slug> --date <date> --module <module> [--external-output <dir>] [--usecase-list]
```

3. Review the output summary printed by the exporter for:
   - Number of UCs exported
   - Resolved vs unresolved references
   - Output paths written

4. Report a compact summary to the user:
   - Resolved project/module
   - UCs exported with counts
   - Any unresolved CR-/MSG-/BR- references and which UCs they appear in
   - Output directory path
   - Reminder: "Apply all corrections to BA-kit canon, then re-export. Do not edit generated QC output as the business source."

## Output

After the run, report:

- resolved slug, date, module
- UCs processed
- resolved reference count vs unresolved
- unresolved reference list (code + source UC)
- output root path
- usecase-list.md path (if `--usecase-list` was used)

## Expected Output Directory Structure

The exporter generates monolithic files per Use Case rather than mirroring the raw multi-file source structure. The expected output structure in the compiled directory is:

```text
plans/{slug}-{date}/04_compiled/qc-kit/
  qc-export-summary.json        <-- Export metadata summary (JSON)
  docs/BA/
    Common rule/
      common-rules.md            <-- Exported common rule registry
      message-list.md            <-- Exported common message list
    {module_slug}/
      UC-{usecase_slug}.md       <-- Monolithic markdown file containing UC details,
                                     inlined screen specs, ACs, and referenced rules
      UC-{usecase_slug}-screens/
        *.png                    <-- Supplementary PNG assets (if any)
      usecase-list.md            <-- Optional UC list index (if --usecase-list is used)
```

**CRITICAL:** Under no circumstances does `qc-export` generate separate `usecases/`, `screens/`, or `userstories/` folders containing separate markdown files. Screens, user stories, and rules are always compiled and inlined into the single `UC-{usecase_slug}.md` file for that UC.


## Stop Conditions

- Module root not found at `plans/{slug}-{date}/03_modules/{module_slug}/`
- No UC files found in `usecases/` directory
- Missing `common-rules.md` or `message-list.md` in backbone (warn, continue with empty registries)
- Write scope check fails for any output path
- Export command exits with non-zero status

## Non-Goals

- This skill does NOT auto-run after `package` or any lifecycle step. It is manual on-demand.
- This skill does NOT modify BA-kit canon. All business corrections go through BA source artifacts first.
- This skill does NOT build QC-kit project config, context master, site map, or dashboard. Those are QC-kit's responsibility.
- This skill does NOT generate PNG designs. BA places designs manually in screen folders.
