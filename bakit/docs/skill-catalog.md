# BA-kit Skill Catalog

## Purpose

This catalog explains the BA-kit workflow skill plus the maintenance skills that support packaging, publishing, and runtime upkeep.

## Skill

| Skill | When to Use | Related Templates | Related Agents | Typical Output |
| --- | --- | --- | --- | --- |
| `ba-start` | Full BA engagement, reverse as-built analysis, or resumable step-level reruns from raw input to packaged deliverables | `project-home-template.md`, `intake-form-template.md`, `requirements-backbone-template.md`, `frd-template.md`, `userstory-item-template.md`, `userstories-index-template.md`, `srs-template.md`, `srs-spec-template.md`, `usecase-item-template.md`, `ascii-screen-template.md`, `design-md-template.md` | `requirements-engineer`, `ui-ux-designer`, `ba-documentation-manager`, `ba-researcher` | Project Home dashboard, intake form, option pack + comparison when needed, requirements backbone, gated FRD/stories/SRS artifacts, canon screen/use case/data sources with mandatory ASCII, routing indexes, compiled SRS deliverable, reverse evidence lane, project runtime `DESIGN.md`, FRD/SRS HTML, quality review, artifact status |
| `brainstorm` | Pre-intake idea clarification — capture and expand a raw idea through a 7-section deep interview before entering the BA lifecycle | `brainstorm-template.md` | None | Structured brainstorm doc with flows, ASCII diagrams, scenario matrix, state transitions, interrupted-tx handling, exact wording, open questions |
| `ba-collab` | Module ownership, review packets, conflict checks, and approval-gated GitHub handoff | `collab-home-template.md`, `module-home-template.md`, `review-packet-template.md` | Lead BA / Module BA roles | Collab Home, Module Home, review packet, optional approved PR handoff |
| `qc-uc-review` | Module-level QC audit after `ba-start srs` or when a BA explicitly asks for readiness review | QC report template + backlog conventions under `skills/qc-uc-review/` | QA/Test Lead | Module-scoped QC report, verdict, blockers, question backlog |
| `ba-kit-update` | Update the installed BA-kit runtime assets from the registered source repo | None | None | One-command fast-forward update and reinstall |
| `ba-notion` | Publish an exact BA markdown artifact into Notion via MCP | None | None | Notion page created or updated from BA source content |
| `ba-figma-sync` | Downstream Figma canvas sync from approved screen canon, shared shell contract, and `DESIGN.md` | `figma-sync-report-template.md`, `figma-mismatch-report-template.md` | ui-ux-designer | Figma frames, sync report, mismatch report. Must not mutate BA canon. |
| `ba-content-audit` | Read-only cross-artifact format + cross-reference consistency audit for BA-kit projects | `audit-report-template.md` | Lead BA / Module BA | Audit report at `shared/audit-report.md` with Blocking/Warning/Info findings |

## Workflow

`/brainstorm` is the pre-intake idea exploration tool:

1. Auto-derive feature slug and idea slug from idea content
2. Detect complexity signals (external redirect, multi-role, state machine, throttle rules)
3. Run 7-section deep interview (one section at a time, not batched)
4. Synthesize answers into 13-section structured document
5. Quality checklist gate before write
6. Resolve open questions with cascade scan

Output: `docs/{feature}/brainstorms/{idea-slug}.md`

After brainstorm, feed the output into `/ba-start intake` as source material.

`/ba-start` with no subcommand handles the forward BA lifecycle:

1. Accept raw input (file or text)
2. Parse and normalize into intake form
3. Create or refresh `PROJECT-HOME.md` as the BA-facing dashboard
4. Gap analysis and clarifying questions
5. Scope lock and engagement-mode selection (`lite`, `hybrid`, `formal`)
6. Option pack + comparison when intake needs multiple solution directions before backbone
7. Requirements backbone production
8. Gated FRD and user story generation
9. Selective use case and Screen Contract Plus production when needed
10. Design decision capture and project runtime `DESIGN.md` creation when UI support is justified
11. Canon-first SRS authoring into module `ascii-screen/*.md`, `usecases/*.md`, `srs/*.md`, and their indexes
12. Compiled `srs.md` production as the full reader-facing deliverable with screen descriptions and ASCII wireframes
13. Automatic module QC review after `srs` using canon-first evidence and module-scoped QC outputs
14. Optional downstream Figma sync from canon screen files and shared shell contract
15. Unified browser-editable HTML packaging and aggregate validation across the emitted artifacts

`/ba-start reverse` is the as-built lane. It scans committed source files, locks a baseline commit, and builds an evidence-backed reverse index before any canonical BA artifact is updated. Future-state asks do not belong in this lane; route them through `impact` or the normal forward lifecycle. Reverse mode treats wireframes as skipped / not-applicable because it documents the current implemented system rather than proposing UI changes.

## Invocation

```text
/brainstorm
/brainstorm <idea text>
/brainstorm @<file-path>
/brainstorm <idea text> --shallow
/brainstorm <idea text> --lang en

/ba-start
/ba-start intake <file>
/ba-start options --slug <slug>
/ba-start options --slug <slug> --select option-02
/ba-start options --slug <slug> --skip
/ba-start backbone --slug <slug>
/ba-start frd --slug <slug> --module <module_slug>
/ba-start stories --slug <slug> --module <module_slug>
/ba-start srs --slug <slug> --module <module_slug>
/ba-start package --slug <slug>
/ba-start status --slug <slug>
/ba-notion srs --slug <slug> --page <url|id> --mode overwrite
/ba-figma-sync --slug <slug> --module <module_slug>
/ba-content-audit --slug <slug>
/ba-content-audit --slug <slug> --date <YYMMDD-HHmm>
/ba-start reverse --slug <slug> [--focus <area>] [--commit <hash>]
/ba-start reverse status --slug <slug>
/ba-start reverse refresh --slug <slug> [--commit <hash>]
/ba-start reverse promote --slug <slug> --evidence-ids <id,...>
/ba-start reverse impact --slug <slug> [--evidence-ids <id,...>]
```

## Subcommands

| Command | Purpose | Prerequisite |
| --- | --- | --- |
| `intake` | Parse input, normalize intake, save Project Home, and save the work plan | Raw file or pasted text |
| `options` | Generate or review the pre-backbone option pack, comparison, and explicit select/skip decision | Matching intake artifact |
| `backbone` | Build the persisted source-of-truth artifact after scope lock and refresh Project Home | Matching intake artifact |
| `frd` | Produce the FRD and FRD HTML only when the gate is open | Matching backbone artifact |
| `stories` | Produce user stories only | Matching backbone artifact |
| `srs` | Produce folder-based SRS sources, use cases, mandatory ASCII screens, routing indexes, and compiled `srs.md` | Matching backbone and user stories |
| `wireframes` | Deprecated compatibility validation for existing screen canon ASCII | Current `ascii-screen/index.md`, screen canon, and compile receipt |
| `ba-figma-sync` | Sync approved SRS screen canon to Figma through Figma MCP and write sync/mismatch reports | Current `ascii-screen/index.md`, `srs-compile-receipt.json`, screen canon, `DESIGN.md`, and shared shell contract |
| `package` | Run aggregate validation, validate existing packaged HTML artifacts, and regenerate only the needed packaged outputs | Emitted artifact set and non-missing wireframe state |
| `status` | Print artifact checklist with dates | Resolved slug and dated set |
| `reverse` | Scan committed source files, lock the baseline commit, and build the reverse evidence index | None (creates `00_reverse/` lane) |
| `reverse status` | Print reverse lane progress: baseline lock, index freshness, evidence counts, drift state | `reverse_baseline_lock` |
| `reverse refresh` | Re-scan against a new commit and update drift state | `reverse_baseline_lock` |
| `reverse promote` | Promote validated `as_built_drift` evidence to canonical backbone or SRS | `reverse_baseline_lock`, `reverse_evidence_ledger`, `--evidence-ids` |
| `reverse impact` | Classify evidence entries as `as_built_drift`, `future_state_request`, or `mixed_change` | `reverse_baseline_lock`, `reverse_focus_excerpts` |

Subcommand targeting rules:

- Use `--slug <slug>` first when rerunning an existing project.
- If exactly one slug exists in the modular `plans/{slug}-{date}/` tree, BA-kit may use it automatically.
- If multiple slugs exist, BA-kit should stop and ask the user to choose.
- If one slug has multiple dated artifact sets, BA-kit should stop and ask which dated set to use.

## Agent Delegation

| Agent | Role in Workflow |
| --- | --- |
| `requirements-engineer` | Backbone, FRD, user stories, use cases, Screen Contract Plus, canon screen descriptions, compiled SRS sections |
| `ui-ux-designer` | Runtime `DESIGN.md`, shared-shell decisions, mandatory screen canon ASCII, and downstream Figma/visual consumers |
| `ba-documentation-manager` | Validation pack, quality review, consistency, packaging |
| `ba-researcher` | Domain research when external context is needed |

Delegation is intentionally partitioned. Large SRS work should be split into grouped slices and passed downstream as narrow handoff packets with exact excerpts and trace IDs, not as full merged artifacts. If one delegated slice becomes too large to keep consistent, repartition and rerun only that slice.

Use [`templates/sub-agent-handoff-template.md`](../templates/sub-agent-handoff-template.md) as the default packet structure when delegation is non-trivial.
For non-trivial delegated work, also create a tracker under `plans/{slug}-{date}/delegation/` so `/ba-start status` can expose `queued`, `running`, `blocked`, `needs-repartition`, `completed`, or likely stalled slices.

## HTML Editing

Packaged HTML artifacts are meant to be edited in the browser. Update copy, swap images, and add or remove blocks directly in the rendered HTML instead of hand-editing source HTML.

If the user manually inserts wireframe images or links into the markdown source, the packaged HTML preserves those references only when the asset path stays inside the allowed base directory. Mermaid diagrams are rendered explicitly after the DOM is ready, and PlantUML diagrams always prefer local rendering. Use `ba-kit install-plantuml` or the renderer's `--auto-install-plantuml` option before falling back to a configured server.

`/ba-start status` reports `PROJECT-HOME.md` first, then regular artifacts with dates. For SRS modules it must show `userstories/index.md`, `usecases/index.md`, `ascii-screen/index.md`, counts under `ascii-screen/`, `usecases/`, and `srs/`, compiled `srs.md`, receipt, ASCII coverage, and module QC outputs. Shared shell files are reported separately.

`qc-uc-review` reads module canon sources first: `usecases/index.md`, `ascii-screen/index.md`, `usecases/*.md`, `ascii-screen/*.md`, `screen-field-contract.yaml`, then compiled `srs.md` and receipt as supporting evidence. Automatic QC fires after module `srs`.

`wireframes` is compatibility validation only. It must not emit legacy handoff artifacts and must not act as the primary `qc-review` trigger.

Runtime guardrail helpers:

- `ba-kit doctor-srs <module_root>` validates ASCII screen index paths, screen canon schema, required screen sections, Behaviour Rules format, source-of-truth invariants, and compile receipt presence.
- `ba-kit check-write-scope --command <command> <path>...` blocks downstream commands such as `figma-sync` and `package` from mutating canon files.
- `ba-kit check-srs-index`, `ba-kit check-screen-canon`, and `ba-kit check-source-of-truth` expose the narrow validators for hooks and CI.

## Expected Quality Bar

- Outputs reference business goals
- Backbone decisions explain why downstream artifacts were emitted or skipped
- Every requirement has acceptance criteria
- Use cases cover primary and alternate flows
- Screen descriptions use field tables with Display/Behaviour/Validation rules
- Approved `DESIGN.md` decisions are reflected in the shared shell contract, canon screen sources, and any user-supplied wireframes or downstream Figma outputs
- Every SRS requirement, use case, and screen traces to user stories
- Diagrams use PlantUML for swimlanes and Mermaid for the rest
- Risks, assumptions, and open questions are visible
