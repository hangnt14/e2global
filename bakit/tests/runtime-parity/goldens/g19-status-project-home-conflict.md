# Golden: F19 - status Ignores PROJECT-HOME Conflict

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start status |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260424/01_intake/plan.md |
| write_target | NONE |
| approval_gate | NOT_REQUIRED |
| activation_level | Base |
| fallback_code | NONE |
| visible_warning | PROJECT_HOME_CONFLICT |
| canonical_state_summary | options still recommended from plan.md |
| read_scope | plans/test-project-20260424/PROJECT-HOME.md, plans/test-project-20260424/02_backbone/project-memory.md, plans/test-project-20260424/02_backbone/project-memory/index.md |

## Guardrail Preflight

| Field | Expected Value |
| --- | --- |
| status | ok |
| command | status |
| resolved_slug | test-project |
| guardrail_mode | canonical-state-first |
| project_home_override | true |
| allow_reads_includes | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/PROJECT-HOME.md, plans/test-project-20260424/02_backbone/project-memory.md, plans/test-project-20260424/02_backbone/project-memory/index.md |
| message | GUARDRAIL: cmd=status mode=canonical-state-first allow=contract.yaml,index.md |

## Guardrail Audit

| Field | Expected Value |
| --- | --- |
| status | pass |
| actual_reads_includes | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/PROJECT-HOME.md |
| actual_reads_excludes | plans/test-project-20260424/01_intake/intake.md, plans/test-project-20260424/01_intake/plan.md, plans/test-project-20260424/02_backbone/project-memory/log.md |
| violations.count | 0 |
| warnings.count | 0 |
| message | GUARDRAIL_AUDIT_PASS: cmd=status |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- The parity proof here is two-part: preflight computes the canonical summary, while the audit confirms the runtime stayed on the compact read scope.
