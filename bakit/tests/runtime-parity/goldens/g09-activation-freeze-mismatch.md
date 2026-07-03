# Golden: F09 - Activation Freeze On Runtime Mismatch

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start status |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/project-memory/index.md |
| read_scope | plans/test-project-20260424/02_backbone/project-memory/index.md |
| write_target | NONE |
| approval_gate | REQUIRED_REFRESH |
| activation_level | Base |
| fallback_code | ACTIVATION_FREEZE |
| visible_warning | ACTIVATION_FREEZE |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- Stored Program plus computed Modular must not continue as either Program or Modular.
- Runtime must freeze to Base and wait for explicit activation refresh.
