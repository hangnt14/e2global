# Fixture F17: stories Guardrail Enforces backbone-index First

## Scenario

Explicit `ba-start stories` runs for module `auth-flow` with a current `backbone-index.md`.
Verifies that user-story discovery starts from the backbone index and does not broad-read
the full backbone even when a module artifact is about to be authored.

## Input State

```text
plans/test-project-20260424/
├── 01_intake/
│   └── plan.md
├── 02_backbone/
│   ├── backbone.md
│   └── backbone-index.md
└── 03_modules/auth-flow/
    └── MODULE-HOME.md
```

`backbone-index.md` metadata is current and routes module `auth-flow` to a targeted backbone slice.

## Input Command

```text
ba-start stories --slug test-project --module auth-flow
```

## Expected Behavior

- Reads `core/contract.yaml` and `core/contract-behavior.md`.
- Reads `02_backbone/backbone-index.md` before any backbone content lookup.
- May read `03_modules/auth-flow/frd.md` only if it already exists and the mode justifies it.
- May use a generated excerpt derived from the routed anchor.
- Does not discovery-read full `02_backbone/backbone.md`.
- Writes `03_modules/auth-flow/user-stories.md`.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | ba-start stories |
| activation_level | Base |
| fallback_code | NONE |
| approval_gate | NOT_REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/backbone.md |
| read_scope | core/contract.yaml + core/contract-behavior.md + 01_intake/plan.md + 02_backbone/backbone-index.md |
| write_target | plans/test-project-20260424/03_modules/auth-flow/user-stories.md |

## Guardrail Evidence

| Field | Expected Value |
| --- | --- |
| evidence_source | adapter manifest or runtime trace |
| preflight_status | ok |
| audit_status | pass |

## Notes

- This fixture fails parity if a runtime discovery-reads `backbone.md` before honoring the index.
- Golden: `goldens/g17-stories-guardrail-index-first.md`
