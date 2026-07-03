# Golden: F23 - Reverse Drift Stale Block

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start reverse status |
| resolved_slug | test-project |
| source_of_truth_artifact | none |
| read_scope | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/00_reverse/reverse-baseline-lock.json, plans/test-project-20260424/00_reverse/reverse-index.md |
| write_target | none |
| approval_gate | NOT_REQUIRED |
| activation_level | Base |
| fallback_code | REVERSE_INDEX_STALE |
| visible_warning | reverse index is stale; run reverse refresh before using evidence |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- The runtime must flag stale_status and recommend reverse refresh.
- Using stale evidence as current is a parity failure.
- Only header fields of reverse_index.md may be read; full content read is not required.
