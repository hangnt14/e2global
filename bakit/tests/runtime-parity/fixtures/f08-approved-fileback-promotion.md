# Fixture F08: Approved File-Back Promotion

## Scenario

An impact run produced useful analysis that should be filed back into canonical memory.
Verifies that runtimes require human approval authority and persisted trace metadata before
promoting the result.

## Input State

```text
plans/test-project-20260424/
├── 02_backbone/
│   ├── backbone.md
│   └── project-memory/
│       ├── index.md
│       └── hot/approved-decisions.md
└── 03_modules/export/
    └── user-stories.md
```

## Input Command

```text
ba-impact --slug test-project "Chốt Export CSV audit log là bắt buộc"
```

## Expected Behavior

- Produces impact analysis without mutating memory.
- Requires explicit approval before file-back.
- Promotion target is a canonical memory shard, not runtime chat memory.
- File-back record carries approver, role, approval basis, impact reference, and trace ids.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-impact |
| activation_level | Modular |
| fallback_code | NONE |
| approval_gate | REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/backbone.md |
| write_target | NONE |
| promotion_target | project-memory/hot/approved-decisions.md |
| required_trace_fields | source_artifact, source_ids, promotion_target, approved_by, approved_role, approved_at, approval_basis, approval_trigger, impact_ref |

## Notes

- This fixture fails parity if useful output is stored automatically without approval.
- Golden: `goldens/g08-approved-fileback-promotion.md`
