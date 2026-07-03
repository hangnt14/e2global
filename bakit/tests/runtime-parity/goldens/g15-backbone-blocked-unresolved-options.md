# Golden: F15 - backbone Blocked While options Decision Is Unresolved

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start backbone |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260424/01_intake/plan.md |
| read_scope | plans/test-project-20260424/01_intake/intake.md, plans/test-project-20260424/01_intake/plan.md |
| write_target | plans/test-project-20260424/02_backbone/backbone.md |
| approval_gate | REQUIRED_DECISION |
| activation_level | Base |
| fallback_code | OPTIONS_UNRESOLVED |
| visible_warning | OPTIONS_UNRESOLVED |
| required_decision | selected option or skipped |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- Backbone must fail closed when `options status` is `recommended` or `in-progress`.
- The decision ledger in `plan.md` is sufficient for the block; runtimes must not broad-scan for option artifacts before stopping.
