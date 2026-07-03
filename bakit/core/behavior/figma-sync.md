# Figma Sync Behavior

## Scope

`figma-sync` is a downstream visual-consumer lane. It may read approved SRS canon files and interact with Figma MCP, but it never owns BA requirements.

## Read Scope

- Must read `core/contract.yaml` and `core/contract-behavior.md`.
- Must read `paths.ascii_screen_index` before individual screen files.
- May read `paths.ascii_screen_root`, `paths.design_doc`, `paths.shared_shell_contract`, `paths.shared_shell_index`, `paths.shared_definitions`, `paths.shared_traceability`, and `paths.shared_rule_message_index`.
- May read `paths.srs_compile_receipt` to confirm compiled SRS freshness.
- Must not read or use legacy wireframe pack artifacts as the visual source when canon screen files exist.

## Write Scope

- May write only `paths.figma_sync_report` and `paths.figma_mismatch_report`.
- May mutate Figma only through the configured Figma MCP tool after the user has explicitly asked for sync.
- Must not write `paths.srs`, `paths.ascii_screen_root`, `paths.usecases_root`, `paths.userstories_root`, `paths.shared_shell_contract`, or `paths.design_doc`.

## Guardrails

- If `paths.srs_compile_receipt` is missing or stale, block and recommend `ba-start srs --slug <slug> --module <module_slug>`.
- If a screen has `figma_sync_eligible: false`, skip it and record the reason in the sync report.
- If a screen has L3 state rows without ASCII coverage or Figma frame mapping, block that screen and record it in the mismatch report.
- If Figma readback does not match the screen canon state/frame map, do not patch canon silently. Write a mismatch report and ask the BA to update canon first.

## Output

- `figma-sync/figma-sync-report.md`: what was attempted, skipped, created, updated, and verified.
- `figma-sync/figma-mismatch-report.md`: canon/Figma differences that require BA or designer decision.
