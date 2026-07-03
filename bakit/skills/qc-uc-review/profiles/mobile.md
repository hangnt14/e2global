# Mobile Platform Profile

> Loaded by `qc-uc-review` skill when `--platform mobile` is specified.
> This profile defines all mobile-specific framing, paths, edge cases, and KA adjustments.

---

## Subject Framing — CHỈ Mobile Client

Mọi phát biểu trong output PHẢI đặt **chủ ngữ là App/Client**, KHÔNG đặt chủ ngữ là API/Server.

| ❌ SAI (focus API) | ✅ ĐÚNG (focus Client) |
|---|---|
| API Tin tức trả về danh sách 5 tin | App nhận response Tin tức → render tối đa 5 tin |
| Timeout tối đa 10s cho API calls | App không nhận response trong 10s → hiển thị message + nút Thử lại |
| API có lọc theo role? | App có expected dataset khác nhau giữa các role? |
| Server xử lý timeout sau 10s | App phát hiện không có response sau 10s → hiển thị thông báo |
| API Biểu đồ trả về dữ liệu chart | App nhận dữ liệu → render biểu đồ theo format |

**Scope boundary:** Only raise questions about CLIENT-SIDE behavior. Do NOT question API/backend logic. Do NOT audit API logic, evaluate backend, or ask questions about server-side processing.

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

## Edge Case Checklist (Mobile-specific)

Apply during KA #6 — Object Attributes & Behavior Definition.
If UC does not mention an item → record gap + question.

| Group | Key checks |
|---|---|
| A — Extreme Data | Text overflow (truncate/wrap?), numeric 0/negative/max, empty list vs max items, null from API → placeholder? |
| B — Network | Slow API → loading/skeleton?, partial failure → independent or block all?, double-tap → debounce?, network loss mid-load? |
| C — Abnormal Interaction | Rapid taps → block multiple nav?, back button when modal open?, screen rotation? |
| D — Permissions & Session | Session expire → redirect/notify?, force-close → return screen?, different roles → different UI? |
| E — i18n | Language change → immediate update?, long text languages → layout break?, language persistence? |

> Edge cases only check CLIENT-SIDE behavior. Do NOT deduct points for gaps found here (bonus coverage).

**Rule 6.4 threshold:** ≥70% items covered across groups A-E → Clear (4pts). 40–<70% → Partial (2pts). <40% → Missing (0pts).

---

## KA Adjustments (Mobile)

### KA #3 — Actors & User Roles
- 3.3 Permission rules: focus on what each actor can **tap** / **see** on the mobile screen.
- 3.4 Fallback: role not in enum → how does the **App UI** handle it?

### KA #5 — UI Object Inventory & Mapping
- 5.2 Use case ↔ screen canon consistency: check label names, positions, component types match between module use cases, screen canon, and supporting mockup when present.
- 5.4 Shared-rule cross-check: reference `screen-field-contract.yaml`, shared shell rules, and explicit rule/message IDs. ≥85% applicable shared rules referenced → Clear.

### 5.5 Behaviour Rules Language Check

Behaviour Rules in screen field tables must describe user-visible behaviour in business language, not technical implementation details.

| Check | Criteria |
|---|---|
| No API paths | Behaviour Rules must NOT contain `/api/` or HTTP methods such as POST/GET/PUT/PATCH/DELETE. |
| No framework calls | Must NOT contain `navigate()`, `showModal()`, `setState()`, `dispatch()`, router calls, or mutation/query hook names. |
| Screen navigation | Must reference `SCR-*` IDs when describing navigation targets. |
| User-visible feedback | Must reference `MSG-*` codes when describing messages, toasts, banners, or inline errors. |
| Action verbs | Use business verbs: open/close/navigate/display/show/hide/enable/disable, not technical calls. |

Scoring: 0 violations -> Clear (4pts). 1-2 violations -> Partial (2pts). 3+ violations -> Missing (0pts). Evidence: read `ascii-screen/*.md` -> Fields table -> Behaviour Rules column for each field.

### KA #7 — Functional Logic & Workflow Decomposition
- 7.3 Exception & Error Flows: error handling for every **API call from the client** — what does the App display/do when the call fails or times out?

### KA #10 — Non-functional Requirements
- 10.3 Accessibility: touch target size, contrast ratio, screen reader support.
- 10.4 Compatibility: iOS/Android OS versions, screen sizes, orientations.

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

## Examples — Mobile Subject Framing in Gap Reports

**Gap: Missing network error handling**
- ❌ "API call fails → server returns 500"
- ✅ "App receives error response / no response → what does the screen display? Is there a retry button?"

**Gap: Missing role-based UI difference**
- ❌ "API filters data by role"
- ✅ "App renders different dataset / different action buttons depending on logged-in role?"

**Gap: Missing loading state**
- ❌ "API response takes time"
- ✅ "App has no loading indicator / skeleton screen defined while waiting for data"

**Gap: Missing debounce on navigation**
- ❌ "Backend receives duplicate requests"
- ✅ "App: rapid double-tap on nav button → does it navigate twice? Is there a tap guard?"

**Gap: Missing empty state**
- ❌ "API returns empty array"
- ✅ "App receives empty list → what does the screen render? Placeholder text? Illustration?"
