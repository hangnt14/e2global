# Golden: F20 - next Recommends Canonical Step Despite PROJECT-HOME Conflict

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start options |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260424/01_intake/plan.md |
| write_target | NONE |
| approval_gate | NOT_REQUIRED |
| activation_level | Base |
| fallback_code | NONE |
| visible_warning | PROJECT_HOME_CONFLICT |
| recommendation_summary | Recommend running options before backbone |
| read_scope | plans/test-project-20260424/PROJECT-HOME.md, plans/test-project-20260424/02_backbone/project-memory.md, plans/test-project-20260424/02_backbone/project-memory/index.md |

## Guardrail Preflight

| Field | Expected Value |
| --- | --- |
| status | ok |
| command | next |
| resolved_slug | test-project |
| guardrail_mode | canonical-state-first |
| project_home_override | true |
| allow_reads_includes | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/PROJECT-HOME.md, plans/test-project-20260424/02_backbone/project-memory.md, plans/test-project-20260424/02_backbone/project-memory/index.md |
| message | GUARDRAIL: cmd=next mode=canonical-state-first allow=contract.yaml,index.md |

## Guardrail Audit

| Field | Expected Value |
| --- | --- |
| status | pass |
| actual_reads_includes | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/PROJECT-HOME.md |
| actual_reads_excludes | plans/test-project-20260424/01_intake/intake.md, plans/test-project-20260424/01_intake/plan.md, plans/test-project-20260424/02_backbone/project-memory/log.md |
| violations.count | 0 |
| warnings.count | 0 |
| message | GUARDRAIL_AUDIT_PASS: cmd=next |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- `PROJECT-HOME.md` may still be read, but it is demoted to dashboard context while preflight carries the canonical next-step conclusion.
