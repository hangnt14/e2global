# Fixture F18: package Guardrail Records Escalated Exact-Content Reads

## Scenario

`ba-start package` runs with current backbone, user story, use case, and ASCII screen indexes. Verifies that
discovery stays index-first and that any full-artifact compilation read is carried as explicit
guardrail evidence instead of being treated as an untracked bypass.

## Input State

```text
plans/test-project-20260424/
├── 02_backbone/
│   ├── backbone.md
│   ├── backbone-index.md
│   ├── project-memory.md
│   └── project-memory/
│       └── index.md
└── 03_modules/auth-flow/
    ├── userstories/
    │   ├── index.md
    │   └── us-login.md
    ├── usecases/
    │   └── index.md
    ├── ascii-screen/
    │   └── index.md
    ├── srs.md
```

All four index files are current. The package run compiles SRS output and records an explicit
exact-content escalation for the full `srs.md` read.

## Input Command

```text
ba-start package --slug test-project
```

## Expected Behavior

- Reads `core/contract.yaml` and `core/contract-behavior.md`.
- Uses `backbone-index.md`, `userstories/index.md`, `usecases/index.md`, `ascii-screen/index.md`, and project memory indexes for discovery.
- Does not broad-read intake or full backbone during discovery.
- Records any full `srs.md` compile read as explicit guardrail evidence.
- Writes `04_compiled/compiled-srs.html`.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start package |
| activation_level | Base |
| fallback_code | READ_ESCALATION |
| approval_gate | NOT_REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/03_modules/auth-flow/srs.md |
| read_scope | core/contract.yaml + core/contract-behavior.md + 02_backbone/backbone-index.md + 02_backbone/project-memory.md + 02_backbone/project-memory/index.md + 03_modules/auth-flow/userstories/index.md + 03_modules/auth-flow/usecases/index.md + 03_modules/auth-flow/ascii-screen/index.md + 03_modules/auth-flow/srs.md |
| write_target | plans/test-project-20260424/04_compiled/compiled-srs.html |

## Guardrail Evidence

| Field | Expected Value |
| --- | --- |
| evidence_source | adapter manifest plus escalation ledger |
| preflight_status | ok |
| audit_status | warn |

## Notes

- This fixture makes the evidence gap explicit: discovery stays index-first, but compile-time full reads must still be auditable.
- Golden: `goldens/g18-package-guardrail-escalated-exact-content.md`
