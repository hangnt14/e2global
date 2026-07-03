# Golden: F22 - Reverse Focus Selection Blocks Without Confirmation

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start reverse |
| resolved_slug | test-project |
| source_of_truth_artifact | none |
| read_scope | core/contract.yaml, core/contract-behavior.md |
| write_target | none |
| approval_gate | FOCUS_SELECTION_REQUIRED |
| activation_level | Base |
| fallback_code | FOCUS_SELECTION_PENDING |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- The runtime must not write reverse_baseline_lock.json, reverse_index.md, or reverse_read_manifest.ndjson before focus is confirmed.
- A runtime that proceeds past the focus gate without user input is a parity failure.
