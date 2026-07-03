# Fixture F09: Activation Freeze On Runtime Mismatch

## Scenario

Stored activation state and computed activation state disagree. Verifies that runtimes
freeze to `Base` rather than continuing with inconsistent Modular or Program behavior.

## Input State

```text
plans/test-project-20260424/
└── 02_backbone/
    └── project-memory/
        └── index.md
```

`index.md` stores `Activation Level: Program`, but computed signals from persisted
sources produce `Modular`.

## Input Command

```text
ba-start status --slug test-project
```

## Expected Behavior

- Detects mismatch between stored and computed activation level.
- Freezes activation to `Base`.
- Emits visible `ACTIVATION_FREEZE` warning.
- Does not proceed with Modular or Program behavior until explicit refresh.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start status |
| activation_level | Base |
| fallback_code | ACTIVATION_FREEZE |
| approval_gate | REQUIRED_REFRESH |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/project-memory/index.md |
| read_scope | plans/test-project-20260424/02_backbone/project-memory/index.md |
| write_target | NONE |
| visible_warning | ACTIVATION_FREEZE |

## Notes

- This fixture fails parity if the runtime silently recomputes and proceeds.
- Golden: `goldens/g09-activation-freeze-mismatch.md`
