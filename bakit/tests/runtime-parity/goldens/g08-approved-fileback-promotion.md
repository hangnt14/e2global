# Golden: F08 - Approved File-Back Promotion

## Behavior Envelope

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-impact |
| resolved_slug | test-project |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/backbone.md |
| read_scope | plans/test-project-20260424/02_backbone/backbone.md, plans/test-project-20260424/02_backbone/project-memory/index.md, plans/test-project-20260424/02_backbone/project-memory/hot/approved-decisions.md, plans/test-project-20260424/03_modules/export/user-stories.md |
| write_target | NONE |
| promotion_target | plans/test-project-20260424/02_backbone/project-memory/hot/approved-decisions.md |
| required_trace_fields | source_artifact, source_ids, promotion_target, approved_by, approved_role, approved_at, approval_basis, approval_trigger, impact_ref |
| approval_gate | REQUIRED |
| activation_level | Modular |
| fallback_code | NONE |

## Runtime Parity Check

| Runtime | Status |
| --- | --- |
| Claude Code | EXEMPT v1 maintainer decision |
| Codex | EXEMPT v1 maintainer decision |
| Antigravity | EXEMPT v1 maintainer decision |

## Notes

- Useful analysis output cannot enter canonical memory until approved by the correct human authority.
- Command-level approval alone is not enough for file-back promotion.
