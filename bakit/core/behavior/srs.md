# SRS Behavior

## Read Scope

- Must read: `core/contract.yaml`, `core/contract-behavior.md`, `paths.backbone_index`, `paths.userstories_index`, and `skills/ba-start/steps/srs.md`.
- May read: targeted `paths.backbone` and userstory item sections, `paths.srs_spec` when refreshing, `paths.project_memory` or hot shards, module warm shard, and `paths.frd` when it exists.
- Must not read: `log.md`, `cold/`, other module shards, full `paths.backbone`, or full userstory files when indexes are current.

Re-entry after long sessions, reruns, or host auto-compact still starts with `paths.backbone_index`, then `paths.userstories_index`, before reopening targeted source sections.

## Backbone Authority

Before writing any SRS source artifact, validate backbone alignment:
- UC actor, trigger, main outcome, and linked story must trace to backbone scope → `BACKBONE_ALIGNMENT_FAIL: usecase_scope`
- Portal, nav schema, active menu, actor, screen goal must trace to backbone/shared shell → `BACKBONE_ALIGNMENT_FAIL: screen_scope`
- FR/NFR/BR terms and rules must trace to backbone, shared definitions, or approved CR → `BACKBONE_ALIGNMENT_FAIL: srs_spec_scope`
- Module/system flow must not introduce cross-module behavior outside backbone → `BACKBONE_ALIGNMENT_FAIL: flow_scope`
- State lifecycle must align with UC and ASCII screen states traceable to backbone → `BACKBONE_ALIGNMENT_FAIL: state_scope`

Recovery: route through `ba-start impact` or backbone refresh, then rerun.

## Source Set

SRS authoring uses a folder-based source set. Do not create `srs-index.md`, `screens/`, `data/`, `flows/`, or `srs-groups/`.

- `srs/spec.md` — FR/NFR/business rules/API/data constraints
- `srs/flows.md` — module/system flows only (not UC-level diagrams)
- `srs/states.md` — module state registry
- `srs/erd.md` — business data model when justified
- `usecases/index.md` + `usecases/uc-{slug}.md` — use case canon
- `usecases/diagrams.md` — UC-specific diagrams
- `ascii-screen/index.md` + `ascii-screen/{screen}.md` — screen canon with mandatory ASCII wireframes
- `srs.md` — compiled output only (requested-scope compile)
- `srs-compile-receipt.json` — receipt with compile scope and source hashes

## Partial Compile Semantics

```
full: compile all source files
spec: compile srs/spec.md only
usecases: compile usecases/index.md + selected UC files + diagrams
screens: compile ascii-screen/index.md + selected screen files
flows: compile srs/flows.md
states: compile srs/states.md
erd: compile srs/erd.md
mixed: compile user-requested combination
```

Receipt must define `compile_scope`, `requested_sections`, `included_sources`, `excluded_sources`, and `source_hashes`.

## Navigation And Screen Contract Rules

- Reverse-mode carveout: when `paths.reverse_baseline_lock` exists and reverse-backed SRS work is active,
  do not require `paths.design_doc` as a prerequisite for screen authoring.
  Instead require current reverse evidence and route any future-state UI request back through `impact`.
- **DESIGN.md is a system-level prerequisite owned by Lead BA.** Module BA may augment nav items in existing portals with user confirmation. Portal-level changes escalate hard.
  Two-tier change authority:

| Level | Scope | Who | Gate |
|-------|-------|-----|------|
| **L1 - Portal** | New portal, new nav schema, new shell variant, new shared component | Lead BA only | Hard — `DESIGN_GAP` → stop → escalate via `impact` |
| **L2 - Nav Item** | Add/modify menu items in an existing nav schema whose portal is already in DESIGN.md | Module BA with user confirm | Soft — `MENU_ITEM_GAP` → ask user → add to DESIGN.md → flag in review packet |

  **L1 checks — stop and escalate:**
  - If `paths.design_doc` is missing entirely: `DESIGN_GAP: design_doc missing` → escalate to Lead BA.
  - If the module's portal is not in DESIGN.md §2: `DESIGN_GAP: {portal_id} not found` → escalate to Lead BA.

  **L2 checks — Module BA may resolve:**
  - If portal exists but a needed menu item is absent: `MENU_ITEM_GAP: {screen_id} needs "{active_item}" in {portal_id}/{nav_schema_id}`.
    - Module BA: ask user "Thêm menu item '{active_item}' vào {portal_id}/{nav_schema_id} trong DESIGN.md?"
    - User confirms → add item to DESIGN.md Navigation Schema + shared-shell-contract → flag in review packet.
    - User declines → stop, escalate to Lead BA.
  - If a structural nav schema issue exists (schema ID mismatch, missing schema entirely): `MENU_SCHEMA_GAP` → escalate to Lead BA (L1).
  - Module BA MUST NOT create new portals, new nav schemas, or new shell variants in DESIGN.md.
- Every screen in the same `Portal ID` must reuse the same `Nav Schema ID` unless an explicit exception is declared.
- Overlay screens inherit the parent portal unless an explicit cross-portal transition is documented.
- If modal, dialog, drawer, or overlay screens hide global navigation, set `Navigation Region Visible` to `No` and state the exception reason.
- Primary screens must link to use cases and user stories and define portal, role, nav schema, active menu, navigation visibility, breadcrumbs/back behavior, entry/exit conditions, actions, and states.
- Behaviour Rules in screen field tables MUST use business language describing navigation targets (`SCR-*`), overlay actions (open/close), and user-visible feedback (toast/banner/inline message with `MSG-*`). They MUST NOT contain API paths, HTTP methods, endpoint URLs, or framework-specific function names. Technical language in Behaviour Rules is a hard contract violation: `BEHAVIOUR_FORMAT_VIOLATION`.

Run `python3 scripts/validate-navigation-consistency.py --design {paths.design_doc} $(find {paths.ascii_screen_root} -name '*.md' ! -name 'index.md' | sort | sed 's/^/--screen-contract /')` after screen authoring when UI-backed screens exist. Treat `NAV_SCHEMA_MISMATCH`, `MENU_SCHEMA_MISMATCH`, and `MENU_ACTIVE_MISSING` as blocking.

## ASCII Wireframe Gates

- Reverse-mode carveout: if reverse evidence is the active gate, skip ASCII generation and cite evidence instead.
- In reverse mode, canonical SRS writes must cite reverse evidence and trace IDs before promotion.
- Build `paths.screen_field_contract` after screen authoring when UI-backed screens exist. This artifact is the normalized machine-facing truth derived from screen canon.
- `paths.screen_field_contract` must preserve exact `Portal ID`, `Nav Schema ID`, `Expected Active Menu Item`, field allowlists, required states, Display / Behaviour / Validation rules, rule codes, message codes, and short raw excerpts when prose cannot be normalized safely.
- `paths.screen_field_contract` is owned by `srs`, not by downstream wireframe tool lanes.
- Every UI-backed `ascii-screen/*.md` file must include `## ASCII Wireframe`, at least one ASCII subsection per required state, and `ascii_status: current` before SRS assembly is accepted.
- Manual mockup insertion is out-of-band and optional; it must not replace the required ASCII wireframe in screen canon.
- If IA or menu behavior must change after screen authoring, route through `impact` instead of silently rewriting.

## Index Generation

When SRS writes or refreshes `paths.usecases_index` or `paths.ascii_screen_index`, generate with `stale_status: unknown`, leave `validated_at` and `validated_by` blank. **[BẮT BUỘC]** Immediately run both:

```bash
ba-kit validate-index --index-key usecases_index --slug <slug> --date <date> --module <module> --writeback
ba-kit validate-index --index-key ascii_screen_index --slug <slug> --date <date> --module <module> --writeback
```

If either validation fails, stop execution. Do not proceed to SRS compile or downstream commands. The PostToolUse hook serves as fallback, but these inline calls are the primary enforcement.
