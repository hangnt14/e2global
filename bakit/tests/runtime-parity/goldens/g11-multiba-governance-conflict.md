# Golden: F11 - Multi-BA Governance Conflict

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | STOP |
| resolved_slug | test-project |
| resolved_module | export |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/project-memory/hot/approved-decisions.md |
| read_scope | plans/test-project-20260424/02_backbone/backbone.md, plans/test-project-20260424/02_backbone/project-memory/index.md, plans/test-project-20260424/02_backbone/project-memory/hot/approved-decisions.md, plans/test-project-20260424/02_backbone/project-memory/warm/modules/export.md, plans/test-project-20260424/02_backbone/project-memory/warm/modules/billing.md |
| write_target | NONE |
| approval_gate | LEAD_BA_REQUIRED |
| activation_level | Program |
| fallback_code | GOVERNANCE_CONFLICT |
| visible_warning | GOVERNANCE_CONFLICT |
| escalation_target | Lead BA |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- Module-scoped work must not override global hot-shard decisions.
- Cross-module decision changes require Lead BA approval plus impact rerun before mutation.
