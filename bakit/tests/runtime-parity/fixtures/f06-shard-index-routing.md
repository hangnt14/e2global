# Fixture F06: Shard Index Routing

## Scenario

Project has a valid shard tree. Verifies that runtimes read `project-memory/index.md`
first and then load only the hot shards routed by that index for a module command.

## Input State

```text
plans/test-project-20260424/
├── 02_backbone/
│   ├── backbone.md
│   └── project-memory/
│       ├── index.md
│       ├── hot/canonical-vocabulary.md
│       ├── hot/approved-decisions.md
│       ├── hot/pushback-triggers.md
│       └── warm/modules/export.md
└── 03_modules/export/
    └── user-stories.md
```

## Input Command

```text
ba-start srs --slug test-project --module export
```

## Expected Behavior

- Reads `project-memory/index.md` before shard content.
- Reads only hot shards plus `warm/modules/export.md`.
- Does not read unrelated module shards or `cold/`.
- Same routing and read-scope decision across all 3 runtimes.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start srs |
| activation_level | Modular |
| fallback_code | NONE |
| approval_gate | NOT_REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/backbone.md |
| read_scope | project-memory/index.md, hot/canonical-vocabulary.md, hot/approved-decisions.md, hot/pushback-triggers.md, warm/modules/export.md, 03_modules/export/user-stories.md |
| write_target | plans/test-project-20260424/03_modules/export/srs.md |

## Notes

- This fixture fails parity if a runtime scans the whole memory tree.
- Golden: `goldens/g06-shard-index-routing.md`
