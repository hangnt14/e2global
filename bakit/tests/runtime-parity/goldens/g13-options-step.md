# Golden: F13 - Explicit ba-start options Command

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start options |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260424/01_intake/intake.md |
| read_scope | plans/test-project-20260424/01_intake/intake.md, plans/test-project-20260424/01_intake/plan.md |
| write_target | plans/test-project-20260424/01_intake/options/index.md |
| approval_gate | NOT_REQUIRED |
| activation_level | Base |
| fallback_code | NONE |
| option_artifact_count | 1-3 |
| comparison_rule | comparison.md only when more than one viable option exists |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- Options generation is a pre-backbone step and must not pull in `02_backbone/` artifacts.
- `plan.md` is the decision ledger that opens the optioning cycle; it does not replace `intake.md` as source input.
