# Reverse Behavior

## Read Scope

- Must read: `core/contract.yaml`, `core/contract-behavior.md`, and the active reverse-lane artifact required by the current command.
- May read: `paths.reverse_index` header, `paths.reverse_drift_state`, `paths.reverse_evidence_ledger` summary fields, and allowlisted files named in `paths.reverse_read_manifest`.
- Must not read: full backbone, full stories, full SRS, memory shards, `log.md`, or any file outside `paths.reverse_read_manifest` unless the runtime emits `READ_ESCALATION`.

## Baseline And Truth

- Reverse mode is evidence-only. `00_reverse/` artifacts are never canonical source of truth.
- All as-built claims are bound to `documented_commit` in `paths.reverse_baseline_lock`.
- `paths.reverse_baseline_lock` must carry `documented_commit`, `scan_timestamp`, `focus_selection`, and `locked_files`.
- Treat legacy field names `locked_at` and `focus_areas` as compatibility aliases only. New writes must use `scan_timestamp` and `focus_selection`.

## Hard Guardrails

- `FOCUS_SELECTION_REQUIRED`: do not scan or write reverse artifacts before the user explicitly confirms focus selection.
- `REVERSE_REFRESH_REQUIRED`: block when the baseline/index is stale, the documented commit is gone, or locked files drifted.
- `REVERSE_SOURCE_ONLY_V1`: block when reverse flows would require app execution, runtime probes, DB reads, or live endpoint checks.
- `REVERSE_TRACE_COVERAGE_REQUIRED`: block promotion to canonical artifacts when promoted claims lack ledger trace coverage.
- `REVERSE_READ_SCOPE_ESCALATION`: emit when a reverse command needs to reopen a file outside `paths.reverse_read_manifest`.

## Reverse SRS Carveout

- When a reverse lane is active, reverse-backed SRS work must gate on reverse evidence, not on `paths.design_doc` or wireframe artifacts.
- Treat `wireframes` as `not-applicable` for reverse mode.
- For reverse-backed SRS sections, require:
  - a valid `paths.reverse_baseline_lock`
  - current reverse drift state
  - reverse evidence or focused excerpts for the module being documented
  - traceable claims before canonical promotion
- If the requested change is future-state rather than as-built, route back to `impact` or the forward lifecycle instead of silently using reverse evidence.
