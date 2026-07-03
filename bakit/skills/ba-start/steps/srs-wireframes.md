# BA Start Step - SRS Wireframes

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md`
- `core/behavior/srs.md`

## Step 8.2 - Verify DESIGN.md Coverage For Module Portals

Skip this step when reverse mode is the active lane. Reverse-backed SRS work must use reverse evidence,
not `DESIGN.md`, as the blocking prerequisite.

**DESIGN.md is a system-level prerequisite created by Lead BA during backbone.**
Two-tier change authority applies:

| Level | Scope | Who | Gate |
|-------|-------|-----|------|
| L1 - Portal | New portal, new nav schema, new shell variant | Lead BA only | Hard — stop + escalate |
| L2 - Nav Item | Add menu item to existing portal/nav schema | Module BA with confirm | Soft — ask user → add → flag review |

Before authoring UI-backed screens, verify the module's portal(s) are covered:

### L1 Checks — Stop And Escalate To Lead BA

1. **DESIGN.md must exist.** If `paths.design_doc` is missing:
   ```
   DESIGN_GAP: design_doc missing for slug={slug}
   Action: Lead BA must run 'ba-start backbone --slug {slug}' first.
   ```
   Stop. Do NOT create DESIGN.md from this module step.

2. **Portal must be in DESIGN.md.** For every `Portal ID` used by this module, verify it exists in `paths.design_doc` §2. If missing:
   ```
   DESIGN_GAP: {portal_id} not found in designs/{slug}/DESIGN.md
   Action: Lead BA must run 'ba-start impact --slug {slug} "Add {portal_id} to DESIGN.md"'
   ```
   Stop.

3. **Nav Schema must exist.** If the module's `Nav Schema ID` is not declared in DESIGN.md:
   ```
   MENU_SCHEMA_GAP: {nav_schema_id} not found for {portal_id}
   Action: Lead BA must add Nav Schema to DESIGN.md and shared-shell-contract.md.
   ```
   Stop.

### L2 Checks — Module BA May Resolve With User Confirmation

4. **Missing menu item in existing nav schema.** If the portal and nav schema exist but a needed `Expected Active Menu Item` is absent:
   ```
   MENU_ITEM_GAP: screen {screen_id} needs menu item "{active_item}" in {portal_id}/{nav_schema_id}
   ```
   Ask user: "Thêm menu item '{active_item}' vào {portal_id}/{nav_schema_id} trong DESIGN.md và shared-shell-contract.md?"
   - **Yes**: add the item to both DESIGN.md Navigation Schema and shared-shell-contract.md. Flag in review packet for Lead BA visibility.
   - **No**: stop, escalate to Lead BA.

5. **Verify shared-shell-contract consistency.** Read `paths.shared_shell_contract` and confirm it declares all portals, nav schemas, and shell variants used by `paths.design_doc`. If inconsistent, flag and escalate.

All checks pass → proceed to screen authoring.

## Source: srs/flows.md

Output: `paths.srs_flows`

Produce only when module/system flows, cross-module interactions, or data flow diagrams are justified. UC-level diagrams belong in `usecases/diagrams.md`, not here.

## Source: srs/states.md

Output: `paths.srs_states`

Produce the module state registry when the module has meaningful state transitions across screens or use cases.

## Source: srs/erd.md

Output: `paths.srs_erd`

Produce only when data modelling, ERD, or API handoff needs justify it.

## Step 9 - Generate And Validate Mandatory ASCII Wireframes

Skip this step when reverse mode is the active lane. Reverse mode documents existing behavior from evidence and does not generate future-state wireframes.

For every UI-backed primary screen in `paths.ascii_screen_root`, create or refresh the `## ASCII Wireframe` section directly inside the matching `ascii-screen/*.md` file. ASCII wireframes are mandatory review evidence and must be derived from the screen canon itself.

Mode defaults inside the SRS pipeline:

- `lite`: generate ASCII for every UI-backed primary screen that exists in scope.
- `hybrid`: generate ASCII for every UI-backed primary screen and every L3 state.
- `formal`: generate ASCII for the full approved screen set, including supporting states.

Required screen canon result:
- canonical screen/use case artifacts authored first
- `ascii_status: current`
- `## ASCII Wireframe` present
- one ASCII subsection per required state listed in State Visual Coverage
- **[BẮT BUỘC]** Every inline message declared in `## Message Placement` MUST have a `▼ MSG-ERR-XX` marker at the exact field position in the wireframe
- **[BẮT BUỘC]** Toast messages MUST be drawn in a toast zone (corner box) in the wireframe
- **[BẮT BUỘC]** Banner messages MUST be drawn as a banner bar in the wireframe
- **[BẮT BUỘC]** Every wireframe MUST end with a `Message Zones:` legend listing all message positions
- Figma sync run as a separate consumer skill
- compiled `paths.srs` refreshed after canon changes

Example wireframe with markers:
```
+--------------------------------------------------+
| {Screen Title}                                   |
+--------------------------------------------------+
| {field label}: [________________]                |
| ▼ MSG-ERR-01: {error message}                    |
| [{Action Button}]                                |
|              ┌──────────────────┐                |
|              │ ✓ MSG-SUC-01     │                |
|              └──────────────────┘                |
+--------------------------------------------------+

Message Zones:
  Inline: dưới field {field_name} (MSG-ERR-01)
  Toast area: góc phải dưới (MSG-SUC-01: tự tắt sau 3s)
```

## Step 10 - Produce Final Screen Field Contract

After Step 9 resolves, expand final screen field contract from use case canon, screen canon, and backbone.

Manual mockup insertion into the final document is out of band and optional; it never replaces required ASCII in screen canon.
If reverse mode is active, expand screen descriptions from reverse evidence, promoted claims, and screen canon only.

Screen field contract rules:

- enrich the pre-wireframe screen spec; do not redefine portal ownership
- do not change `Nav Schema ID`, `Expected Active Menu Item`, or active/highlight behavior
- treat compiled `paths.srs` as a deliverable assembled from canon sources, not the primary edit surface
- if IA or menu behavior must change, route through `impact`
- run the navigation validator described in `core/behavior/srs.md` before finalizing when UI-backed screens exist

Screen field table format:

| Ten truong (Field Name) | Loai truong (Field Type) | Mo ta (Description) |
| --- | --- | --- |
| [Field] | [Type] | **Display Rules:** [visibility, defaults, read-only conditions, formatting] |
| | | **Behaviour Rules:** [on-change actions, auto-fill, cascading, navigation triggers] |
| | | **Validation Rules:** [required, format, range, cross-field, error message triggers] |
| | | **Rule Codes:** [CR-DIS-01, CR-VAL-01, v.v.] |
| | | **Message Codes:** [MSG-ERR-01, MSG-SUC-01, v.v.] |
