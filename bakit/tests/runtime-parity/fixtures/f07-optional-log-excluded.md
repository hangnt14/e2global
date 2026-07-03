# Fixture F07: Optional Log Excluded From Default Reads

## Scenario

Project has `project-memory/log.md`, but the command is a normal status check without
audit or recent-history request. Verifies that `log.md` stays out of default reads.

## Input State

```text
plans/test-project-20260424/
└── 02_backbone/
    └── project-memory/
        ├── index.md
        ├── log.md
        └── hot/approved-decisions.md
```

## Input Command

```text
ba-start status --slug test-project
```

## Expected Behavior

- Reads `project-memory/index.md` for activation and freshness metadata.
- Does not read `project-memory/log.md`.
- Emits no audit escalation because the user did not request audit context.
- Same behavior across all 3 runtimes.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start status |
| activation_level | Modular |
| fallback_code | NONE |
| approval_gate | NOT_REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/project-memory/index.md |
| read_scope | project-memory/index.md |
| must_not_read | project-memory/log.md, project-memory/cold/ |
| write_target | NONE |

## Notes

- This fixture fails parity if `log.md` is loaded by default.
- Golden: `goldens/g07-optional-log-excluded.md`
