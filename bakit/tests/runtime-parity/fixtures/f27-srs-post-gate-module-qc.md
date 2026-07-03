# Fixture F27: SRS Auto-Triggers Module QC With Module-Scoped Outputs

## Scenario

`ba-start srs` completes for one module in the canon-first flow. The runtime must immediately
run `qc-review` against the module canon set and write the QC report inside the same module
root. The gate no longer waits for `wireframes`, and it no longer writes to legacy `docs/QC-*`
folders.

## Input State

```text
plans/test-project-20260526/
├── 02_backbone/
│   ├── backbone.md
│   └── backbone-index.md
└── 03_modules/auth-flow/
    ├── user-stories.md
    ├── user-stories-index.md
    ├── screens/
    ├── screen-field-contract.yaml
    ├── usecases/
    ├── srs-index.md
    ├── srs.md
    └── srs-compile-receipt.json
```

The module canon is current enough for SRS completion. No QC report exists yet.

## Input Command

```text
ba-start srs --slug test-project --module auth-flow
```

## Expected Behavior

- Completes SRS compilation for the module.
- Fires the single post-`srs` QC gate automatically.
- Reads module canon first (`srs-index.md`, `usecases/*.md`, `screens/*.md`, `screen-field-contract.yaml`).
- Uses compiled `srs.md` only as supporting evidence.
- Writes the QC report and backlog under `03_modules/auth-flow/qc-review/`.
- Does not require `wireframes` to trigger QC.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start srs |
| source_of_truth_artifact | plans/test-project-20260526/03_modules/auth-flow/srs-index.md + usecases/*.md + screens/*.md + screen-field-contract.yaml |
| write_target | plans/test-project-20260526/03_modules/auth-flow/qc-review/auth-flow-qc-review-report-v1.md |
| approval_gate | NOT_REQUIRED |
| activation_level | Base |
| fallback_code | NONE |

## Notes

- This fixture fails parity if QC still waits for `wireframes` or writes to `docs/QC-*`.
- Golden: `goldens/g27-srs-post-gate-module-qc.md`
