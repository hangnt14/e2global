# Fixture F22: Reverse Focus Selection Blocks Without Confirmation

## Scenario

BA runs `ba-start reverse` and the runtime attempts to proceed past focus selection
without explicit user confirmation. Verifies the fail-closed HITL gate.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/
│   └── intake.md
└── 02_backbone/
    └── backbone.md
(no 00_reverse/ directory)
```

No `reverse_baseline_lock.json` exists. No `--focus` argument supplied.

## Input Command

```text
ba-start reverse --slug test-project
```

## Expected Behavior

- Reads `core/contract.yaml` and `core/contract-behavior.md`.
- Presents focus area options.
- Does NOT proceed to scan phase without explicit focus confirmation.
- Does NOT write `reverse_baseline_lock.json`, `reverse_index.md`, or `reverse_read_manifest.ndjson`.
- Emits a clear stop message indicating focus selection is required.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start reverse |
| activation_level | Base |
| fallback_code | FOCUS_SELECTION_PENDING |
| approval_gate | FOCUS_SELECTION_REQUIRED |
| source_of_truth_artifact | none |
| read_scope | core/contract.yaml + core/contract-behavior.md |
| write_target | none |

## Guardrail Evidence

| Field | Expected Value |
| --- | --- |
| evidence_source | adapter manifest or runtime trace |
| preflight_status | ok |
| audit_status | pass |

## Notes

- This fixture fails parity if a runtime writes any reverse artifact before focus is confirmed.
- Golden: `goldens/g22-reverse-focus-selection-blocks.md`
