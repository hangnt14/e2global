# Golden: F27 - SRS Auto-Triggers Module QC With Module-Scoped Outputs

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start srs |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260526/03_modules/auth-flow/srs-index.md, plans/test-project-20260526/03_modules/auth-flow/usecases/*.md, plans/test-project-20260526/03_modules/auth-flow/screens/*.md |
| read_scope | core/contract.yaml, core/contract-behavior.md, core/behavior/qc-review.md, skills/qc-uc-review/SKILL.md, skills/qc-uc-review/profiles/mobile.md, skills/qc-uc-review/references/scoring-rubric.md, plans/test-project-20260526/03_modules/auth-flow/srs-index.md, plans/test-project-20260526/03_modules/auth-flow/usecases/*.md, plans/test-project-20260526/03_modules/auth-flow/screens/*.md, plans/test-project-20260526/03_modules/auth-flow/screen-field-contract.yaml, plans/test-project-20260526/03_modules/auth-flow/srs.md, plans/test-project-20260526/03_modules/auth-flow/srs-compile-receipt.json |
| write_target | plans/test-project-20260526/03_modules/auth-flow/qc-review/auth-flow-qc-review-report-v1.md |
| approval_gate | NOT_REQUIRED |
| activation_level | Base |
| fallback_code | NONE |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- The qc-report backlog companion path is `plans/test-project-20260526/03_modules/auth-flow/qc-review/auth-flow-qc-review-question-backlog.md`.
- Parity fails if the runtime treats compiled `srs.md` as the sole source of truth or routes QC to legacy `docs/QC-*`.
