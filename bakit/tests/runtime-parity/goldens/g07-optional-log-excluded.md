# Golden: F07 - Optional Log Excluded From Default Reads

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start status |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/project-memory/index.md |
| read_scope | plans/test-project-20260424/02_backbone/project-memory/index.md |
| must_not_read | plans/test-project-20260424/02_backbone/project-memory/log.md, plans/test-project-20260424/02_backbone/project-memory/cold/ |
| write_target | NONE |
| approval_gate | NOT_REQUIRED |
| activation_level | Modular |
| fallback_code | NONE |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- `log.md` may exist, but status must not read it unless the user asks for audit context.
