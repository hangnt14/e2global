# Fixture F19: status Ignores PROJECT-HOME Conflict

## Scenario

`ba-start status` runs when `PROJECT-HOME.md` claims backbone is ready, but canonical intake
artifacts still show optioning as the active next step. Verifies that dashboard prose is read
as context only and cannot override canonical artifact state.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/
│   ├── intake.md
│   └── plan.md
└── PROJECT-HOME.md
```

`plan.md` records `options status: recommended`. `PROJECT-HOME.md` incorrectly says `backbone in-progress`
and suggests stories work can start next.

## Input Command

```text
ba-start status --slug test-project
```

## Expected Behavior

- Reads `PROJECT-HOME.md` as a dashboard only.
- Injects the canonical state summary from preflight instead of discovery-reading intake artifacts at runtime.
- Keeps runtime read scope compact: `PROJECT-HOME.md`, `project-memory.md` header, and `project-memory/index.md` when present.
- Reports the dashboard conflict.
- Keeps status aligned to the canonical optioning gate.
- Does not write any artifact.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start status |
| activation_level | Base |
| fallback_code | NONE |
| approval_gate | NOT_REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/01_intake/plan.md |
| read_scope | PROJECT-HOME.md + 02_backbone/project-memory.md + 02_backbone/project-memory/index.md |
| write_target | NONE |

## Guardrail Evidence

| Field | Expected Value |
| --- | --- |
| evidence_source | adapter manifest or runtime trace |
| preflight_status | ok |
| audit_status | pass |

## Notes

- This fixture fails parity if `PROJECT-HOME.md` overrides the canonical intake decision ledger.
- Golden: `goldens/g19-status-project-home-conflict.md`
