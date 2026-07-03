# Golden: F06 - Shard Index Routing

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start srs |
| resolved_slug | test-project |
| resolved_module | export |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/backbone.md |
| read_scope | plans/test-project-20260424/02_backbone/project-memory/index.md, plans/test-project-20260424/02_backbone/project-memory/hot/canonical-vocabulary.md, plans/test-project-20260424/02_backbone/project-memory/hot/approved-decisions.md, plans/test-project-20260424/02_backbone/project-memory/hot/pushback-triggers.md, plans/test-project-20260424/02_backbone/project-memory/warm/modules/export.md, plans/test-project-20260424/03_modules/export/user-stories.md |
| write_target | plans/test-project-20260424/03_modules/export/srs.md |
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

- The index must be the navigation surface before hot or warm shards are read.
- Parity fails if unrelated module shards, `log.md`, or `cold/` are loaded.
