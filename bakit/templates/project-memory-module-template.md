# Bộ nhớ Module (Module Memory Shard) — Warm Tier

| Field | Value |
| --- | --- |
| artifact_profile | agent_facing |
| project | [Tên dự án] |
| slug | [initiative-slug] |
| module_slug | [module-slug] |
| owner | [requirements-engineer / ui-ux-designer / ba-documentation-manager] |
| module_status | [in-progress / completed / on-hold / blocked] |
| last_updated | [YYYY-MM-DD] |
| stale_status | [current / stale / unknown] |

## Module Scope

| Field | Value |
| --- | --- |
| summary | [1-2 line module scope] |
| source_artifact | [backbone/frd/stories/srs path] |

## Key Module Decisions

| Decision ID | Decision | Source | Impact |
| --- | --- | --- | --- |
| MOD-DEC-01 | [short module decision] | [user/backbone/impact] | [frd, stories, srs] |

## Cross-Module Dependencies

| Module | Dependency Type | Artifact | Status |
| --- | --- | --- | --- |
| [module-slug] | [data-contract/shared-actor/shared-rule/integration] | [FR/SCR/ACT] | [resolved/pending/blocked] |

## Trace Links

| Artifact | Path | Status |
| --- | --- | --- |
| FRD | `03_modules/[module-slug]/frd.md` | [exists/missing] |
| User Stories | `03_modules/[module-slug]/userstories/index.md` | [exists/missing] |
| SRS | `03_modules/[module-slug]/srs.md` | [exists/missing] |
| Screen Canon ASCII | `03_modules/[module-slug]/ascii-screen/*.md` | [current/missing/stale] |

## Open Issues

| Issue ID | Description | Blocking | Action |
| --- | --- | --- | --- |
| MOD-ISS-01 | [short issue] | [yes/no] | [impact/user/escalate] |

## Promotion Trace

| Record ID | Promoted At | Approved By | Source Artifact |
| --- | --- | --- | --- |
| FB-YYMMDD-01 | [YYYY-MM-DD] | [approver] | [path] |
