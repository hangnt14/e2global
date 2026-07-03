# Fixture F14: ba-next Recommends options After Intake Recommendation

## Scenario

`ba-start next` runs after intake when the decision ledger says optioning is recommended.
Verifies that runtimes recommend the explicit options command without mutating artifacts.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/
│   ├── intake.md
│   └── plan.md
└── PROJECT-HOME.md
```

`plan.md` records `options status: recommended`, a recommendation summary, and `expected next command: options`.

## Input Command

```text
ba-start next --slug test-project
```

## Expected Behavior

- Reads `01_intake/intake.md` and `01_intake/plan.md`.
- Recommends `ba-start options --slug test-project`.
- Does not write any artifact.
- Explains that the next safe step is the options flow before backbone.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start options |
| activation_level | Base |
| fallback_code | NONE |
| approval_gate | NOT_REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/01_intake/plan.md |
| read_scope | 01_intake/intake.md + 01_intake/plan.md |
| write_target | NONE |

## Notes

- This fixture fails parity if a runtime jumps directly to backbone while `options status` is still `recommended`.
- Golden: `goldens/g14-next-recommends-options.md`
