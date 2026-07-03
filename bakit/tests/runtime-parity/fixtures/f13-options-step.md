# Fixture F13: Explicit ba-start options Command

## Scenario

Explicit `ba-start options` command after intake exists and before backbone exists.
Verifies that runtimes open the optioning cycle from the intake decision ledger without
reading beyond the pre-backbone scope.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/
│   ├── intake.md
│   └── plan.md
└── PROJECT-HOME.md
```

`plan.md` records `options status: recommended` and `expected next command: options`.

## Input Command

```text
ba-start options --slug test-project
```

## Expected Behavior

- Reads `01_intake/intake.md` and `01_intake/plan.md` only.
- Writes `01_intake/options/index.md`.
- Writes 1-3 option files.
- Writes `comparison.md` only when more than one viable option exists.
- Keeps options as solution briefs, not mini-backbones.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start options |
| activation_level | Base |
| fallback_code | NONE |
| approval_gate | NOT_REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/01_intake/intake.md |
| read_scope | 01_intake/intake.md + 01_intake/plan.md |
| write_target | 01_intake/options/index.md |

## Notes

- This fixture fails parity if a runtime reads backbone artifacts before the option decision is locked.
- Golden: `goldens/g13-options-step.md`
