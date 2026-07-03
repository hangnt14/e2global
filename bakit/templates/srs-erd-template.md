---
type: srs-erd
module: "{module_slug}"
created: "{YYYY-MM-DD}"
owner: "{@handle}"
erd_required: true
changelog:
  - {YYYY-MM-DD} | /srs | initial draft
---

# SRS ERD — {module_slug}

> Business data model. If ERD is not required for this module, set `erd_required: false` and leave this file as a stub.

## Entities

| Entity | Description | Key Attributes |
|---|---|---|
| {Entity} | {description} | {id, name, status, ...} |

## Relationships

| From | Relationship | To | Cardinality |
|---|---|---|---|
| {Entity A} | has many | {Entity B} | 1..N |

## ERD Diagram

```mermaid
erDiagram
  {ENTITY_A} {
    string id
    string name
  }
  {ENTITY_B} {
    string id
    string entity_a_id
  }
  {ENTITY_A} ||--o{ {ENTITY_B} : "has many"
```
