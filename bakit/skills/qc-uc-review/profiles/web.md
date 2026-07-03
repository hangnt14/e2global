# Web Platform Profile

> Loaded by `qc-uc-review` skill when `--platform web` is specified.
> This profile defines all web-specific framing, paths, edge cases, and KA adjustments.

---

## Subject Framing — CHỈ Browser / Web App

Mọi phát biểu trong output PHẢI đặt **chủ ngữ là Browser/Web App**, KHÔNG đặt chủ ngữ là API/Server.

| ❌ SAI (focus API) | ✅ ĐÚNG (focus Client) |
|---|---|
| API trả về danh sách 5 bản ghi | Browser nhận response → render tối đa 5 bản ghi lên bảng |
| Timeout tối đa 10s cho API calls | Web App không nhận response trong 10s → hiển thị message + nút Thử lại |
| API có lọc theo role? | Web App hiển thị dataset / action buttons khác nhau giữa các role? |
| Server xử lý timeout sau 10s | Browser phát hiện không có response sau 10s → hiển thị thông báo |
| API Biểu đồ trả về dữ liệu chart | Web App nhận dữ liệu → render biểu đồ theo format |

**Scope boundary:** Only raise questions about CLIENT-SIDE behavior in the browser. Do NOT question API/backend logic. Do NOT audit API logic, evaluate backend, or ask questions about server-side processing.

---

## Input Contract

- Module root: `plans/{slug}-{date}/03_modules/{module_slug}/`
- Primary evidence order: `backbone-index.md` -> `userstories/index.md` -> `usecases/index.md` + `usecases/uc-*.md` -> `ascii-screen/index.md` + `ascii-screen/*.md` -> `srs/spec.md` -> `screen-field-contract.yaml`
- Supporting evidence: current `srs.md`, `srs-compile-receipt.json`, `DESIGN.md`, shared shell contract, `shared/definitions.md`, `shared/traceability.md`
- Question Backlog: `plans/{slug}-{date}/03_modules/{module_slug}/qc-review/*-qc-review-question-backlog.md` (if exists)
- Important: Check the QC output directory for existing versions and read the highest report version.

## Output Contract

- Output folder: `plans/{slug}-{date}/03_modules/{module_slug}/qc-review/`
- Versioning: If `v[N]` exists -> `v[N+1]`. NEVER overwrite.

---

## Edge Case Checklist (Web-specific)

Apply during KA #6 — Object Attributes & Behavior Definition.
If UC does not mention an item → record gap + question.

| Group | Key checks |
|---|---|
| A — Responsive | Layout breakpoints defined?, table/grid collapse on small viewport?, modal/drawer overflow on mobile viewport?, font scaling? |
| B — Accessibility | Keyboard navigation order defined?, focus trap in modals?, ARIA labels on interactive elements?, color contrast WCAG 2.1 AA?, screen reader announcements for dynamic content? |
| C — Browser Compat | Minimum supported browsers listed?, CSS feature fallbacks?, JS polyfills for older browsers?, file download behavior across browsers? |
| D — Performance | Large list → virtual scroll / pagination?, image lazy loading?, debounce on search/filter input?, heavy page → skeleton/loading state? |
| E — State | Browser back/forward → correct page state?, tab refresh → session preserved or reset?, multiple tabs → state sync or conflict?, unsaved changes → leave-page warning? |

> Edge cases only check CLIENT-SIDE behavior. Do NOT deduct points for gaps found here (bonus coverage).

**Rule 6.4 threshold:** ≥70% items covered across groups A-E → Clear (4pts). 40–<70% → Partial (2pts). <40% → Missing (0pts).

---

## KA Adjustments (Web)

### KA #3 — Actors & User Roles
- 3.3 Permission rules: focus on what each actor can **click** / **see** on the web screen.
- 3.4 Fallback: role not in enum → how does the **Web App UI** handle it?

### KA #5 — UI Object Inventory & Mapping
- 5.2 Use case ↔ screen canon consistency: check label names, positions, component types match between module use cases, screen canon, and supporting mockup when present.
- 5.4 Shared-rule cross-check: reference `screen-field-contract.yaml`, shared shell rules, and explicit rule/message IDs. ≥85% applicable shared rules referenced → Clear.

### KA #7 — Functional Logic & Workflow Decomposition
- 7.3 Exception & Error Flows: error handling for every **API call from the browser** — what does the Web App display/do when the call fails or times out?

### KA #10 — Non-functional Requirements
- 10.3 Accessibility: keyboard navigation, WCAG 2.1 AA contrast, ARIA roles, focus management.
- 10.4 Compatibility: browser versions (Chrome, Firefox, Safari, Edge), viewport sizes, responsive breakpoints.

### KA Interaction Terminology (Web)
- Use **Click / Hover / Focus / Keyboard** — NOT Tap/Swipe (those are mobile terms).
- Form interactions: Tab order, Enter to submit, Escape to close modal.
- Responsive variants must be documented when layout changes across breakpoints.

---

## Shared Rule Sources

```text
plans/{slug}-{date}/03_modules/{module_slug}/screen-field-contract.yaml
plans/{slug}-{date}/02_backbone/shared-shell-contract.md
plans/{slug}-{date}/03_modules/{module_slug}/srs.md
```

Read shared rule sources before scoring KA #5 (5.4 Shared-rule cross-check) and before flagging any cross-artefact conflicts.

---

## Output Naming Convention

```text
plans/{slug}-{date}/03_modules/{module_slug}/qc-review/{module_slug}-qc-review-report-v[N].md
plans/{slug}-{date}/03_modules/{module_slug}/qc-review/{module_slug}-qc-review-question-backlog.md
```

---

## Routing Check — Output Folder States

| Output folder state | Action |
| :--- | :--- |
| No `*-qc-review-report-v[N].md` file | → **First audit** workflow |
| Has `*-qc-review-report-*` + backlog all Answered | → **Re-audit** workflow |
| Has `*-qc-review-report-*` + backlog has Open unanswered | → **WARN** + **ASK** user (see SKILL.md Step 0) |
| Has `*-qc-review-report-*` + no backlog | → **ASK** user: view current version or re-audit? |
| Module root or canon evidence missing | → **STOP** — ask user to verify module canon paths |
| Output folder does not exist (but module root exists) | → Create folder + continue first-audit |

---

## Examples — Web Subject Framing in Gap Reports

**Gap: Missing network error handling**
- ❌ "API call fails → server returns 500"
- ✅ "Web App receives error response / no response → what does the page display? Is there a retry button?"

**Gap: Missing role-based UI difference**
- ❌ "API filters data by role"
- ✅ "Web App renders different dataset / different action buttons depending on logged-in role?"

**Gap: Missing loading state**
- ❌ "API response takes time"
- ✅ "Web App has no loading indicator / skeleton screen defined while waiting for data"

**Gap: Missing debounce on search**
- ❌ "Backend receives duplicate requests"
- ✅ "Web App: rapid typing in search field → is there debounce? Does it fire a request on every keystroke?"

**Gap: Missing empty state**
- ❌ "API returns empty array"
- ✅ "Web App receives empty list → what does the page render? Placeholder text? Empty state illustration?"

**Gap: Missing responsive behavior**
- ❌ "Table has 10 columns"
- ✅ "Web App: table with 10 columns on mobile viewport → does it scroll horizontally, collapse, or reflow?"
