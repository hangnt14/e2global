---
type: srs-spec
module: "{module_slug}"
created: "{YYYY-MM-DD}"
owner: "{@handle}"
source_backbone_ids: []
changelog:
  - {YYYY-MM-DD} | /srs | initial draft
---

# SRS Spec — {module_slug}

> Source file. Not a compiled deliverable. Edit here; compile to `srs.md` via `ba-start srs`.

## Functional Requirements

| ID | Description | Priority | Trace |
|---|---|---|---|
| FR-{module}-001 | {requirement} | P0 | {backbone-id} |

## Non-Functional Requirements

| ID | Category | Description | Threshold | Trace |
|---|---|---|---|---|
| NFR-{module}-001 | {performance/security/usability} | {requirement} | {threshold} | {backbone-id} |

## Business Rules

| Rule Code | Description | Scope | Trace |
|---|---|---|---|
| CR-VAL-01 | {rule} | {screens/UCs} | {backbone-id} |

## API / Integration Constraints

| Integration | Direction | Description |
|---|---|---|
| {service} | inbound/outbound | {constraint} |

## Data Constraints

| Entity | Field | Constraint |
|---|---|---|
| {entity} | {field} | {constraint} |

## Common Rules Reference

See `02_backbone/common-rules.md` for shared rule codes.

## Message List Reference

See `02_backbone/message-list.md` for shared message codes.
