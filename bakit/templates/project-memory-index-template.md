# Chỉ mục bộ nhớ dự án (Project Memory Index)

| Field | Value |
| --- | --- |
| artifact_profile | agent_facing |
| project | [Tên dự án] |
| slug | [initiative-slug] |
| date | [YYMMDD-HHmm] |
| mode | shard |
| last_updated | [YYYY-MM-DD] |
| updated_by_runtime | [claude-code / codex / antigravity] |
| stale_status | [current / stale / unknown] |

## Activation State

| Field | Value |
| --- | --- |
| activation_level | [Base / Modular / Program] |
| activation_status | [provisional / locked / frozen] |
| last_refresh | [YYYY-MM-DD / not-checked] |
| computed_signals | module_count=[n]; owner_count=[n]; cross_module_dependency=[true/false]; delegation_slice_count=[n] |

## Shard Registry

| Shard | Path | Status | Last Updated |
| --- | --- | --- | --- |
| Canonical Vocabulary | `hot/canonical-vocabulary.md` | [active/stale/empty] | [YYYY-MM-DD] |
| Approved Decisions | `hot/approved-decisions.md` | [active/stale/empty] | [YYYY-MM-DD] |
| Push-back Triggers | `hot/pushback-triggers.md` | [active/stale/empty] | [YYYY-MM-DD] |
| Memory Log | `log.md` | [active/not-initialized] | [YYYY-MM-DD] |

## Module Shards

| Module Slug | Path | Status | Owner |
| --- | --- | --- | --- |
| [module-slug] | `warm/modules/[module-slug].md` | [active/stale/empty] | [owner] |

## Owner Metadata

| Layer | Primary Owner | Role |
| --- | --- | --- |
| Global hot/ | [Lead BA] | Lead BA |
| Module: {module_slug} | [Module BA] | Module BA |

## Packet Registry

| Packet ID | Path | Status | Owner |
| --- | --- | --- | --- |
| PKT-01 | `delegation/packets/PKT-01.md` | [queued/running/completed/blocked/failed] | [owner] |
