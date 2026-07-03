# Golden: F24 - Reverse Mixed-Change Blocks Promotion

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start reverse promote |
| resolved_slug | test-project |
| source_of_truth_artifact | none |
| read_scope | core/contract.yaml, core/contract-behavior.md, plans/test-project-20260424/00_reverse/reverse-baseline-lock.json, plans/test-project-20260424/00_reverse/reverse-evidence-ledger.md |
| write_target | none |
| approval_gate | SPLIT_REQUIRED |
| activation_level | Base |
| fallback_code | MIXED_CHANGE_SPLIT_REQUIRED |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- The runtime must block promotion of mixed_change evidence and recommend reverse impact to split.
- Promoting mixed_change evidence directly to backbone or SRS is a parity failure.
- The canonical artifacts (backbone, SRS) must remain unmodified.
