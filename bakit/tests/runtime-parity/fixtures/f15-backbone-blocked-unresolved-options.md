# Fixture F15: backbone Blocked While options Decision Is Unresolved

## Scenario

An explicit `ba-start backbone` command is issued while the intake decision ledger still
shows unresolved optioning. Verifies that runtimes fail closed before any backbone write.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/
│   ├── intake.md
│   └── plan.md
└── PROJECT-HOME.md
```

`plan.md` records `options status: recommended` and no `selected option`.

## Input Command

```text
ba-start backbone --slug test-project
```

## Expected Behavior

- Reads `01_intake/intake.md` and `01_intake/plan.md` only.
- Stops because the options decision is unresolved.
- Does not write `02_backbone/backbone.md`.
- Requires an explicit decision before backbone can proceed.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start backbone |
| activation_level | Base |
| fallback_code | OPTIONS_UNRESOLVED |
| approval_gate | REQUIRED_DECISION |
| source_of_truth_artifact | plans/test-project-20260424/01_intake/plan.md |
| read_scope | 01_intake/intake.md + 01_intake/plan.md |
| write_target | 02_backbone/backbone.md |

## Notes

- This fixture fails parity if a runtime silently skips the decision gate and drafts backbone anyway.
- Golden: `goldens/g15-backbone-blocked-unresolved-options.md`
