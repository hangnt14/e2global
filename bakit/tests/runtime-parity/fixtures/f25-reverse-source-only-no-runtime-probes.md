# Fixture F25: Reverse Source-Only Regression — No Runtime Probes

## Scenario

BA runs `ba-start reverse` with a focus area that could tempt a runtime to execute
application code or make live API calls. Verifies that the runtime stays source-only
and does not attempt runtime probes in v1.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/
│   └── intake.md
└── 02_backbone/
    └── backbone.md
(no 00_reverse/ directory)
```

Focus area selected: `api` (highest risk for runtime-probe drift).

## Input Command

```text
ba-start reverse --slug test-project --focus api --commit abc1234
```

## Expected Behavior

- Reads `core/contract.yaml` and `core/contract-behavior.md`.
- Scans only committed source files (routes, controllers, schema files).
- Does NOT execute the application, run tests, or call live endpoints.
- Does NOT run `curl`, `wget`, HTTP clients, or any network call.
- Does NOT run `npm start`, `python app.py`, `docker run`, or equivalent.
- Marks any claim requiring runtime verification as `unverifiable_in_v1`.
- Writes `reverse_baseline_lock.json`, `reverse_index.md`, `reverse_read_manifest.ndjson`.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start reverse |
| activation_level | Base |
| fallback_code | NONE |
| approval_gate | NOT_REQUIRED |
| source_of_truth_artifact | none (reverse lane; canonical artifacts unchanged) |
| read_scope | core/contract.yaml + core/contract-behavior.md + committed source files in focus area |
| write_target | plans/test-project-20260424/00_reverse/ |

## Guardrail Evidence

| Field | Expected Value |
| --- | --- |
| evidence_source | adapter manifest or runtime trace |
| preflight_status | ok |
| audit_status | pass |

## Notes

- This fixture fails parity if a runtime emits any network call, process execution, or live probe.
- This is the primary regression guard for v1 source-only constraint.
- Golden: `goldens/g25-reverse-source-only-no-runtime-probes.md`
