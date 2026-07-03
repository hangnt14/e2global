# Fixture F10: Freeform Router Explicit-Step Fallback

## Scenario

Freeform routing cannot determine a single safe command. Verifies that runtimes stop and
recommend the explicit `ba-start` path instead of guessing or mutating artifacts.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/intake.md
└── 02_backbone/backbone.md
```

## Input Command

Freeform text:

```text
Làm tiếp phần đó cho module export
```

## Expected Behavior

- Detects ambiguous freeform intent.
- Does not mutate any artifact.
- Falls back to explicit-step prompt with exact supported commands.
- Recommends explicit `ba-start <step> --slug test-project --module export` once the user selects a step.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | STOP |
| activation_level | Base |
| fallback_code | EXPLICIT_STEP_REQUIRED |
| approval_gate | REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/backbone.md |
| read_scope | plans/test-project-20260424/02_backbone/backbone.md |
| write_target | NONE |
| visible_warning | Freeform route ambiguous; choose explicit ba-start step |

## Notes

- This fixture fails parity if a runtime infers a step and writes without confirmation.
- Golden: `goldens/g10-freeform-router-explicit-fallback.md`
