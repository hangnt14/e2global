# Golden: F18 - package Guardrail Records Escalated Exact-Content Reads

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start package |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260424/03_modules/auth-flow/srs.md |
| read_scope | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/02_backbone/backbone-index.md, plans/test-project-20260424/03_modules/auth-flow/userstories/index.md, plans/test-project-20260424/03_modules/auth-flow/usecases/index.md, plans/test-project-20260424/03_modules/auth-flow/ascii-screen/index.md, plans/test-project-20260424/02_backbone/project-memory/index.md, plans/test-project-20260424/02_backbone/project-memory.md, plans/test-project-20260424/03_modules/auth-flow/srs.md |
| write_target | plans/test-project-20260424/04_compiled/compiled-srs.html |
| approval_gate | NOT_REQUIRED |
| activation_level | Base |
| fallback_code | READ_ESCALATION |

## Guardrail Preflight

| Field | Expected Value |
| --- | --- |
| status | ok |
| command | package |
| resolved_slug | test-project |
| guardrail_mode | index-first |
| indexes.backbone_index.state | current |
| indexes.userstories_index.state | current |
| indexes.usecases_index.state | current |
| indexes.ascii_screen_index.state | current |
| allow_reads_includes | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/02_backbone/backbone-index.md, plans/test-project-20260424/03_modules/auth-flow/userstories/index.md, plans/test-project-20260424/03_modules/auth-flow/usecases/index.md, plans/test-project-20260424/03_modules/auth-flow/ascii-screen/index.md, plans/test-project-20260424/02_backbone/project-memory/index.md, plans/test-project-20260424/02_backbone/project-memory.md |
| deny_reads_includes | plans/test-project-20260424/01_intake/intake.md, plans/test-project-20260424/02_backbone/backbone.md, plans/test-project-20260424/03_modules/auth-flow/userstories/us-login.md, plans/test-project-20260424/03_modules/auth-flow/srs.md |
| message | GUARDRAIL: cmd=package mode=index-first idx=backbone_index+userstories_index+usecases_index+ascii_screen_index current=4 allow=contract.yaml,backbone-index.md,index.md,index.md,index.md,index.md,project-memory.md deny=summary,chunk-index,intake,backbone,us-login,srs,log |

## Guardrail Audit

| Field | Expected Value |
| --- | --- |
| status | warn |
| actual_reads_includes | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/02_backbone/backbone-index.md, plans/test-project-20260424/03_modules/auth-flow/userstories/index.md, plans/test-project-20260424/03_modules/auth-flow/usecases/index.md, plans/test-project-20260424/03_modules/auth-flow/ascii-screen/index.md, plans/test-project-20260424/02_backbone/project-memory/index.md, plans/test-project-20260424/02_backbone/project-memory.md, plans/test-project-20260424/03_modules/auth-flow/srs.md |
| actual_reads_excludes | plans/test-project-20260424/01_intake/intake.md, plans/test-project-20260424/02_backbone/backbone.md |
| violations.count | 0 |
| warnings.count | 1 |
| warnings.types_includes | escalated_read |
| warnings.paths_includes | plans/test-project-20260424/03_modules/auth-flow/srs.md |
| message | GUARDRAIL_AUDIT_WARN: cmd=package warning=escalated_read path=plans/test-project-20260424/03_modules/auth-flow/srs.md |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- This fixture encodes the current v1 compromise: exact-content reads stay legal only when they are surfaced as auditable escalations.
