# Golden: F26 - Reverse SRS Skips Design And Wireframes

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start srs |
| resolved_slug | test-project |
| source_of_truth_artifact | backbone |
| read_scope | core/contract.yaml, core/contract-behavior.md, core/behavior/srs.md, plans/test-project-20260424/00_reverse/reverse-baseline-lock.json, plans/test-project-20260424/00_reverse/reverse-evidence-ledger.md, plans/test-project-20260424/00_reverse/reverse-drift-state.json |
| write_target | plans/test-project-20260424/03_modules/auth-flow/srs.md |
| approval_gate | NONE |
| activation_level | Base |
| fallback_code | NONE |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- Reverse-backed SRS work must gate on reverse evidence, not on `DESIGN.md`.
- Reverse-backed SRS work must verify current reverse drift state before canonical SRS writes.
- Missing wireframe artifacts are not a blocker in reverse mode.
- Future-state UI requests still route through `impact` and the forward lifecycle.
