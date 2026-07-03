# Golden: F14 - ba-next Recommends options After Intake Recommendation

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start options |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260424/01_intake/plan.md |
| read_scope | plans/test-project-20260424/01_intake/intake.md, plans/test-project-20260424/01_intake/plan.md |
| write_target | NONE |
| approval_gate | NOT_REQUIRED |
| activation_level | Base |
| fallback_code | NONE |
| recommendation_summary | Recommend running options before backbone |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- `ba-start next` is inspection only here; it must emit the next exact command and leave artifacts unchanged.
- When `options status` is `recommended`, the next safe command is `ba-start options --slug test-project`.
