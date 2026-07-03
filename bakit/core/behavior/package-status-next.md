# Package, Status, And Next Behavior

## Read Scope

- `package` must read `core/contract.yaml`, `core/contract-behavior.md`, and `paths.backbone_index` when present.
- `package` may read `paths.userstories_index`, `paths.usecases_index`, `paths.ascii_screen_index`, `paths.srs_compile_receipt`, `paths.project_memory` compact summary, and `paths.memory_index` for health overview.
- `package` must not read raw source, full intake, `log.md`, `cold/`, `warm/` shards, or full source-of-truth artifacts for discovery when indexes are current.
- `status` and `next` may read `paths.project_home`, project memory header, and `paths.memory_index` activation/freshness. They must not read `log.md` unless `--audit`, or warm/cold shards by default.

## Package Behavior

- `package` is a validation-and-compile step, not a full rebuild.
- Markdown canon artifacts remain the source of truth. Compiled `paths.srs` is a deliverable assembled from module canon files and `paths.srs_compile_receipt`.
- HTML output belongs under `paths.compiled_root`.
- Use indexes first for cross-reference discovery and load full source artifacts only when compilation or validation needs exact content.
- Block package when `paths.srs` exists but `paths.srs_compile_receipt` is missing or stale.
- Block package when UI-backed canon screens are missing required ASCII coverage or the compile receipt is stale.
- Package reads sources through `paths.userstories_index`, `paths.usecases_index`, `paths.ascii_screen_index`, and `paths.srs_compile_receipt`. Missing compiled sections are not errors unless requested in receipt scope.

## Status And Next

- Use one lifecycle status vocabulary: `recommended`, `in-progress`, `completed`, `skipped`, and `not-needed`.
- Do not introduce parallel labels such as `todo`, `doing`, or `done`.
- Treat `paths.project_home` as a BA-facing dashboard for resume/status guidance, not as a source of truth.
- If Project Home conflicts with intake, backbone, or module artifacts, report the conflict and trust the source-of-truth artifact.
- `status` must show canon SRS state explicitly: `paths.userstories_index` count, `paths.usecases_index` count, `paths.ascii_screen_index` count, `paths.srs_spec`, `paths.srs_flows`, `paths.srs_states`, `paths.srs_erd`, `paths.srs`, and `paths.srs_compile_receipt` scope.
- `status` must show shared shell state separately: `paths.design_doc`, `paths.shared_shell_contract`, and `paths.shared_shell_index`.
- `status` must show shared artifact health: `paths.shared_traceability`, `paths.shared_staleness`, `paths.shared_definitions`.
- `next` must recommend `ba-start srs` when canon sources, `userstories/index.md`, or the compile receipt are missing/stale.
- `next` must not recommend legacy `wireframes`; missing or stale ASCII coverage is fixed by `ba-start srs`.
- `next` state machine: no intake → intake; no backbone → backbone; no `userstories/index.md` → stories; SRS source set missing → srs; receipt missing/stale for requested scope → srs compile; package missing → package; else status.
- Figma sync readiness is downstream-only: current canon + current compile receipt + shared shell + `DESIGN.md`. Any Figma mismatch belongs in `paths.figma_mismatch_report`, not in canon files.
- `next` recommends the next command and does not mutate artifacts.
