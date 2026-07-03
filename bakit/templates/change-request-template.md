---
type: change-request
change_id: "CR-{YYYYMMDD}-{NNN}"
slug: "{change-slug}"
status: draft
classification: "{backbone_scope_change|story_change|usecase_change|screen_change|srs_spec_change|shared_change}"
created: "{YYYY-MM-DD}"
owner: "{@handle}"
changelog:
  - {YYYY-MM-DD} | /impact | initial CR note
---

# CR-{YYYYMMDD}-{NNN}: {change title}

## Change Statement

{Describe the change in plain business language. What changed, was added, or was removed.}

## Classification

- Type: {backbone_scope_change | story_change | usecase_change | screen_change | srs_spec_change | shared_change}
- Affected layer: {backbone | userstories | usecases | ascii-screen | srs/spec | srs/flows | srs/states | srs/erd | shared}

## Affected Artifacts

| Artifact | Path | Change Type |
|---|---|---|
| {artifact name} | {path} | {add/modify/remove} |

## Business Justification

{Why this change is needed. Stakeholder, regulatory, or product driver.}

## Approval

- Requested by: {name}
- Approved by: {name}
- Approved on: {YYYY-MM-DD}

## Impact Report

See `impacts/CR-{YYYYMMDD}-{NNN}-impact.md`.
