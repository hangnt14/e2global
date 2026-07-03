# ba-qc-export Bridge Skill — Design Note

**Origin:** QC-kit compatibility analysis, 2026-05-29

## Purpose

Export BA-kit canon artifacts into QC-kit's expected input format (`docs/BA/<UC-ID>/<UC-ID>.md` per UC). One-way bridge. BA-kit canon set remains source of truth.

## Context

- **QC-kit repo:** https://github.com/Sotatek-PhuongTran/qc-kit
- **QC-kit expects:** monolithic per-UC markdown files with 6 fixed sections + supplementary PNGs in `docs/BA/<UC-ID>/`
- **BA-kit produces:** structured canon set (`usecases/uc-*.md`, `screens/*.md`, `srs/spec.md`, `userstories/us-*.md`) per module, compiled into `srs.md`
- **QC-kit's Phase A** (project onboarding, context master, site map, dashboard) is QC's responsibility — export bridge only handles the per-UC artifact handoff

## What the Bridge Does

### Input
- Direct canon sources: `usecases/uc-*.md`, `ascii-screen/*.md`, `srs/spec.md`, `userstories/us-*.md`
- Module compiled SRS from `plans/{slug}-{date}/03_modules/{module_slug}/srs.md` as fallback/supporting evidence only
- `common-rules.md` and `message-list.md` from `02_backbone/`
- Any PNG design assets placed in screen folders

### Output (default: plan-scoped)

```
plans/{slug}-{date}/04_compiled/qc-kit/
  qc-export-summary.json     ← export manifest
  docs/BA/
    Common rule/
      common-rules.md         ← resolved codes to text
      message-list.md         ← resolved message codes to text
    {module_slug}/
      UC-{slug}.md             ← 6-section monolithic UC doc
      UC-{slug}-screens/*.png  ← design images (if placed by BA)
      usecase-list.md          ← optional, with --usecase-list

External mirror only via explicit --external-output <dir>.
```

### Transformation Steps

1. **Read UC canon** — iterate `usecases/uc-*.md` per module; compiled `srs.md` is fallback/supporting evidence only
2. **Map sections** from BA-kit structure to QC-kit's 6-section format
3. **Resolve codes** — replace CR-VAL-NN, MSG-ERR-NN, BR-xxx with exact text from common files
4. **Embed linked screens** — only screens referenced in UC trace, with field tables and states
5. **Include ACs** — from linked user stories
6. **Copy PNG assets** — any design images placed by BA in screen folders
7. **Assemble cross-references** — aggregate all rule/message codes used, with resolved text

### Section Mapping

| QC-kit section | BA-kit source |
|---------------|---------------|
| Header block | UC frontmatter + source path metadata |
| §1 Use Case Description | UC: actors, preconditions, trigger, main/alternate/error flows, postconditions, business rules |
| §2 Screen Description | Screens linked to UC: field tables, user actions, states, ASCII wireframes, PNG assets |
| §3 Validation Summary | Screen field validation rules + message codes resolved to text |
| §4 Cross-References | FR table, BR table, common rules, message list, **cross-function dependencies** (from `## Cross-Function Impact` in UC) |
| §5 Open Questions | UC `## Open Questions` |
| §6 Changelog | Aggregated changelog from all contributing artifacts |

### Cross-Function Data in §4

BA-kit UC `## Cross-Function Impact` section maps to a `### Functional Integration` subsection within §4 Cross-References:

```markdown
### Functional Integration

#### Dependencies (this UC needs)
| Source UC / Module | Data / State | Type | Status |
|--------------------|--------------|------|--------|
| UC-cart / payment | cart_id, cart_items | Input | Resolved |
| FEAT-AUTH-03 / auth | user_id, token | Input | Resolved |

#### Consumers (this UC provides for)
| Target UC / Module | Data / State | Type | Status |
|--------------------|--------------|------|--------|
| UC-tracking / payment | order_id, order_status | Output | Resolved |
| FEAT-SHP-01 / shipping | order_id, order_status | Output | Expected: TBD |
```

**Export rules:**
1. **Resolved** dependencies → appear with full details, Status = "Resolved"
2. **Pending** "produces for" → appear as "Expected: TBD" with backbone feature ID — QC-kit treats as known limitation
3. **Pending** "consumes from" → appear as "Expected: TBD" with backbone feature ID
4. **Mismatches** → appear with Status = "Mismatch" and conflict description
5. **No cross-function section** in UC → no Functional Integration subsection in §4

### What the Bridge Does NOT Do

- Generate PNG exports (BA places designs manually)
- Build QC-kit's project config or context master (QC's job)
- Create QC-kit's site map or dashboard (QC's job)
- Cross-function dependencies are exported from `## Cross-Function Impact` UC declarations; pending inter-module edges appear as "Expected: TBD" — full resolution requires both modules to be authored
- Enumerate atomic UI elements (QC-kit's agent does this from screen descriptions + PNGs)

## Known Gaps in Export

| Gap | Impact on QC-kit | Mitigation |
|-----|-----------------|------------|
| No PNG designs placed yet | KA #5 visual enumeration can't run | QC-kit skips image verification; uses text-based screen descriptions |
| Partial cross-function dependency resolution (§4) | KA #8 may score Partial when inter-module edges are pending | Export includes cross-function data from `## Cross-Function Impact`; resolved edges appear fully, pending dependencies appear as "Expected: TBD" — QC-kit treats as known limitation |
| AC not categorized by Interface/Function/Integration | AC synthesis less granular | QC-kit's agent categorizes from existing AC text |

## Decisions

- Export is manual/on-demand; it does not auto-run after `package`.
- Default output is one folder per UC under plan-scoped `04_compiled/qc-kit/docs/BA/`.
- `usecase-list.md` is optional via `--usecase-list`.
- External mirror is explicit via `--external-output <dir>`; the exporter appends `docs/BA/` below that root.

## Open Questions

- Does the bridge need to handle incremental updates (re-export single UC), or always full module?
- Does QC-kit's `input-files-format.md` need updating for BA-kit's section naming conventions?

## Related

- Cross-function analysis note: `docs/cross-function-impact-analysis-note.md`
- QC-kit repo: https://github.com/Sotatek-PhuongTran/qc-kit
- BA-kit qc-uc-review skill: `skills/qc-uc-review/`
- UC template: `templates/usecase-item-template.md`
- Compiled SRS template: `templates/srs-template.md`
