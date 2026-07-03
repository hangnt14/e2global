---
type: shared-traceability
project: "{slug}"
generated_at: "{YYYY-MM-DD}"
stale_status: unknown
changelog:
  - {YYYY-MM-DD} | /srs | initial generation
---

# Shared Traceability — {slug}

> Maps backbone → userstories → usecases → screens/SRS source. Updated after each module SRS run.

## Traceability Matrix

| Backbone ID | Feature / Scope | Story ID | Use Case ID | Screen ID | SRS Spec FR | Status |
|---|---|---|---|---|---|---|
| {backbone-id} | {feature} | US-{module}-001 | UC-{module}-{slug} | SCR-01 | FR-{module}-001 | current |

## Coverage Gaps

| Gap Type | ID | Missing Link | Notes |
|---|---|---|---|
| story_without_uc | US-{module}-{NNN} | No linked use case | {notes} |
| uc_without_screen | UC-{module}-{slug} | No linked screen | {notes} |
| screen_without_story | SCR-{NN} | No linked story | {notes} |
