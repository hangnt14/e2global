# Golden: F21 - Reverse Baseline Entry and Focus Selection Gate

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start reverse |
| resolved_slug | test-project |
| source_of_truth_artifact | none |
| read_scope | core/contract.yaml, core/contract-behavior.md |
| write_target | none until focus confirmed |
| approval_gate | FOCUS_SELECTION_REQUIRED |
| activation_level | Base |
| fallback_code | NONE |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- The runtime must present focus area options and stop. Auto-picking focus areas is a parity failure.
- No reverse artifacts may be written before focus is confirmed.
- Source-only constraint applies from the first command invocation.
