# Golden: F28 - Deprecated Wireframes Does Not Trigger QC

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start wireframes |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260526/03_modules/auth-flow/screens/scr-login.md |
| read_scope | core/contract.yaml, core/contract-behavior.md, core/behavior/wireframes.md, plans/test-project-20260526/03_modules/auth-flow/srs-index.md, plans/test-project-20260526/03_modules/auth-flow/screens/scr-login.md, plans/test-project-20260526/03_modules/auth-flow/srs-compile-receipt.json |
| write_target | NONE |
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

- QC already happened after `srs`. `wireframes` must not create `auth-flow-qc-review-report-v2.md`.
- The compatibility command must not create legacy visual handoff artifacts.
- Aggregate cross-artifact validation is deferred to `ba-start package`.
