---
type: shared-staleness
project: "{slug}"
updated_at: "{YYYY-MM-DD}"
changelog:
  - {YYYY-MM-DD} | /impact | initial record
---

# Shared Staleness — {slug}

> Records stale artifacts and their refresh commands. Updated by impact approved writeback.

## Stale Artifacts

| Artifact | Path | Stale Since | Reason | Refresh Command | Status |
|---|---|---|---|---|---|
| {artifact} | {path} | {YYYY-MM-DD} | CR-{YYYYMMDD}-{NNN} | `ba-start {command} --slug {slug} --module {module}` | stale |

## Resolved

| Artifact | Path | Resolved On | Resolved By |
|---|---|---|---|
| {artifact} | {path} | {YYYY-MM-DD} | {command or manual} |
