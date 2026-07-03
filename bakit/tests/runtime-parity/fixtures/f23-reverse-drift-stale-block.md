# Fixture F23: Reverse Drift Stale Block

## Scenario

BA runs `ba-start reverse status` when the reverse index exists but `stale_status`
is `stale` (documented_commit has changed). Verifies that the runtime surfaces the
stale state and recommends `reverse refresh` instead of silently using stale evidence.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/
│   └── intake.md
├── 02_backbone/
│   └── backbone.md
└── 00_reverse/
    ├── reverse-baseline-lock.json   (documented_commit: abc1234)
    ├── reverse-index.md             (stale_status: stale)
    └── reverse-read-manifest.ndjson
```

Current HEAD commit differs from `documented_commit` in the baseline lock.

## Input Command

```text
ba-start reverse status --slug test-project
```

## Expected Behavior

- Reads `core/contract.yaml` and `core/contract-behavior.md`.
- Reads `reverse_baseline_lock.json` header fields only.
- Reads `reverse_index.md` header fields only (stale_status).
- Flags the index as `[!] stale` in the output.
- Recommends `/ba-start reverse refresh --slug test-project`.
- Does NOT treat stale evidence as current.
- Does NOT mutate any artifacts.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start reverse status |
| activation_level | Base |
| fallback_code | REVERSE_INDEX_STALE |
| approval_gate | NOT_REQUIRED |
| source_of_truth_artifact | none (reverse lane; canonical artifacts unchanged) |
| read_scope | core/contract.yaml + core/contract-behavior.md + 00_reverse/reverse-baseline-lock.json + 00_reverse/reverse-index.md |
| write_target | none |

## Guardrail Evidence

| Field | Expected Value |
| --- | --- |
| evidence_source | adapter manifest or runtime trace |
| preflight_status | ok |
| audit_status | pass |

## Notes

- This fixture fails parity if a runtime uses stale reverse evidence without flagging it.
- Golden: `goldens/g23-reverse-drift-stale-block.md`
