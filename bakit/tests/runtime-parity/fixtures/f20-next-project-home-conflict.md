# Fixture F20: next Recommends Canonical Step Despite PROJECT-HOME Conflict

## Scenario

`ba-start next` runs when `PROJECT-HOME.md` says backbone work is next, but canonical intake
artifacts still require the options step. Verifies that next-step resolution trusts canonical
artifacts and only surfaces the dashboard as a warning source.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/
│   ├── intake.md
│   └── plan.md
└── PROJECT-HOME.md
```

`plan.md` records `options status: recommended`. `PROJECT-HOME.md` incorrectly recommends
`ba-start backbone --slug test-project`.

## Input Command

```text
ba-start next --slug test-project
```

## Expected Behavior

- Reads `PROJECT-HOME.md` as dashboard guidance only.
- Injects the canonical next-step summary from preflight instead of discovery-reading intake artifacts at runtime.
- Keeps runtime read scope compact: `PROJECT-HOME.md`, `project-memory.md` header, and `project-memory/index.md` when present.
- Warns about the dashboard conflict.
- Recommends `ba-start options --slug test-project`.
- Does not write any artifact.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start options |
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

- This fixture fails parity if `ba-start next` follows dashboard prose instead of the canonical plan gate.
- Golden: `goldens/g20-next-project-home-conflict.md`
