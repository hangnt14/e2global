# Fixture F24: Reverse Mixed-Change Classification Blocks Promotion

## Scenario

BA runs `ba-start reverse promote` with an evidence ID that is classified as
`mixed_change`. Verifies that the runtime blocks promotion and requires the
evidence to be split via `reverse impact` before proceeding.

## Input State

```text
plans/test-project-20260424/
└── 00_reverse/
    ├── reverse-baseline-lock.json
    ├── reverse-index.md             (stale_status: current)
    ├── reverse-focus-excerpts.md
    └── reverse-evidence-ledger.md   (EV-003 lane: mixed_change)
```

`reverse-evidence-ledger.md` contains entry `EV-003` with `lane: mixed_change`.

## Input Command

```text
ba-start reverse promote --slug test-project --evidence-ids EV-003
```

## Expected Behavior

- Reads `core/contract.yaml` and `core/contract-behavior.md`.
- Reads `reverse_baseline_lock.json` and `reverse_evidence_ledger.md`.
- Detects that EV-003 has `lane: mixed_change`.
- Blocks promotion and prints a split instruction.
- Recommends `/ba-start reverse impact --slug test-project --evidence-ids EV-003`.
- Does NOT mutate backbone, SRS, or any canonical artifact.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start reverse promote |
| activation_level | Base |
| fallback_code | MIXED_CHANGE_SPLIT_REQUIRED |
| approval_gate | SPLIT_REQUIRED |
| source_of_truth_artifact | none (promotion blocked) |
| read_scope | core/contract.yaml + core/contract-behavior.md + 00_reverse/reverse-baseline-lock.json + 00_reverse/reverse-evidence-ledger.md |
| write_target | none |

## Guardrail Evidence

| Field | Expected Value |
| --- | --- |
| evidence_source | adapter manifest or runtime trace |
| preflight_status | ok |
| audit_status | pass |

## Notes

- This fixture fails parity if a runtime promotes mixed_change evidence without splitting.
- Golden: `goldens/g24-reverse-mixed-change-blocks-promotion.md`
