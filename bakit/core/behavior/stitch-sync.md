# Stitch Sync Behavior

## Scope

`stitch-sync` is a downstream visual-consumer lane. It reads approved SRS canon
and DESIGN.md, bootstraps a Stitch design system, and generates consistent UI
screens via Stitch MCP. It never owns BA requirements.

## Read Scope

- Must read `core/contract.yaml` and `core/contract-behavior.md`.
- Must read `paths.ascii_screen_index` before individual screen files.
- Must read `paths.design_doc` and `paths.shared_shell_contract`.
- Must read `paths.message_list` for MSG-* code resolution.
- May read `paths.ascii_screen_root` and `paths.srs_compile_receipt`.
- Must not read `paths.usecases_root`, `paths.userstories_root`, or `paths.frd`.

## Write Scope

- May write only under `paths.stitch_lane_root`.
- Must write: `paths.stitch_design_system_id`, `paths.stitch_screen_map`,
  `paths.stitch_sync_report`, `paths.stitch_mismatch_report`.
- Must not write `paths.srs`, `paths.ascii_screen_root`, `paths.usecases_root`,
  `paths.design_doc`, or `paths.shared_shell_contract`.

## MCP Connectivity Gate

- Before any BA artifact read, probe Stitch MCP via `list_projects`.
- If the tool is unavailable or returns AUTH_FAILED: block immediately.
  Print Stitch MCP setup instructions. Do not proceed.
- BA-kit does not install or configure MCP. The user must set it up separately.

## Guardrails

- If Stitch MCP is unreachable, block — do not read BA artifacts.
- If `paths.srs_compile_receipt` is missing or stale, block and recommend
  `ba-start srs --slug <slug> --module <module_slug>`.
- If `paths.design_doc` is missing, block and recommend `ba-start backbone`.
- If a Stitch design system already exists for this project, ask: reuse / refresh / abort.
  If disk file `paths.stitch_design_system_id` is missing when MCP says DS exists,
  block: "Stitch design system exists on server but local asset ID file not found at
  {path}. Run `git pull` to fetch stitch-design-system-id.json, then retry."
- If DESIGN.md content hash changed since last sync, force-refresh the design system.
- Refresh means full regeneration: destroy old DS, regenerate ALL screens.
- Screens with `stitch_sync_eligible: false` in ascii-screen frontmatter are skipped.
- `--device` flag (DESKTOP default | MOBILE | TABLET | AGNOSTIC) controls screen device type.
- `--skip-states` flag skips state variant generation (Phase 2a). Default screens are still generated.

## Design System Bootstrap

1. Read `paths.design_doc` — extract full content.
2. Base64-encode the DESIGN.md content.
3. Call `upload_design_md(designMdBase64, projectId)` — creates screen instance.
4. Call `create_design_system_from_design_md(projectId, selectedScreenInstance)` — builds design system asset.
5. Persist asset ID + DESIGN.md hash to `paths.stitch_design_system_id`.
6. All subsequent `generate_screen_from_text` calls use this asset ID via `designSystem` parameter.

## Screen Generation

For each eligible screen:
1. Read the ascii-screen canon file.
2. Extract: screen name, Portal ID, Nav Schema ID, active_menu, field table, state coverage, ASCII wireframe.
3. Extract documented states from `## States` table and `## ASCII Wireframe` subsections.
4. Extract MSG-* codes from field table (Validation Rules, Behaviour Rules) and resolve against `paths.message_list`.
5. Read portal/nav context from `paths.shared_shell_contract`.
6. Build prompt in plain natural language — NO IDs, NO keys, NO contract references. Stitch MCP is stateless and does not understand BA-kit IDs. Resolve every ID to its human-readable display text:
   - Portal: display name + description in prose (not portal_id).
   - Navigation: full list of menu items with exact visible labels (not nav_schema_id).
   - Active state: "The '{menu_label}' item is highlighted" (not a key reference).
   - Layout: describe layout direction and shell variant in words.
   - Wireframe: copy the ASCII wireframe into the prompt as visual reference. Describe every element position (what, where, label, purpose) top-to-bottom, left-to-right. **Exact placeholder data (CRITICAL):** all numbers, labels, and text visible in the ASCII wireframe are exact placeholder values — copy them verbatim and instruct Stitch to use them as-is, not invent different data. **Zone coverage (CRITICAL):** enumerate every shell zone (topbar, sidebar header, sidebar footer, content header, filter bar, main content, pagination area, footer). For each zone the wireframe does NOT occupy, emit an explicit negative-space directive: "Zone X is INTENTIONALLY EMPTY. Do NOT place anything here." This prevents Stitch from filling "gaps" with invented elements like search bars, notification bells, or user avatars.
   - **Field table priority:** the Field Table defines the widget STRUCTURE (table, cards, form fields, dropdown). The ASCII wireframe defines approximate LAYOUT POSITIONS. When they conflict on structure → field table wins. Example: if field table says "Project list | table" but wireframe shows card bullets, render a TABLE placed where the wireframe shows the list zone.
   - Branding/chrome: extract app_name, logo, user_area, footer from DESIGN.md. If absent → explicitly ban each: "NO logo", "NO user avatar". **Per-zone negative space:** after describing what IS in each zone, explicitly list what MUST NOT be there. Topbar: "NO search bar, NO notification bell, NO help icon, NO settings gear." Sidebar footer: "NO user avatar, NO user name, NO profile section." Content header: "NO breadcrumbs unless wireframe shows them."
   - Anti-hallucination: "Do NOT add any UI element not explicitly described. No invented logos, avatars, breadcrumbs, or extra menu items." **Reinforce with per-zone bans:** every zone description in the prompt must end with an explicit "Do NOT add X, Y, Z here" list covering the most common Stitch inventions for that zone type (search bars in topbar, notification icons, user profile sections, empty-state illustrations, extra filter controls).
   - Consistency directive: "Every screen in this portal must have the exact same branding and navigation. Branding: same app name, same logo treatment, same header, same footer across every screen. Navigation: same items, same order, same labels. Do not add, remove, rename, or reorder any menu item."
   - Cross-screen: reference already-generated screens by display name, not by ID. Include first-screen anchor: if this is the first screen generated for this portal, state "This is the first screen. All subsequent screens must match your branding and navigation exactly."
7. **States — DO NOT include in base prompt:** Do NOT append state descriptions or state ASCII wireframes to the `generate_screen_from_text` prompt. Describe ONLY the default state. Including state descriptions causes Stitch to generate all states at once in the same call, bypassing `generate_variants`. State generation is handled exclusively in the State Variant Generation section below.
8. **Prompt Sanitizer Gate (HARD):** Before calling `generate_screen_from_text`, scan the built prompt for leaked BA-kit ID patterns (`PORTAL-`, `NAV-`, `SCR-`, `UC-`, `FR-`, `MSG-`, `CR-`, etc.) and empty resolved values. If any leak detected or lookup incomplete → block that screen, do NOT call Stitch. If all screens fail the gate → block entire Phase 2.
9. Call `generate_screen_from_text(projectId, prompt, deviceType=<resolved_device>, designSystem=<assetId>)`.
10. Record `{ba_screen_id: {default: {stitch_screen_id, generated_at, status}, states: {}}}` in `paths.stitch_screen_map`.
11. **CRITICAL — BEFORE next screen:** if base generation succeeded and non-default states were extracted in step 3, **MUST execute State Variant Generation for this screen NOW.** Do not advance to next screen without attempting state generation.

### State Variant Generation

After base screen generated successfully, for each non-default state documented in the screen canon:
1. Build a state-specific delta prompt: describe ONLY what changes from the base screen (error messages, toast, banner, disabled controls). Do NOT repeat layout, nav, chrome, or zones — these are inherited from the base. Include anti-hallucination bans: do not change brand name, button text, link text, icons, border radius, input styling, or pre-filled values. Only the documented state changes may differ from the base.
2. Resolve ALL MSG-* codes to canonical text. The literal string `MSG-` must NOT appear in the prompt.
3. Specify exact feedback surface and styling: inline (below field, red text + red border), toast (position, color, auto-dismiss duration, text), banner (position, dismissible, color, text), dialog (overlay, close behavior).
4. Include state-specific ASCII wireframe from screen canon.
5. Run state prompt sanitizer gate: no IDs, no unresolved MSG-* codes, non-empty values, no structural changes.
6. Call `generate_variants(projectId, selectedScreenIds=[base_stitch_screen_id], prompt, variantOptions={creativeRange: REFINE, aspects: [TEXT_CONTENT], variantCount: 1})`.
   - `creativeRange: REFINE` → minimal changes, preserve base structure.
   - `aspects: [TEXT_CONTENT]` → only text-level changes applied. Layout, nav, chrome inherited from base.
   - `variantCount: 1` → exactly one variant per state.
   - NOTE: `deviceType` and `designSystem` are NOT accepted by `generate_variants`. Do not pass them.
7. **Validate response — `generate_variants` returns a chat-structured response, not a flat array:**
   - Response object has `outputComponents: [...]` and `sessionId`.
   - Extract variant screen ID from `outputComponents[0].design.screens[0].id`.
   - If `outputComponents[0]` has no `design` field → tool entered interactive/clarification mode. Mark state as `failed`, record "Stitch asked for clarification — prompt may not match base screen content".
   - If `outputComponents` is empty → mark state as `failed`, record "generate_variants returned no output components".
   - If timeout → mark as `failed`, record "timeout".
   - If error code `RATE_LIMITED` → BLOCK state generation.
   - If extracted variant screen ID equals base screen ID → mark as `uncertain` (Stitch may not have applied changes).
8. Record state variant: `{ba_screen_id: {default: {...}, states: {state_name: {stitch_screen_id, session_id, generated_at, status}}}}`.
9. Incremental write to `paths.stitch_screen_map` after EACH state variant.
10. Do not retry failed state variants — `generate_variants` is non-deterministic on retry.

## Output

- `stitch-design-system-id.json`: `{asset_id, design_md_hash, created_at, project_id}`
- `stitch-screen-map.json`: `{ba_screen_id: {default: {stitch_screen_id, generated_at, status}, states: {state_name: {stitch_screen_id, generated_at, status}}}}`
- `stitch-sync-report.md`: what was generated, skipped, verified (base screens + state variants)
- `stitch-mismatch-report.md`: cross-screen drift detected (logo, navbar, colors, state feedback text, state feedback surface)
