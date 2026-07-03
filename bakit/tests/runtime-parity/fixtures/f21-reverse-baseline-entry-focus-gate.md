# Fixture F21: Reverse Baseline Entry and Focus Selection Gate

## Scenario

BA runs `ba-start reverse` on a project with no existing reverse lane artifacts.
Verifies that the command locks the baseline commit, presents focus areas, and
blocks at the HITL focus-selection gate without auto-picking.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/
│   └── intake.md
└── 02_backbone/
    └── backbone.md
(no 00_reverse/ directory)
```

No `reverse_baseline_lock.json` exists.

## Input Command

```text
ba-start reverse --slug test-project
```

## Expected Behavior

- Reads `core/contract.yaml` and `core/contract-behavior.md`.
- Resolves HEAD commit via `git rev-parse HEAD` (or accepts `--commit`).
- Presents focus area options to the user.
- Stops and waits for explicit focus selection — does not auto-pick.
- Does not write any reverse artifacts until focus is confirmed.
- Does not execute application code, runtime probes, or live endpoint calls.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start reverse |
| activation_level | Base |
| fallback_code | NONE |
| approval_gate | FOCUS_SELECTION_REQUIRED |
| source_of_truth_artifact | none (reverse lane; canonical artifacts unchanged) |
| read_scope | core/contract.yaml + core/contract-behavior.md |
| write_target | none until focus confirmed |

## Guardrail Evidence

| Field | Expected Value |
| --- | --- |
| evidence_source | adapter manifest or runtime trace |
| preflight_status | ok |
| audit_status | pass |

## Notes

- This fixture fails parity if a runtime auto-selects focus areas without user confirmation.
- Golden: `goldens/g21-reverse-baseline-entry-focus-gate.md`
