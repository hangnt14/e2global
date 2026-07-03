---
type: srs-states
module: "{module_slug}"
created: "{YYYY-MM-DD}"
owner: "{@handle}"
changelog:
  - {YYYY-MM-DD} | /srs | initial draft
---

# SRS States — {module_slug}

> Module state registry. States must align with UC flows and ASCII screen states traceable to backbone.

## State Registry

| State ID | Entity | State Name | Description | Entry Conditions | Exit Conditions | Owning Screen | Owning UC |
|---|---|---|---|---|---|---|---|
| {STATE-01} | {entity} | {name} | {description} | {condition} | {condition} | SCR-{NN} | UC-{slug} |

## State Transition Diagram

```mermaid
stateDiagram-v2
  [*] --> {STATE-01}: {trigger}
  {STATE-01} --> {STATE-02}: {event}
  {STATE-02} --> [*]: {terminal condition}
```
