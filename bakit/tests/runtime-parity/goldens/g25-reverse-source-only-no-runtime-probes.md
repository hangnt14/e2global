# Golden: F25 - Reverse Source-Only Regression — No Runtime Probes

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start reverse |
| resolved_slug | test-project |
| source_of_truth_artifact | none |
| read_scope | core/contract.yaml, core/contract-behavior.md, committed source files in focus area |
| write_target | plans/test-project-20260424/00_reverse/ |
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

- The runtime must not execute application code, run tests, make HTTP calls, or probe live services.
- Any network call, process execution, or live endpoint verification is a parity failure.
- Claims requiring runtime verification must be marked unverifiable_in_v1 in the evidence ledger.
- This golden is the primary regression guard for the v1 source-only constraint.
