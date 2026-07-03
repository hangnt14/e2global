---
name: ba-stitch-sync
description: Sync approved BA canon to Stitch MCP for consistent UI screen generation. Requires Stitch MCP installed and configured.
argument-hint: "--module <module_slug> [--slug <slug>] [--date <date>] [--device DESKTOP|MOBILE|TABLET|AGNOSTIC]"
allowed-tools:
  - Read
  - Write
  - Bash
  - mcp__stitch__list_projects
  - mcp__stitch__create_project
  - mcp__stitch__list_design_systems
  - mcp__stitch__upload_design_md
  - mcp__stitch__create_design_system_from_design_md
  - mcp__stitch__generate_screen_from_text
  - mcp__stitch__get_screen
  - mcp__stitch__get_project
  - mcp__stitch__generate_variants
---

# BA Stitch Sync

Downstream visual-consumer command. Reads approved SRS canon + DESIGN.md, bootstraps a Stitch design system, and generates consistent UI screens via Stitch MCP.

## Invocation

```text
/ba-stitch-sync --module auth-flow
/ba-stitch-sync --slug warehouse-rfp --module payment --device MOBILE
/ba-do đồng bộ Stitch cho module auth-flow
/ba-do tạo UI từ SRS module payment
```

## Required Read Order

1. Read `core/contract.yaml`.
2. Read `core/contract-behavior.md`.
3. Read `core/behavior/stitch-sync.md`.
4. Resolve slug, date, module, and `--device` flag per `contract.yaml` resolution rules.

## General Error Handling Rules

**ID Validation Rule (applies to ALL MCP calls):**
After every MCP call that returns an ID (screen ID, asset ID, project ID):
1. Check the value is a non-empty string.
2. Check it is not an error object (no `error` or `code` field at top level).
3. Check it is not a hallucinated placeholder (not "id", "undefined", "null", "TODO", "xxx").
4. If ANY check fails → follow the per-step BLOCK/WARN/retry rule below.
5. Print the ID to user immediately so they can verify.
6. Write ID to disk immediately (not batch at end) to survive mid-phase crashes.

**Recovery Hierarchy:**

| Severity | Action | Example |
|----------|--------|---------|
| **BLOCK** | Stop entire command. Print error + fix instructions. | Asset ID missing, all screens failed, quota exceeded |
| **WARN + skip** | Log warning, skip this item, continue. | Single screen generation failed |
| **Retry** | Retry once after 10s. If still fails → escalate to WARN. | Timeout on upload_design_md |

---

## Phase 0 — Preflight

### Step 0.1: Parse arguments

- Extract `--slug`, `--date`, `--module` from ARGUMENTS.
- Extract `--device` flag: DESKTOP (default) | MOBILE | TABLET | AGNOSTIC.
- Resolve slug/date/module per contract.yaml resolution rules.

### Step 0.2: Read contract

- Read `core/contract.yaml`.
- Read `core/contract-behavior.md`.
- Read `core/behavior/stitch-sync.md`.

### Step 0.3: MCP Connectivity Gate

- Call `mcp__stitch__list_projects()`.
- If tool unavailable or error:
  - Print Stitch MCP setup instructions (API key, .mcp.json config, restart Claude Code).
  - **BLOCK** — do not proceed.
- If success: continue.

### Step 0.3a: Resolve Stitch project

- From `list_projects()` output, find project matching slug or prompt user to select.
- If no matching project exists, create one via `mcp__stitch__create_project(name=<slug>)`.
- Extract `projectId` for all subsequent MCP calls.

### Step 0.4: BA Prerequisite Gate

- Check `paths.design_doc` exists.
- Check `paths.srs_compile_receipt` exists and fresh.
- Check `paths.ascii_screen_index` exists.
- Check `paths.shared_shell_contract` exists.
- Any fail → **BLOCK** + recommend correct `ba-start` command.

---

## Phase 1 — Design System Bootstrap

### Step 1.1: Check existing design system

- Call `mcp__stitch__list_design_systems(projectId)`.
- **VALIDATE:** Check response is an array (not null, not error object).
  If response is not iterable → WARN "Unexpected response from list_design_systems" + treat as no existing DS.
- If existing DS found:
  - **Disk cross-check:** Check if `paths.stitch_design_system_id` exists on disk.
    - If file exists → read it, validate `asset_id` field is non-empty.
    - If file MISSING → **BLOCK** "Design system exists on Stitch server but local asset ID file not found at {path}. Another BA created this design system — run `git pull` to fetch stitch-design-system-id.json, then retry."
  - Show: "Design system already exists (created {date}). Reuse / Refresh / Abort?"
  - **Refresh: Full regeneration.** Destroy old design system, regenerate ALL screens.
    Existing stitch-screen-map.json is invalidated. User warned about re-generation cost.
  - Abort: exit.
- If no existing DS: continue.

### Step 1.2: Read DESIGN.md

- Read full `paths.design_doc`.
- **VALIDATE:** Content is non-empty string. If empty → **BLOCK** "DESIGN.md is empty. Cannot create design system."
- Compute content hash (SHA-256 or similar) for change detection.

### Step 1.3: Upload DESIGN.md

- Base64-encode DESIGN.md content.
- Call `mcp__stitch__upload_design_md(projectId, designMdBase64)`.
- **VALIDATE response:**
  - Response must be an object (not null, not error string).
  - Extract `selectedScreenInstance`: must have `id` (non-empty string) and `sourceScreen` (non-empty string).
  - If `id` is missing/empty → **BLOCK** "upload_design_md returned no screen instance ID. Cannot proceed."
  - If `sourceScreen` is missing/empty → **BLOCK** "upload_design_md returned no source screen reference. Cannot proceed."
- Log: `upload_design_md OK — screen instance: {id}`.

### Step 1.4: Create design system

- Call `mcp__stitch__create_design_system_from_design_md(projectId, selectedScreenInstance)`.
- **VALIDATE response:**
  - Wait for completion — this call can take minutes. DO NOT retry on timeout.
  - If timeout → poll `get_project(projectId)` every 30s for up to 10 attempts to check if DS was created.
  - Extract asset ID from response. Must be non-empty string matching `assets/` or numeric pattern.
  - If asset ID is null/empty/undefined after polling → **BLOCK** "Failed to create design system. DESIGN.md was uploaded but design system creation did not complete. Check Stitch project manually."
- **ID VALIDATION GATE — HARD BLOCK:**
  - The asset ID extracted here is CRITICAL. Every subsequent screen depends on it.
  - Write it to `paths.stitch_design_system_id` IMMEDIATELY (before Phase 2).
  - Re-read the file to confirm the write succeeded and the ID is not truncated.
  - If the file write fails or the ID is malformed → **BLOCK** "Cannot persist design system ID."

### Step 1.5: Verify design system exists (sanity check)

- Call `mcp__stitch__list_design_systems(projectId)` again.
- **VALIDATE:** The asset ID from Step 1.4 MUST appear in the list.
  - If NOT found → **BLOCK** "Design system was created (asset ID: {id}) but not found in list_design_systems. Possible Stitch sync delay or ID mismatch. Retry Phase 1 or check Stitch manually."

---

## Phase 2 — Screen Generation

### Step 2.1: Load design system ID

- Read `paths.stitch_design_system_id`.
- **VALIDATE:** `asset_id` field exists, is non-empty string.
  - If missing or empty → **BLOCK** "Design system ID not found. Run Phase 1 bootstrap first."
  - If file doesn't exist → **BLOCK** "stitch-design-system-id.json not found. Run Phase 1 first."
- **CRITICAL:** This ID is used in EVERY screen generation call. Wrong ID = all screens broken.
  Print the ID to user so they can verify: "Using design system: {asset_id}"

### Step 2.1a: Migrate stitch-screen-map.json schema (if exists)

The schema changed from v1 (flat) to v2 (nested with `default` + `states`). Existing maps from prior sync runs may use v1.

- Check if `paths.stitch_screen_map` exists.
- If file doesn't exist → skip migration (fresh run).
- If file exists:
  - Read and parse JSON.
  - Check format:
    - **v2 (current):** entries have `default` key → no migration needed. Print: "Screen map already v2 format."
    - **v1 (legacy):** entries have `stitch_screen_id` at top level → auto-migrate.
  - **Migration (v1 → v2):**
    For each entry `{ba_screen_id: {stitch_screen_id, generated_at, status, error?}}`:
    ```
    {ba_screen_id: {
      default: {stitch_screen_id, generated_at, status, error?},
      states: {}
    }}
    ```
  - Write migrated map back to `paths.stitch_screen_map`.
  - Print: "Migrated {N} screen entries from v1 to v2 format. State variants will be added on this run."
  - **VALIDATE:** Re-read file, confirm entries have `default` key → if not, **BLOCK** "Schema migration failed. Map still in v1 format. Check JSON structure manually."
- **If map has mixed format** (some v1, some v2) → **BLOCK** "stitch-screen-map.json has mixed v1/v2 entries. Cannot auto-migrate. Fix manually or delete map for fresh regeneration."

### Step 2.2: Build BA-kit ID Reference Index

Before reading any screen file, build a lookup index from shared_shell_contract:
- Read `paths.shared_shell_contract`.
- Extract ALL valid IDs into a structured index:
  ```
  portals: { "PORTAL-APP": { display_name, layout_direction, shell_variant, description }, ... }
  nav_schemas: {
    "NAV-APP-01": {
      portal_id,
      menu_items: [{ label, target, icon_hint?, order }],
      active_rule,
      layout_hint
    },
    ...
  }
  actors: { "ACT-01": {...}, "ACT-02": {...} }  (if defined)
  ```
- **CRITICAL:** The `menu_items` list in each nav_schema is the single source of truth for what navigation items appear. Extract every field — label, target, icon_hint, order. This list will be injected verbatim into every screen generation prompt to ensure navigation consistency.
- **VALIDATE:** Each nav_schema must reference a portal_id that EXISTS in `portals`.
  - If nav_schema references unknown portal → **BLOCK** "shared_shell_contract: NAV-xx references unknown portal PORTAL-xx. Fix shared_shell_contract first."
- Also read `paths.design_doc` — extract Portal Summary and Navigation Schema tables.
  - From Portal Summary: extract portal_id, display_name, layout direction (sidebar|topbar|mixed), shell variant.
  - From Navigation Schema: extract nav_schema_id, menu item list, active/highlight rule.
  - **Chrome & branding (CRITICAL for anti-hallucination):** extract project-level branding elements if present:
    - `app_name`: the application display name (e.g., "WMS Pro")
    - `logo`: logo description or "NO LOGO" / "TEXT ONLY" directive
    - `user_area`: user avatar/name display area description (e.g., "top-right avatar + user name dropdown"), or "NONE"
    - `footer`: footer content or "NONE"
    - `global_header`: any global header content outside the nav, or "NONE"
  - If DESIGN.md does NOT define these → mark each as "UNSPECIFIED" (will trigger anti-hallucination rule in prompt).
- **CROSS-CHECK:** Portal IDs and Nav Schema IDs in DESIGN.md MUST match shared_shell_contract exactly.
  - If DESIGN.md has PORTAL-X but shared_shell_contract has PORTAL-Y → **BLOCK** "DESIGN.md and shared_shell_contract disagree on portals. Align them first."
  - If DESIGN.md has NAV-xx but shared_shell_contract doesn't → **BLOCK** "DESIGN.md defines NAV-xx but shared_shell_contract has no matching schema."
- Print the resolved index: "Resolved {N} portals, {M} nav schemas ({menu_count} total menu items)."

### Step 2.2a: Load Message List for State Generation

Screen states reference `MSG-*` codes (e.g., `MSG-ERR-01`, `MSG-SUC-01`). These MUST be resolved to their canonical text before building prompts — Stitch does not understand BA-kit codes.

- Read `paths.message_list` if it exists.
- Build a message code lookup:
  ```
  messages: { "MSG-ERR-01": { type: "ERR", canonical_text: "Email hoặc mật khẩu không đúng.", surface: "inline" }, ... }
  ```
  - `canonical_text`: the exact message text that must appear in the generated UI
  - `surface`: where the message appears — `inline` (below field), `toast` (floating notification), `banner` (top-of-page bar), `dialog` (modal)
  - `type`: `ERR` (error), `WRN` (warning), `SUC` (success), `INF` (info)
- If `paths.message_list` is missing or empty → WARN "No message list found at {path}. Error messages in generated screens may show placeholder text. Recommend running ba-start backbone to generate message-list.md first."
- If message list exists but a referenced MSG-* code is NOT found → WARN "MSG-{code} referenced in screen canon but not found in message-list.md. Will use code as fallback text."
- Print: "Loaded {N} shared messages for state generation."

### Step 2.2b: Load Component Stylings for State Feedback

Screen states use feedback components (toast, inline error, banner, dialog). DESIGN.md §5 "Component Stylings" defines the visual treatment of these components.

- Re-read `paths.design_doc` §5 (Component Stylings) and extract **feedback style** section:
  - Toast: position (top-right, top-center, bottom-center), auto-dismiss duration, color treatment
  - Inline error: text color, icon presence, border treatment
  - Banner: position (top of content, below header), dismissible or persistent
  - Dialog/Modal: overlay darkness, close behavior
  - Disabled/Read-only: opacity or gray treatment
- Store as `feedback_styles` dict for injection into state prompts.
- If DESIGN.md §5 has no feedback section → mark as "UNSPECIFIED" (will fall back to standard patterns with explicit bans).
- If DESIGN.md §5 is missing entirely → WARN "DESIGN.md §5 Component Stylings missing. Feedback component styling will fall back to generic defaults. Stitch may invent styles."

### Step 2.3: Read screen index

- Read `paths.ascii_screen_index`.
- **VALIDATE:** Index is parsable, contains at least 1 screen entry.
  - If empty → WARN "No screens found in ascii_screen_index. Nothing to generate." + skip Phase 2.
- Filter: skip screens with `stitch_sync_eligible: false`.

### Step 2.4: Cross-Reference Validation Gate (MANDATORY — before ANY screen generation)

For each eligible screen, read the canon file and extract IDs. Validate ALL of them against the reference index BEFORE calling any MCP tool:

1. **Screen ID (`id` or `screen_id`):**
   - Must be non-empty.
   - Must follow expected pattern (e.g., `SCR-NN`).
   - If missing → **BLOCK** "Screen file {path}: missing screen ID. Add it before generating."
   - If malformed (e.g., `SCR-`, `SCREEN01`, no prefix) → WARN "Unusual screen ID format: {id}" + continue.

2. **Portal ID (`portal_id`):**
   - Must be non-empty.
   - Must exist in the reference index `portals` built in Step 2.2.
   - If NOT found → **BLOCK** "Screen {id}: portal_id '{portal_id}' not found in shared_shell_contract. Valid portals: {list}. Fix screen file."
   - If screen file doesn't declare portal_id → **BLOCK** "Screen {id}: missing portal_id. Every screen must declare which portal it belongs to."

3. **Nav Schema ID (`nav_schema_id`):**
   - Must be non-empty.
   - Must exist in the reference index `nav_schemas`.
   - Must belong to the same portal declared in `portal_id` (cross-check: nav_schema.portal_id == screen.portal_id).
   - If NOT found → **BLOCK** "Screen {id}: nav_schema_id '{nav_schema_id}' not found. Valid schemas: {list}."
   - If schema belongs to different portal → **BLOCK** "Screen {id}: nav_schema_id '{nav_schema_id}' belongs to portal '{actual_portal}', but screen declares portal '{screen_portal}'. Mismatch."

4. **Expected Active Menu Item:**
   - If declared, must match an item in the nav schema's `menu_item_list`.
   - If NOT found → WARN "Screen {id}: active_menu '{item}' not in nav schema '{nav_schema_id}' menu list: {valid_items}. Active highlight may be wrong."

5. **Overlay Context (`overlay_context.parent_screen`):**
   - If screen is modal/dialog/drawer/overlay, `parent_screen` must reference an existing screen ID in the index.
   - If parent NOT found → **BLOCK** "Screen {id}: overlay parent '{parent}' not found in screen index. Parent screen must exist."

6. **Cross-screen Portal consistency:**
   - All screens in the same portal MUST use the same nav_schema_id (unless an explicit exception is documented).
   - Group screens by portal_id. Check nav_schema_id is uniform per portal group.
   - If mismatch → WARN "Portal {portal_id}: screens use different nav schemas: {list}. This may cause navigation inconsistency. Explicit exception documented?"

7. **Duplicate Screen IDs:**
   - Check no two screen canon files declare the same screen ID.
   - If found → **BLOCK** "Duplicate screen ID '{id}' in files: {file1}, {file2}. Screen IDs must be unique."

8. **State message code resolution (HARD — before generation):**
   For each screen, extract ALL `MSG-*` codes from the field table (Validation Rules column) and from state descriptions.
   - Resolve each code against the message lookup from Step 2.2a.
   - If a code is NOT found in the message list → WARN "Screen {id}: MSG-{code} referenced but not found in message-list.md. Generated UI may show code instead of text."
   - If the message list is entirely missing → WARN "Screen {id}: no message list available. MSG-* codes in this screen's validation rules will not be resolved to text. Stitch may show raw codes."

9. **State ASCII wireframe coverage:**
   For each screen with documented states:
   - Verify each state listed in `## States` has a corresponding `### {State Name}` subsection under `## ASCII Wireframe`.
   - If a state has no ASCII wireframe → WARN "Screen {id}: state '{state_name}' has no ASCII wireframe. State generation will rely on text description only."
   - If a screen has states but no `## States` table → WARN "Screen {id}: has multiple ASCII wireframe subsections but no States table. State list inferred from wireframe headings."

**Gate outcome:**
- Print validation summary: "{N} screens checked, {S} states found, {W} warnings, {E} errors."
- If E > 0 → **BLOCK** entire Phase 2. "Fix {E} cross-reference errors above before generating screens."
- If W > 0 → show warnings, ask user "Continue with {W} warnings? (Y/n)". Default Y.
- If 0 errors + 0 warnings → proceed to generation.

### Step 2.5: Prompt Building Rules — Plain Text Only (NO IDs, NO keys)

Stitch MCP's `generate_screen_from_text` is stateless. Each call is an isolated AI generation. It has NO knowledge of BA-kit IDs, contract keys, or the project's shared shell. **Every piece of information the model needs must be in the prompt as full natural language text.**

**HARD RULES:**

1. **NO IDs in prompt.** Do NOT pass `portal_id`, `nav_schema_id`, `screen_id`, or any BA-kit internal key to Stitch. These strings are opaque garbage to the generation model.
   - WRONG: "Portal: PORTAL-APP, Nav Schema: NAV-APP-01"
   - RIGHT: "This screen belongs to the Admin Portal — a left-sidebar layout with 5 navigation items."

2. **Resolve all IDs to their display text.** For every ID in the reference index, substitute the human-readable text:
   - `portal_id` → portal `display_name` + `description` in natural language
   - `nav_schema_id` → describe the navigation structure in prose, then list every menu item with its visible label
   - `active_menu` → "The '{menu_label}' menu item must be visually highlighted/active on this screen"
   - `layout_direction` → "The navigation appears as a vertical sidebar on the left" or "The navigation is a horizontal top bar"
   - `shell_variant` → describe the chrome layout in words

3. **Menu items as full sentences, not keys.** List each navigation item with its exact display label, position, and what it navigates to:
   ```
   The navigation menu contains these items, in this order:
   1. "Tổng quan" — links to the dashboard overview page
   2. "Quản lý kho" — links to warehouse management
   3. "Báo cáo" — links to reports
   4. "Cài đặt" — links to settings
   ```

4. **Consistency directive must be in plain text.** Do not reference nav_schema_id. Instead: "Every screen in this portal must show the exact same navigation menu with the exact same items in the same order. Do not add, remove, rename, or reorder any menu item."

5. **Cross-screen anchoring uses display names, not IDs.** "Previous screens already generated with this navigation: 'Trang tổng quan', 'Danh sách kho hàng'. Your navigation must match theirs exactly."

6. **Use the screen's human-readable name**, not its SCR-xx ID, when describing what this screen is.

### Step 2.6: Generate each screen (sequential)

For each eligible screen:
1. Read ascii-screen canon file.
2. Extract: name, portal_id, nav_schema_id, field table, state coverage, ASCII wireframe.
3. **Extract states for variant generation:**
   - Parse `## States` table: extract state_id, state_name, state_description for each row.
   - Parse `## ASCII Wireframe` subsections: each `### {State Name}` is a state-specific wireframe block.
   - Map each state to its wireframe: `{ "state_name": "Error", "description": "Invalid credentials shown", "ascii_wireframe": "..." }`.
   - Identify the DEFAULT state (first wireframe subsection, or explicitly named "Default").
   - Collect all non-default states for variant generation.
   - If `## States` table is missing but multiple wireframe subsections exist → infer state names from subsection headings.
   - If only one wireframe subsection (default only) → no state variants to generate.
4. **Extract message codes from field table:**
   - Scan `Validation Rules` column of each field for `MSG-*` patterns.
   - Also scan `Behaviour Rules` column for message references (e.g., "show MSG-ERR-01").
   - Resolve each MSG-* code against the message lookup from Step 2.2a.
   - Build a resolved message list for this screen:
     ```
     resolved_messages: [
       { code: "MSG-ERR-01", type: "ERR", text: "Email hoặc mật khẩu không đúng.", surface: "inline", field: "Password" },
       { code: "MSG-SUC-01", type: "SUC", text: "Đăng nhập thành công.", surface: "toast", field: null }
     ]
     ```
   - If a message has `surface: inline`, note which field it appears below.
   - If a message has `surface: toast`, note position from component stylings (Step 2.2b).
   - If a message has `surface: banner`, note whether it's dismissible.
5. **Extract error surface types from field table:**
   - From `Validation Rules` column: identify the surface type for each validation message — `inline` (below the field), `toast` (floating notification), `banner` (top-of-page bar), `dialog` (modal).
   - If surface is not explicitly stated → infer from MSG-* code's `surface` in message list.
   - If still unknown → default to `inline` for field validations, `toast` for success messages.
6. **VALIDATE extracted data:**
   - `name` must be non-empty.
   - `portal_id` must match a known portal from shared_shell_contract.
   - `nav_schema_id` must match a known schema.
   - Each `MSG-*` code must resolve to a known message (WARN if not — use code as fallback text).
   - If any critical field missing → WARN "Screen {file}: missing {field}. Generation may be inconsistent." + continue.
7. **CRITICAL — Do NOT pass extracted IDs directly to the prompt.** The IDs from Step 2 (`portal_id`, `nav_schema_id`) are internal BA-kit keys. Stitch does not know what "PORTAL-APP" or "NAV-APP-01" means. You MUST look each one up in the Step 2.2 reference index and substitute the full text:

   **Mechanical lookup process (do this for EVERY screen):**

   ```
   Step A: Read screen file → extract: name="Danh sách kho hàng", portal_id="PORTAL-APP", nav_schema_id="NAV-APP-01"

   Step B: Look up portal_id in reference index:
           portals["PORTAL-APP"] → {
             display_name: "Ứng dụng quản lý kho",
             description: "Portal chính cho nhân viên quản lý hàng hóa, nhập/xuất kho, kiểm kê.",
             layout_direction: "vertical sidebar on the left",
             shell_variant: "fixed sidebar + scrollable content area"
           }

   Step C: Look up nav_schema_id in reference index:
           nav_schemas["NAV-APP-01"] → {
             menu_items: [
               { label: "Tổng quan", target: "dashboard", icon_hint: "home icon", order: 1 },
               { label: "Quản lý kho", target: "warehouse", icon_hint: "package icon", order: 2 },
               { label: "Nhập hàng", target: "import", icon_hint: "arrow-down icon", order: 3 },
               { label: "Xuất hàng", target: "export", icon_hint: "arrow-up icon", order: 4 },
               { label: "Báo cáo", target: "reports", icon_hint: "chart icon", order: 5 }
             ],
             layout_hint: "vertical sidebar, items stacked top-to-bottom"
           }

   Step D: Look up active_menu for this screen (validated in Step 2.4.4):
           → "Quản lý kho"

   Step E: NOW build the prompt using ONLY the resolved text from Steps B, C, D.
           ZERO IDs from Step A appear in the final prompt.
   ```

5. Build prompt in plain natural language, using ONLY the resolved text from Step 4 lookup. Follow Step 2.5 rules strictly — NO IDs, NO keys:

   **Prompt structure (all sections required):**

   a. **Portal description:**
      "You are generating a screen for the 'Ứng dụng quản lý kho' portal. Portal chính cho nhân viên quản lý hàng hóa, nhập/xuất kho, kiểm kê."

   b. **Layout description:**
      "The layout uses a vertical sidebar on the left — fixed sidebar + scrollable content area."

   c. **Navigation menu (verbatim list — MOST CRITICAL):**
      "The navigation menu has 5 items, displayed as a vertical sidebar stacked top-to-bottom. They must appear on every screen in this portal exactly as follows:
      1. 'Tổng quan' — home icon
      2. 'Quản lý kho' — package icon
      3. 'Nhập hàng' — arrow-down icon
      4. 'Xuất hàng' — arrow-up icon
      5. 'Báo cáo' — chart icon"

   d. **Active menu state:**
      "On THIS screen, the menu item 'Quản lý kho' must be visually highlighted as the active/selected item."

   e. **Screen identity:**
      "This screen is 'Danh sách kho hàng'. Hiển thị danh sách tất cả kho hàng trong hệ thống dưới dạng bảng có phân trang."
      Then summarize key fields, behaviours, and states from the canon file.

   f. **Wireframe layout (DETAILED — mirror ASCII positions exactly):**
      The ASCII wireframe defines exact element positions. Translate it into a structured text description Stitch can follow. Do NOT summarize or skip elements.

      Translation rules:
      - **Read order:** top-to-bottom, left-to-right. Describe elements in the order they appear.
      - **Copy the ASCII wireframe itself into the prompt** as a visual reference block. Stitch can interpret ASCII art.
      - **For each visible element**, state: what it is (button/input/dropdown/table/label/link), its label text, its approximate position (top-left, center, right side, below X, etc.), and its purpose.
      - **Group related elements:** fields in a form → "A form with 4 input fields arranged vertically: ..."
      - **Describe layout zones:** "The screen is divided into: (1) a top search bar, (2) a data table filling the main area, (3) a bottom pagination bar, (4) a 'Tạo mới' button above the table on the right."
      - **State-specific wireframes (NEW):** If the screen has multiple states, the prompt body describes the DEFAULT state as the primary screen to generate. After the default state description, append a `## States` block listing all other states and their visual differences (see Step 2.6.4f3 below).
      - **Exact labels:** use the EXACT field labels from the ASCII wireframe. Same wording, same capitalization.
      - **Exact placeholder data (CRITICAL — prevents Stitch from inventing numbers):** all numbers, counts, percentages, and text values visible in the ASCII wireframe are exact placeholder values. Copy them verbatim and add the directive: "Use these exact values as shown. Do NOT invent different numbers, different counts, or different text." If the wireframe says "3 Presale, 5 Won", the generated screen must show exactly "3" and "5" — not "12" and "28".
      - **Zone coverage — empty zones MUST be declared (CRITICAL — prevents Stitch from filling gaps):** after describing every element in the wireframe, enumerate ALL shell zones and declare each one's status:
        1. **Topbar zone** (above content, below nav): list what appears here. If nothing appears → "The topbar is INTENTIONALLY EMPTY except for the page title. Do NOT add a search bar, notification bell, help icon, settings gear, or any other controls to the topbar."
        2. **Sidebar header** (top of sidebar): list what appears. If only nav menu → "The sidebar header is INTENTIONALLY EMPTY. Do NOT add a logo, brand name, or product title."
        3. **Sidebar footer** (bottom of sidebar): list what appears. If nothing → "The sidebar footer is INTENTIONALLY EMPTY. Do NOT add a user avatar, user name, profile link, or logout button."
        4. **Filter bar** (below page header, above main content): list every filter. If no filters in wireframe → "There is NO filter bar. Do NOT add any filter dropdowns or search inputs."
        5. **Main content area**: describe what fills it. Any sub-zone not occupied → "This area is INTENTIONALLY EMPTY."
        6. **Footer**: if wireframe shows no footer → "There is NO footer. Do NOT add a footer line, copyright text, or version number."
        Any zone not explicitly declared → treat as a coverage gap and add an explicit ban before generation.

      Example for a list screen:
      ```
      ASCII wireframe reference:
      ┌─────────────────────────────────────────────┐
      │  [Tạo kho mới]              [Tìm kiếm...]   │
      ├─────────────────────────────────────────────┤
      │  Mã kho  │ Tên kho   │ Địa chỉ    │ Hành động│
      ├──────────┼───────────┼────────────┼─────────│
      │  K-001   │ Kho A     │ 123 ABC    │ [Sửa]   │
      │  K-002   │ Kho B     │ 456 DEF    │ [Sửa]   │
      ├─────────────────────────────────────────────┤
      │  ← Trước   Trang 1/5   Sau →               │
      └─────────────────────────────────────────────┘

      Layout zones, top to bottom:
      1. Top toolbar: "[Tạo kho mới]" button on the left, "[Tìm kiếm...]" search input on the right
      2. Data table: 4 columns — "Mã kho", "Tên kho", "Địa chỉ", "Hành động". Each row has a "[Sửa]" action button in the last column.
      3. Bottom pagination: "← Trước" link, "Trang 1/5" text, "Sau →" link. Centered.

      Zone coverage:
      - Topbar: ONLY page title. NO search bar, NO notification bell, NO help icon.
      - Sidebar header: INTENTIONALLY EMPTY. NO logo, NO product name.
      - Sidebar footer: INTENTIONALLY EMPTY. NO user avatar, NO profile section.
      - Filter bar: the search input in the top toolbar serves as the only filter. NO separate filter bar with extra dropdowns.
      - Footer: NO footer.
      ```

   f2. **Field Table priority over wireframe for widget structure (CRITICAL):**
      The Field Table in the screen canon defines the widget TYPE (table, cards, form, dropdown, etc.). The ASCII wireframe defines approximate LAYOUT POSITIONS. When they conflict on structure → **Field Table wins.**

      Resolution rule:
      - If Field Table says "Project list | table" with columns listed → render a TABLE with those exact columns, placed where the wireframe shows the list zone.
      - If Field Table says "Kanban board | cards" → render CARDS, regardless of wireframe simplification.
      - If Field Table says a widget is a "dropdown" → render a dropdown, not a radio group or toggle.
      - The wireframe's visual arrangement (bullet points, boxes, dashes) is a layout hint — not the final widget type.
      - When Field Table and wireframe agree on widget type → use both for exact positioning.
      - When Field Table specifies structure but wireframe omits it → add the widget at the wireframe's corresponding zone position.

      In the prompt, state the widget type explicitly using Field Table terms: "The project list is a TABLE with columns: Mã dự án, Tên dự án, Khách hàng, % hoàn thành." Do NOT say "a list of projects" if the Field Table says "table".

   f3. **State descriptions — DO NOT include in base prompt:**
      Do NOT include state descriptions or state ASCII wireframes in the `generate_screen_from_text` prompt. The base prompt must describe ONLY the default state. Stitch's model interprets all prompt content as instructions — including state descriptions triggers Stitch to generate all states as separate screens in the same call (using `figaro_agent`), bypassing the `generate_variants` path.

      State generation is handled exclusively in Step 2.6a via `generate_variants`, which starts from the base screen and preserves structural identity. The base prompt should just note: "This screen has {N} additional visual states that will be generated separately."

   g. **Branding & chrome elements (from DESIGN.md — resolve "UNSPECIFIED" to explicit bans):**
      These are shell-level elements that stay the same across all screens. They are NOT part of individual screen wireframes — they come from the shared_shell_contract and DESIGN.md.

      Resolve each chrome field from the Step 2.2 index. If the field is "UNSPECIFIED" → explicitly ban it:
      - `app_name`: if set → "The application name '{app_name}' must appear in the {position}." If UNSPECIFIED → "NO application name or brand title in the header. Leave it blank."
      - `logo`: if set → "Include logo: {logo_description}." If UNSPECIFIED → "NO logo. Do not invent a logo or icon."
      - `user_area`: if set → "Show user area: {user_area_description}." If UNSPECIFIED → "NO user avatar, user name, or profile area. Do not invent user identity elements."
      - `footer`: if set → "Show footer: {footer_content}." If UNSPECIFIED → "NO footer. Do not add a footer line."
      - `global_header`: if set → include it. If UNSPECIFIED → "NO extra header content beyond the navigation sidebar/topbar."

   h. **Anti-hallucination directive with per-zone negative space (CRITICAL — prevents Stitch from inventing):**
      Generic "do not add" directives are insufficient — Stitch's model fills perceived gaps. Every zone must carry an explicit ban list.

      **Global bans (apply to entire screen):**
      "Do NOT add any UI element that is not explicitly described in the wireframe or field table above. Every button, field, label, and link on this screen must correspond to something listed. If it's not listed, it doesn't exist."

      **Per-zone ban lists (inserted directly into each zone description — NOT separate):**
      After describing what IS in each zone, append the zone-specific ban. These MUST appear inline in the zone description, not as a separate bullet list at the end:

      | Zone | Ban directive (append to zone description) |
      |------|---------------------------------------------|
      | Topbar | "NO search bar, NO notification bell, NO help icon, NO settings gear, NO user menu. Only the elements listed above appear in the topbar." |
      | Sidebar header | "NO logo, NO product name, NO brand icon. Only the navigation menu items listed above appear in the sidebar." |
      | Sidebar footer | "NO user avatar, NO user name, NO profile link, NO logout button, NO role label. This area is empty." |
      | Content header | "NO breadcrumbs unless the wireframe explicitly shows them. NO tabs unless the wireframe shows them." |
      | Filter bar | "ONLY the filter controls listed above. NO additional filter dropdowns, NO 'advanced filter' button, NO search input unless specified." |
      | Main content | "ONLY the widgets listed in the Field Table. NO empty-state illustrations, NO onboarding tooltips, NO 'no data' graphics unless the screen is in Empty state." |
      | Footer | "NO footer line, NO copyright text, NO version number, NO links. The page ends at the bottom of the main content area." |

      **Common Stitch invention patterns to explicitly ban (include in every prompt):**
      - Do NOT invent a brand/product name (like "ProjectFlow", "AppName", etc.) — use the portal display name or leave blank.
      - Do NOT invent user identity elements (avatar photo, user name, role title, "Business Analyst" label).
      - Do NOT invent notification UI (bell icon, badge count, notification dropdown).
      - Do NOT invent help/support UI (help icon, "?" button, chat widget).
      - Do NOT add extra menu items beyond the {N} listed above.
      - Do NOT translate labels from one language to another — use exact wording from the wireframe.
      - Do NOT change numeric values — use exact numbers from the wireframe.

   i. **Consistency directive (navigation + branding):**
      "CRITICAL: Every screen in the 'Ứng dụng quản lý kho' portal must have the exact same navigation menu — same items, same order, same labels. Do NOT add, remove, rename, or reorder any menu item.
      Branding must also be identical across all screens: same app name text, same logo treatment (or none), same header layout, same footer. Do NOT change the brand display between screens — if one screen has text-only '{app_name}' branding, every screen must use text-only '{app_name}' in the same position and style."

   j. **Cross-screen anchor (if applicable):**
      If other screens in this portal were already generated: "The following screens were already generated with this exact branding and navigation and must be matched:
      - Branding: '{app_name}' as {text-only | logo description} at {position}
      - Screens: 'Trang tổng quan', 'Danh sách kho hàng'."
      If this is the FIRST screen in the portal: "This is the first screen generated for the 'Ứng dụng quản lý kho' portal. All subsequent screens must match your branding and navigation exactly."

5a. **PROMPT SANITIZER GATE (HARD — before EVERY MCP call):**

   Before calling `generate_screen_from_text`, scan the assembled prompt for leaked BA-kit IDs. This gate catches AI instruction-skipping, partial lookups, and copy-paste errors.

   **Check 1 — Banned ID patterns:**
   Scan the prompt for any string matching these BA-kit ID prefixes. If found → **BLOCK this screen**, record the matched string, skip to next screen:
   - `PORTAL-`, `NAV-`, `SCR-`, `UC-`, `FR-`, `NFR-`, `BR-`, `MSG-`, `CR-`, `BO-`, `CAP-`, `E-`, `AC-`
   - Also: `portal_id`, `nav_schema_id`, `screen_id` (raw field names)
   - Also: any string matching `{...}` placeholder not yet substituted

   **Check 2 — Empty resolved values:**
   Verify every resolved field from Step 4 lookup is non-empty:
   - `portal_display_name` is not empty/null
   - `portal_description` is not empty/null
   - `menu_items` list is not empty
   - Every `label` in menu_items is a non-empty string
   - `active_menu_label` is not empty/null
   - `layout_direction_description` is not empty/null

   **Check 3 — Menu item count matches:**
   The number of menu items in the prompt must equal the number in `nav_schemas[{nav_schema_id}].menu_items` from the reference index. If count differs → **BLOCK** "Menu item count mismatch: index has {N}, prompt has {M}. Prompt may have truncated or invented items."

   **Check 4 — Chrome fields NOT left as "UNSPECIFIED":**
   Scan the prompt for the literal string "UNSPECIFIED". If found → the AI failed to resolve a chrome/branding field from Step 2.2 into an explicit description or ban. **BLOCK this screen** "PROMPT CHROME LEAK: 'UNSPECIFIED' found in prompt. Chrome field not resolved. Check Step 2.2 chrome extraction."

   **Check 5 — Zone coverage completeness:**
   Verify every shell zone is declared in the prompt (see Step 2.6.4f zone list). Scan for these zone markers:
   - "topbar" or "top bar" or "header" — must appear at least once
   - "sidebar header" — must appear at least once
   - "sidebar footer" — must appear at least once
   - "filter" — must appear at least once (either describing filters or explicitly banning them)
   - "footer" — must appear at least once (either describing footer or explicitly "NO footer")
   - For each zone, check it is followed by either a description of content OR an explicit "INTENTIONALLY EMPTY" / "NO ..." ban within 2 sentences.
   If any zone is missing entirely from the prompt → WARN "ZONE COVERAGE GAP: '{zone_name}' not declared in prompt. Stitch may invent content for this zone. Skipping screen {name}." → mark screen as `failed`, continue to next screen.

   **Gate outcome:**
   - **PASS** → print "Prompt gate OK: {N} IDs resolved, 0 leaked, {Z} zones covered." → proceed to Step 6.
   - **FAIL Check 1** → WARN "PROMPT LEAK: found banned pattern '{matched}' in prompt. Skipping screen {name}. Fix Step 4 lookup." → mark screen as `failed`, continue to next screen.
   - **FAIL Check 2** → WARN "PROMPT INCOMPLETE: empty value for '{field}'. Index lookup may have returned nothing. Skipping screen {name}." → mark screen as `failed`, continue.
   - **FAIL Check 3** → WARN "PROMPT MENU COUNT WRONG: index={N} prompt={M}. Skipping screen {name}." → mark screen as `failed`, continue.
   - **FAIL Check 4** → WARN "PROMPT CHROME LEAK: 'UNSPECIFIED' found in prompt. Skipping screen {name}." → mark screen as `failed`, continue.
   - **FAIL Check 5** → WARN "ZONE COVERAGE GAP: '{zone_name}' not declared in prompt. Skipping screen {name}." → mark screen as `failed`, continue.

   **If ALL screens fail the gate** → **BLOCK** entire Phase 2. "All screens failed prompt sanitizer gate. The reference index or lookup process is broken. Fix Step 2.2 and Step 2.6 Step 4 before retrying."

6. Call `mcp__stitch__generate_screen_from_text(projectId, prompt, deviceType=<resolved_device>, designSystem=<assetId>)`.
7. **VALIDATE response:**
   - Response must contain a screen ID (non-empty string).
   - If screen ID is null/empty/undefined → mark screen as `failed`, record error "generate_screen_from_text returned no screen ID", continue to next screen.
   - If timeout (no response after 5 minutes) → mark as `failed`, record "timeout", continue.
   - If error code `RATE_LIMITED` → **BLOCK** entire Phase 2. "Stitch daily quota exceeded. {N} screens remaining. Retry after midnight UTC."
8. **ID VALIDATION — POST-WRITE:**
   - Record in in-memory map FIRST: `{ba_screen_id: {default: {stitch_screen_id, generated_at, status: "ok"|"failed", error: "..."}, states: {}}}`.
   - Write `paths.stitch_screen_map` AFTER EACH screen (not batch at end) — prevents data loss on mid-phase failure.
   - Re-read the file to confirm write succeeded.
9. Print progress: "[{N}/{total}] {screen_name} → {stitch_screen_id} ✓" or "✗ {error}"
10. **CRITICAL — BEFORE moving to next screen:** if this screen's base generation succeeded and it has non-default states (collected in sub-step 3), **MUST execute Step 2.6a for THIS screen now.** Do NOT skip to next screen without attempting state variant generation.

### Step 2.6a: Generate State Variants

After base (default) screen is generated successfully, generate a state variant for each non-default state documented in the screen canon. Use `generate_variants` — it starts from the base screen and applies only the described changes, guaranteeing structural identity (nav, layout, chrome, zones) with the base.

**Why `generate_variants`, not `generate_screen_from_text`:**
- `generate_variants` starts from the base screen → layout, nav, chrome identical by construction. A second `generate_screen_from_text` call may reposition elements, reflow layout, or shift colors — losing state-to-default fidelity.
- With `creativeRange: REFINE` and `aspects: [TEXT_CONTENT]`, only text-level changes are applied. The layout structure is preserved.
- State prompt is simpler — no need to repeat portal/nav/zone descriptions. Only describe the delta.

**When to skip state generation:**
- Screen has only one state (default only) → skip Step 2.6a for this screen.
- Screen base generation failed → skip state generation for this screen.
- `--skip-states` flag passed → skip Step 2.6a entirely.

**State generation loop (for each non-default state):**

1. **Build state-specific delta prompt:**
   Describe ONLY what changes from the base screen. The prompt is a delta — `generate_variants` inherits everything else from the base.

   **State delta prompt structure:**

   ```
   This is the "{state_name}" state of the "{screen_name}" screen.

   Trigger: {state description — when this state appears}.

   Only the following elements differ from the base screen:

   1. {specific change}: e.g., "A red inline error message appears below the Email field:
      'Email không hợp lệ.' The Email field border turns red."
   2. {specific change}: e.g., "A red error banner spans the top of the content area below the
      page header: 'Vui lòng sửa các lỗi bên dưới.' The banner has an X dismiss button."
   3. {specific change}: e.g., "A toast notification appears at the top-right corner:
      'Đã lưu thành công.' Green background, white text. Auto-dismisses after 3 seconds."

   State ASCII wireframe reference:
   ```
   {state-specific ASCII wireframe from screen canon — copy verbatim}
   ```

   Feedback component specifications:
   - Message surface: {inline | toast | banner | dialog}
   - Toast position: {top-right | top-center | bottom-center} (from DESIGN.md §5, or default: top-right)
   - Toast auto-dismiss: {duration} seconds (from DESIGN.md §5, or default: 5s error, 3s success)
   - Banner: {dismissible: yes + X button | persistent} (from DESIGN.md §5, or default: dismissible)
   - Inline error: red text, red field border, error icon if specified in DESIGN.md §5

   Do NOT describe layout, navigation, chrome, or zones — these are inherited from the base screen.
   Do NOT add any UI element not explicitly listed above.

   **Anti-hallucination bans (state-specific):**
   The base screen defines the entire visual identity. Only the changes listed above may be applied. Everything else MUST remain identical to the base screen:
   - Do NOT change the brand name or page title. Use the exact same text as the base screen.
   - Do NOT add or change any logo, brand icon, or decorative icon. Input fields must keep the exact same icon set as the base — no new mail/lock/user icons unless the base already has them.
   - Do NOT change any button text, label text, or link text. Buttons/links must use the exact same wording as the base screen.
   - Do NOT add new links, buttons, or navigation items beyond those on the base screen. If the base has no "Đăng ký ngay" or "Điều khoản" link, do not invent them.
   - Do NOT change border radius (rounded), card styling, input border width, padding, or any visual styling. The only allowed styling changes are those explicitly described above (e.g., red border on a specific error field).
   - Do NOT pre-fill any input field with invented values. Fields must remain empty (or show their placeholder text) unless the state wireframe explicitly shows a value.
   - Do NOT add, remove, or reorder any form field. The field set must be identical to the base screen.
   - Do NOT translate labels or text from one language to another. Use exact wording from the base screen.
   ```
   ```
   These bans prevent Stitch from re-interpreting the screen identity during variant generation. Every state must look like the base screen plus ONLY the documented state changes.

2. **Resolve ALL MSG-* codes to text before building state prompt:**
   - Scan the state description from screen canon for `MSG-*` references.
   - Look up each code in the message lookup from Step 2.2a.
   - Substitute the `canonical_text` verbatim.
   - If a code is unresolved → WARN "State {state_name}: MSG-{code} not found in message list. Using code as fallback." → use the code string as fallback text.

3. **State prompt sanitizer gate:**
   Minimal checks — the base screen already passed full sanitization:
   - **Check 1 — Banned ID patterns:** Scan for `MSG-`, `SCR-`, `CR-`, and all banned patterns from Step 2.6.5a Check 1. State prompts MUST contain only resolved text.
   - **Check 2 — MSG-* resolution:** The literal string `MSG-` must NOT appear in the prompt. If found → **BLOCK** this state. "MSG-* code not resolved in state prompt for {screen_name}/{state_name}."
   - **Check 3 — Empty values:** Verify state name, trigger description, and each change description is non-empty.
   - **Check 4 — No structural changes:** The prompt must NOT describe layout shifts, nav changes, new zones, or chrome modifications. If detected → **BLOCK** "State variant prompt for {screen_name}/{state_name} describes structural changes. State prompts must only describe visual overlays/feedback."
   - **Gate outcome:**
     - PASS → print "State prompt gate OK for {screen_name}/{state_name}." → proceed.
     - FAIL → WARN "State prompt gate FAIL for {screen_name}/{state_name}: {reason}." → mark state as `failed`, continue to next state.

4. **Call `generate_variants` for state:**
   ```
   mcp__stitch__generate_variants(
     projectId,
     selectedScreenIds: [base_stitch_screen_id],
     prompt: <state_delta_prompt>,
     variantOptions: {
       creativeRange: REFINE,
       aspects: [TEXT_CONTENT],
       variantCount: 1
     }
   )
   ```
   - `selectedScreenIds` is the Stitch screen ID from the base (default) generation.
   - `creativeRange: REFINE` → minimal changes, preserve base structure.
   - `aspects: [TEXT_CONTENT]` → only text-level changes (error messages, labels, notifications).
   - `variantCount: 1` → generate exactly one variant per state.
   - **IMPORTANT:** Do NOT pass `deviceType` or `designSystem` — `generate_variants` does not accept these parameters. The device type and design system are inherited from the base screen.

5. **VALIDATE response (chat-structured, NOT a flat array):**
   `generate_variants` returns a chat-structured response, not a simple array of screen IDs. The structure is:
   ```json
   {
     "outputComponents": [
       {"design": {"screens": [{"id": "...", ...}]}, "title": "..."},
       {"text": "..."},
       {"suggestion": "..."}
     ],
     "sessionId": "..."
   }
   ```
   - **Extract variant screen ID:** `outputComponents[0].design.screens[0].id`.
   - **Interactive/clarification mode:** If `outputComponents[0]` has NO `design` field (only `text` + `suggestion`) → Stitch asked for clarification instead of generating. Prompt may not match base screen content. Mark state as `failed`, record "Stitch entered clarification mode — prompt content may not align with base screen".
   - If `outputComponents` is empty or null → mark state as `failed`, record "generate_variants returned no output components", continue.
   - If timeout (no response after 5 minutes) → mark as `failed`, record "timeout", continue.
   - If error code `RATE_LIMITED` → **BLOCK** state generation. "Stitch daily quota exceeded during state generation. Default screens already saved."
   - If extracted variant screen ID equals base screen ID → WARN "State variant returned same ID as base. Stitch may not have applied state changes." → mark state as `uncertain`.
   - Record `sessionId` alongside the variant screen ID for debugging.

6. **Record state in stitch-screen-map.json:**
   Append to the screen's entry:
   ```json
   {ba_screen_id: {
     default: {stitch_screen_id, generated_at, status: "ok"},
     states: {
       "error": {stitch_screen_id, session_id, generated_at, status: "ok"},
       "empty": {stitch_screen_id, session_id, generated_at, status: "ok"}
     }
   }}
   ```
   - `session_id`: the `sessionId` field from `generate_variants` response — recorded for debugging interactive/clarification failures.
   - Write `paths.stitch_screen_map` after EACH state variant (same incremental-write pattern as base screens).

7. **Print progress:**
   "[{N}/{total_screens}] {screen_name} → {state_name} state → {stitch_screen_id} ✓" or "✗ {error}"

8. **State variant failure handling:**
   - If a state variant fails → mark as `failed` in the map, record reason, continue to next state.
   - If ALL state variants for a screen fail → WARN "All {K} state variants failed for {screen_name}. Only default state generated."
   - Do NOT block the entire Phase 2 for individual state failures — the default screen is already generated.
   - Do NOT retry failed state variants (unlike base screens). `generate_variants` retries produce different variants each time.

**State generation summary:**
After all screens processed, print:
"State generation complete: {S_total} states attempted across {N_screens} screens. {S_ok} generated, {S_failed} failed, {S_skipped} skipped (no states)."

### Step 2.7: Post-generation sanity check

- Count screens in `paths.stitch_screen_map`.
- **VALIDATE:** Count of base screens matches number of eligible screens.
  - If fewer → WARN "{N} base screens failed to generate. See stitch-sync-report.md for details."
- **VALIDATE:** At least 1 base screen succeeded.
  - If 0 base screens succeeded → **BLOCK** "All screen generations failed. Check Stitch quota and project state. No reports written."
- Count state variants across all screens:
  - Total states attempted, succeeded, failed.
  - If >30% of states failed → WARN "High state failure rate: {K}/{S_total} states failed. Generated screens may lack error/empty/loading states. Check failed entries in stitch-sync-report.md."
- Check for duplicate stitch_screen_ids (same ID for different BA screens):
  - If found → WARN "Duplicate stitch_screen_id detected: {id}. Possible AI hallucination or Stitch bug. Mark affected screens for re-generation."
- Check for duplicate stitch_screen_ids across states:
  - If a state variant has the same stitch ID as its parent default screen → WARN "State variant {state_name} for {screen_name} returned same stitch ID as default. Stitch may have ignored state prompt."

---

## Phase 3 — Validation

### Step 3.1: Load generated screens

- Read `paths.stitch_screen_map`.
- **VALIDATE:** File exists and contains valid JSON.
  - If file missing → **BLOCK** "No screen map found. Phase 2 may not have run or failed completely."
- Filter to screens with `status: "ok"`.
  - If 0 OK screens → WARN "No successfully generated screens to validate." + skip validation.

### Step 3.2: Cross-screen consistency check

- For each generated screen, get screenshot via `mcp__stitch__get_screen(name, projectId)`.
- **VALIDATE each get_screen call:**
  - If call fails or returns no image data → mark screen as `validation: "skipped"`, record reason.
  - If timeout → skip screen, continue.
- Compare across screens: navbar region, logo placement, primary CTA color, font usage.
- Flag any drift with severity: `high` (different color), `medium` (spacing shift), `low` (minor).

### Step 3.3: State consistency check (NEW)

For each screen with state variants:

1. **Get screenshot for each state variant** via `mcp__stitch__get_screen(name, projectId)`.
2. **Compare state variant vs default:**
   - Layout zones must be identical (navbar, sidebar, footer positions unchanged).
   - Only the documented visual difference should appear (error message, toast, disabled controls).
   - If layout shifted between states (e.g., content area resized, navigation reflowed) → flag as `medium` drift.
3. **Compare state feedback vs message list:**
   - Verify the error/success text visible in the screenshot matches the `canonical_text` from the message list.
   - If text differs → flag as `high` drift: "State variant {state_name} for {screen_name}: expected message '{expected}', generated '{actual}'."
4. **Compare state feedback surface vs specification:**
   - If surface is `inline` but screenshot shows `toast` → flag as `medium` drift.
   - If surface is `toast` but screenshot shows `banner` → flag as `medium` drift.
   - If toast position differs from DESIGN.md §5 → flag as `low` drift.
5. **Flag state consistency drifts in mismatch report** with severity and recommendation.

### Step 3.4: Write reports

- Write `paths.stitch_sync_report`:
  - Generated: N base screens + S state variants (list with stitch IDs)
  - Skipped: M screens (with reasons)
  - Failed: K screens / S_failed state variants (with errors)
  - Validated: V screens + T state variants (with consistency score)
  - Design system asset ID
  - Message list used: {path} ({N_messages} messages loaded)
- Write `paths.stitch_mismatch_report` (if drift detected):
  - Which screens drifted
  - What drifted (color, layout, typography, state feedback text, state feedback surface)
  - Severity
  - Recommendation (re-run specific screen / adjust DESIGN.md / fix message-list.md / accept)

---

## Write Scope

Allowed repo writes:

- `plans/{slug}-{date}/05_tool-lanes/stitch/stitch-design-system-id.json`
- `plans/{slug}-{date}/05_tool-lanes/stitch/stitch-screen-map.json`
- `plans/{slug}-{date}/05_tool-lanes/stitch/stitch-sync-report.md`
- `plans/{slug}-{date}/05_tool-lanes/stitch/stitch-mismatch-report.md`

Forbidden repo writes:

- `srs.md`, `srs/spec.md`, `srs/flows.md`, `srs/states.md`, `srs/erd.md`
- `ascii-screen/*.md`
- `usecases/*.md`
- `userstories/*.md`
- `frd.md`
- `DESIGN.md`
- `shared-shell-contract.md`
- `backbone.md`
- Any canon BA artifact

## Stop Conditions

- Stitch MCP unavailable → **BLOCK** with setup instructions
- Missing or stale `srs-compile-receipt.json`
- Missing `ascii-screen/index.md`
- Missing `DESIGN.md`
- Missing `shared-shell-contract.md`
- Missing `message-list.md` → WARN (soft: proceed but MSG-* codes will not resolve to text)
- Design system creation fails
- All screen generations fail
- RATE_LIMITED error from Stitch MCP
- Cross-reference validation errors (>0)

## Output

After the run, report:
- resolved project/module
- design system asset ID (or reused)
- screens attempted, succeeded, failed, skipped
- device type used
- consistency check results
- report paths written
