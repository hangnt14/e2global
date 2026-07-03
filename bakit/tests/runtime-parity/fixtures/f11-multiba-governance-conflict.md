# Fixture F11: Multi-BA Governance Conflict

## Scenario

A module BA attempts to change a global hot-shard decision while another module depends
on the existing decision. Verifies that runtimes stop and escalate instead of guessing
or writing through the module scope.

## Input State

```text
plans/test-project-20260424/
├── 02_backbone/
│   ├── backbone.md
│   └── project-memory/
│       ├── index.md
│       ├── hot/approved-decisions.md
│       └── warm/modules/
│           ├── export.md
│           └── billing.md
└── 03_modules/export/
    └── user-stories.md
```

`approved-decisions.md` is owned by Lead BA. The export Module BA proposes changing a
shared retention rule that billing also uses.

## Input Command

```text
ba-start stories --slug test-project --module export
```

## Expected Behavior

- Detects that the requested change touches global/cross-module memory.
- Does not mutate export stories or hot shards.
- Emits `GOVERNANCE_CONFLICT` and escalates to Lead BA.
- Requires Lead BA approval and an impact rerun before any mutation.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | STOP |
| activation_level | Program |
| fallback_code | GOVERNANCE_CONFLICT |
| approval_gate | LEAD_BA_REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/02_backbone/project-memory/hot/approved-decisions.md |
| read_scope | plans/test-project-20260424/02_backbone/backbone.md, plans/test-project-20260424/02_backbone/project-memory/index.md, plans/test-project-20260424/02_backbone/project-memory/hot/approved-decisions.md, plans/test-project-20260424/02_backbone/project-memory/warm/modules/export.md, plans/test-project-20260424/02_backbone/project-memory/warm/modules/billing.md |
| write_target | NONE |
| visible_warning | GOVERNANCE_CONFLICT |

## Notes

- This fixture is the simulated multi-module, multi-BA conflict pilot.
- Golden: `goldens/g11-multiba-governance-conflict.md`
