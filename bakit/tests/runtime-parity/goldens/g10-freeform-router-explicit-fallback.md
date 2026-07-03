# Golden: F10 - Freeform Router Explicit-Step Fallback

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | STOP |
| resolved_slug | test-project |
| resolved_module | export |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/backbone.md |
| read_scope | plans/test-project-20260424/02_backbone/backbone.md |
| write_target | NONE |
| approval_gate | REQUIRED |
| activation_level | Base |
| fallback_code | EXPLICIT_STEP_REQUIRED |
| visible_warning | Freeform route ambiguous; choose explicit ba-start step |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- Ambiguous freeform text must fail closed.
- Runtime should ask the user to choose an explicit BA lifecycle step before any mutation.
