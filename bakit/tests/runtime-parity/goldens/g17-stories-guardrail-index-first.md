# Golden: F17 - stories Guardrail Enforces backbone-index First

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start stories |
| resolved_slug | test-project |
| resolved_module | auth-flow |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/backbone.md |
| read_scope | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/02_backbone/backbone-index.md, plans/test-project-20260424/01_intake/plan.md |
| write_target | plans/test-project-20260424/03_modules/auth-flow/user-stories.md |
| approval_gate | NOT_REQUIRED |
| activation_level | Base |
| fallback_code | NONE |

## Guardrail Preflight

| Field | Expected Value |
| --- | --- |
| status | ok |
| command | stories |
| resolved_slug | test-project |
| resolved_module | auth-flow |
| guardrail_mode | index-first |
| indexes.backbone_index.state | current |
| allow_reads_includes | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/02_backbone/backbone-index.md, plans/test-project-20260424/01_intake/plan.md, plans/test-project-20260424/03_modules/auth-flow/frd.md |
| deny_reads_includes | plans/test-project-20260424/02_backbone/backbone.md |
| excerpt_plan | backbone_by_module |
| message | GUARDRAIL: cmd=stories mode=index-first idx=backbone_index current=1 allow=contract.yaml,backbone-index.md,plan.md deny=backbone |

## Guardrail Audit

| Field | Expected Value |
| --- | --- |
| status | pass |
| actual_reads_includes | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/02_backbone/backbone-index.md, plans/test-project-20260424/01_intake/plan.md |
| actual_reads_excludes | plans/test-project-20260424/02_backbone/backbone.md |
| violations.count | 0 |
| warnings.count | 0 |
| message | GUARDRAIL_AUDIT_PASS: cmd=stories |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- `frd.md` appears in the allowlist because the guardrail policy permits it, but this fixture does not require an actual FRD read.
