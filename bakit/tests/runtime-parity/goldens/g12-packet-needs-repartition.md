# Golden: F12 - Packet Needs Repartition

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | NEEDS_REPARTITION |
| resolved_slug | test-project |
| resolved_module | export |
| source_of_truth_artifact | plans/test-project-20260424/delegation/packets/PKT-01.md |
| read_scope | plans/test-project-20260424/delegation/packets/PKT-01.md |
| must_not_read | plans/test-project-20260424/02_backbone/backbone.md, plans/test-project-20260424/02_backbone/project-memory/ |
| write_target | NONE |
| approval_gate | NOT_REQUIRED |
| activation_level | Program |
| fallback_code | NEEDS_REPARTITION |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- Worker runtimes must not self-heal incomplete packets by loading the whole memory tree.
- The correct response is a bounded repartition request with exact missing inputs.
