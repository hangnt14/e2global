# Fixture F12: Packet Needs Repartition

## Scenario

A delegated worker receives an underspecified memory packet. Verifies that runtimes return
`NEEDS_REPARTITION` instead of reading the full memory tree or mutating outside the packet.

## Input State

```text
plans/test-project-20260424/
├── delegation/packets/PKT-01.md
├── 02_backbone/backbone.md
└── 02_backbone/project-memory/
    ├── index.md
    ├── hot/approved-decisions.md
    └── warm/modules/export.md
```

`PKT-01.md` lacks the exact upstream excerpt needed to complete the assigned section.

## Input Command

```text
Read delegation/packets/PKT-01.md and complete the assigned worker task.
```

## Expected Behavior

- Reads only the packet.
- Does not open the full memory tree, full backbone, or unrelated artifacts.
- Does not write any target file.
- Returns `NEEDS_REPARTITION` with the missing minimum input.

## Expected Outcome

| Field | Expected Value |
| --- | --- |
| resolved_command | NEEDS_REPARTITION |
| activation_level | Program |
| fallback_code | NEEDS_REPARTITION |
| approval_gate | NOT_REQUIRED |
| source_of_truth_artifact | plans/test-project-20260424/delegation/packets/PKT-01.md |
| read_scope | plans/test-project-20260424/delegation/packets/PKT-01.md |
| write_target | NONE |
| must_not_read | plans/test-project-20260424/02_backbone/backbone.md, plans/test-project-20260424/02_backbone/project-memory/ |

## Notes

- This fixture fails parity if a worker compensates for a bad packet by scanning canonical memory.
- Golden: `goldens/g12-packet-needs-repartition.md`
