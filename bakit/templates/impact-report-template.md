---
type: impact-report
change_id: "CR-{YYYYMMDD}-{NNN}"
status: draft
created: "{YYYY-MM-DD}"
owner: "{@handle}"
changelog:
  - {YYYY-MM-DD} | /impact | initial analysis
---

# Impact Report — CR-{YYYYMMDD}-{NNN}

## Change Summary

{One-paragraph summary of the change and its business driver.}

## Affected Artifact Classification

| Artifact | Path | Impact Type | Rerun Command |
|---|---|---|---|
| backbone | `02_backbone/backbone.md` | {scope/actor/rule change} | `ba-start backbone --slug {slug}` |
| userstories/index.md | `03_modules/{module}/userstories/index.md` | {story scope change} | `ba-start stories --slug {slug} --module {module}` |
| usecases/uc-{slug}.md | `03_modules/{module}/usecases/uc-{slug}.md` | {behavior change} | `ba-start srs --slug {slug} --module {module}` |
| ascii-screen/{screen}.md | `03_modules/{module}/ascii-screen/{screen}.md` | {UI state change} | `ba-start srs --slug {slug} --module {module}` |
| srs/spec.md | `03_modules/{module}/srs/spec.md` | {FR/NFR/BR change} | `ba-start srs --slug {slug} --module {module}` |
| shared/traceability.md | `shared/traceability.md` | {traceability update} | manual refresh |

## Stale Artifacts

See `shared/staleness.md` for full stale artifact list and refresh commands.

## Reverse Lane Classification

| Item | Lane | Notes |
|---|---|---|
| {item} | as_built_drift / future_state_request / mixed_change | {notes} |

## Recommended Rerun Sequence

1. {step 1 — narrowest owning layer first}
2. {step 2}
3. {step 3}

## Open Questions

- [ ] OQ-1: {question}
