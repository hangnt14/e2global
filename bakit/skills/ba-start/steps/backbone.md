# BA Start Step - Backbone

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md`

## Memory Read Scope

- **Must read:** `core/contract.yaml`, `core/contract-behavior.md`, `paths.intake`
- **Must read when it exists:** `paths.plan`
- **Must read when optioning is completed:** the selected option file only
- **May read:** `paths.project_memory`, `paths.memory_index` (navigation only), `paths.memory_hot_vocabulary`, `paths.memory_hot_decisions`
- **Must NOT read:** `log.md`, `cold/`, `warm/` shards

## Governance Gate

Before mutating this artifact:
1. Always verify write authority for the target artifact and its owning memory shard.
2. For first-pass creation (when `paths.backbone` does not yet exist), skip only the impact-receipt requirement.
3. For reruns (artifact already exists): locate the active impact receipt at `paths.impact_receipt` (or the canonical receipt path for this slug/date). If no active receipt exists and `change_class` is not `wording-only`, emit `GOVERNANCE_BLOCK: impact_receipt missing or invalidated` and stop.
4. If either check fails: emit `GOVERNANCE_BLOCK: {reason}` and stop.
5. After mutation completes: offer to file the change into canonical memory using `templates/project-memory-fileback-record-template.md`.

Receipt reference: `templates/impact-receipt-template.md`

## Scope

Run Step 5 only.

## Prerequisites

- Resolve slug and date using `ba-kit resolve --slug <slug>`.
  The CLI uses `find -type d` internally for correct directory discovery.
  Do not use `Glob` — it only matches files, not directories.
- **[CWD GATE]** After resolve, cd to the project root (`Project root:` line from `ba-kit resolve` output). All artifact paths in `contract.yaml` are relative to the project root. Backbone creates system-level artifacts (`design_doc`, `shared_shell_contract`) under the project root — a stale CWD will place them in the wrong location.
- Require `paths.intake`.
- If intake is missing, print the exact missing path and stop.
- Read `paths.plan` when it exists.
- Run a narrow backbone preflight:
  - read only `paths.intake` and `paths.plan` when it exists
  - do not scan other folders once slug and date are resolved
  - when `paths.plan` records `options status: recommended` or `options status: in-progress`, stop because optioning is unresolved
  - when `paths.plan` records `options status: completed` or `options status: skipped`, treat that as the backbone decision gate
  - require `paths.plan` to state either `options status: skipped`, `options status: completed`, or `options status: not-needed` before proceeding
  - if completed, require a `selected option` AND an active options receipt at `paths.options_receipt`; if the receipt is missing, emit `GOVERNANCE_BLOCK: options_receipt missing` and stop
  - if completed, read only the selected option file as the decision overlay
  - never require `paths.options_root` to exist before honoring the decision-ledger gate
  - options receipt reference: `templates/options-receipt-template.md`

## Output

- `paths.project_home`
- `paths.backbone`
- `paths.backbone_index`
- `paths.common_rules` — always; system-level shared rule registry
- `paths.message_list` — always; system-level shared message registry
- `paths.shared_rule_message_index` — always; compiled CR/MSG cross-reference index
- `paths.project_memory`
- `paths.design_doc` — when UI-backed scope exists
- `paths.shared_shell_contract` + `paths.shared_shell_index` — when UI-backed scope exists
- `paths.control_type_library` — when UI-backed scope exists AND Step 5.1a library gate passed

## Step 5 - Build the requirements backbone

Create the persisted source-of-truth artifact using `~/.claude/templates/requirements-backbone-template.md` (fallback: [../../../templates/requirements-backbone-template.md](../../../templates/requirements-backbone-template.md)).

The backbone must contain:

- scope lock summary
- selected engagement mode (`lite`, `hybrid`, or `formal`)
- business goals and success metrics
- actors and feature map
- system-level portal matrix for UI-backed scope
- FR/NFR draft inventory
- preliminary story map
- UI/screen coverage assessment
- artifact emission gates
- assumptions, risks, and open questions

After writing the backbone, initialize or refresh `paths.project_memory` using `~/.claude/templates/project-memory-template.md` (fallback: [../../../templates/project-memory-template.md](../../../templates/project-memory-template.md)).
Also create or refresh `paths.backbone_index` using `~/.claude/templates/backbone-index-template.md` (fallback: [../../../templates/backbone-index-template.md](../../../templates/backbone-index-template.md)).
Generate the index with `stale_status: unknown`, leave `validated_at` and `validated_by` blank.

**Create shared registries.** These are system-level artifacts that module artifacts reference by code:

1. **`paths.common_rules`** using `~/.claude/templates/common-rules-template.md` (fallback: [../../../templates/common-rules-template.md](../../../templates/common-rules-template.md)).
   - Populate initial CR-* codes derived from backbone scope: CR-VAL-* for common validations (email, password, required), CR-DIS-* for display rules (pagination threshold), CR-BEH-* for behaviour rules (button disabled conditions).
   - Each rule must include `applies_to` pattern and `edge_cases` column.

2. **`paths.message_list`** using `~/.claude/templates/message-list-template.md` (fallback: [../../../templates/message-list-template.md](../../../templates/message-list-template.md)).
   - Populate initial MSG-* codes: MSG-ERR-* for common errors, MSG-SUC-* for success toasts, MSG-WRN-* for warnings, MSG-INF-* for info messages.
   - Each message must include `surface` (inline/toast/banner/modal) and `canonical_text`.

3. **`paths.shared_rule_message_index`** — after writing both registries, generate the compiled index by running:
   ```bash
   ba-kit validate-shared-rule-message-registry --write-index --slug <slug> --date <date>
   ```

**[BẮT BUỘC — KHÔNG ĐƯỢC BỎ QUA]** Ngay sau khi write `backbone-index.md`, PHẢI chạy:

```bash
ba-kit validate-index --index-key backbone_index --slug <slug> --date <date> --writeback
```

- Nếu validation PASS hoặc WARN: `stale_status` được promote lên `current`. Có thể tiếp tục downstream.
- Nếu validation FAIL: DỪNG. Không được chạy `stories`, `frd`, `srs`, `package` hay bất kỳ downstream command nào. Sửa index rồi chạy lại validator.
- PostToolUse hook (`guardrail-index-validation-hook.sh`) sẽ tự chạy lại validator như fallback, nhưng agent PHẢI gọi inline trước.

Không được bỏ qua bước này với lý do "để sau", "index nhỏ", hay "sẽ validate sau".

### Step 5.1 — Persist DESIGN.md and Shared Shell Contract [BẮT BUỘC khi có UI]

**Owner: Lead BA only. Module BA MUST NOT create or modify these files.**

When the backbone Portal Matrix defines at least one portal (UI-backed scope exists), immediately create:

1. **`paths.design_doc`** using `~/.claude/templates/design-md-template.md` (fallback: [../../../templates/design-md-template.md](../../../templates/design-md-template.md)).
   - Section 2 (Information Architecture) MUST include EVERY portal from the backbone Portal Matrix.
   - Section 2.2 (Navigation Schema) MUST declare every nav schema used by any portal.
   - Do NOT restrict DESIGN.md to just one module — it is a system-level visual direction artifact.
   - Ask user to approve design direction (visual tone, colors, typography, component feel). Stop if unresolved.

2. **`paths.shared_shell_contract`** using `~/.claude/templates/shared-shell-contract-template.md` (fallback: [../../../templates/shared-shell-contract-template.md](../../../templates/shared-shell-contract-template.md)).
   - MUST declare ALL portals, nav schemas, shell variants, layout variants, and shared components.
   - This is the machine-readable counterpart to DESIGN.md §2.

3. **`paths.shared_shell_index`** using `~/.claude/templates/shared-shell-index-template.md` (fallback: [../../../templates/shared-shell-index-template.md](../../../templates/shared-shell-index-template.md)).

**Rule:** These files are system-level, owned by Lead BA. Module BAs MAY add menu items to existing nav schemas with user confirmation (flag in review packet). New portals, nav schemas, shell variants, or shared components require Lead BA via `impact`.

### Step 5.1a — UI Library Selection Gate [BẮT BUỘC trước Step 5.2]

**`control_type_library` MUST NOT be created until this gate is satisfied.**

Sau khi DESIGN.md đã được tạo và user đã duyệt design direction ở Step 5.1, backbone PHẢI hỏi user chọn thư viện UI trước khi tiếp tục. Gate này hỗ trợ hai đường:

- **Đường nhanh (single-run):** user chọn library ngay trong prompt → backbone ghi vào DESIGN.md và tiếp tục tạo control-type-library luôn.
- **Đường nghiên cứu (two-run):** user cần thời gian research → backbone dừng, user tự điền DESIGN.md, chạy lại backbone sau.

Gate logic:

1. Đọc `paths.design_doc`, kiểm tra section "UI Library" hoặc "Thư viện UI".
2. Nếu DESIGN.md ĐÃ CÓ library selection (tên library + version cụ thể, không phải `TBD`) → gate passed. Tiếp tục Step 5.2.
3. Nếu library = `none` → gate passed. Tiếp tục Step 5.2 với baseline = `none`.
4. Nếu library = `TBD`, trống, hoặc chỉ có proposal chưa chốt → **HỎI user bằng `AskUserQuestion`**:

   ```
   Hỏi: "DESIGN.md đã có design direction nhưng chưa chốt thư viện UI. Bạn muốn chọn thư viện nào?"

   Các lựa chọn:
   - "Shadcn UI" — component library phổ biến, Tailwind-based
   - "Ant Design 5.x" — design system đầy đủ, phù hợp enterprise
   - "MUI (Material UI)" — Material Design, hệ sinh thái React lớn
   - "Chakra UI" — accessible, composable
   - "Tailwind UI" — utility-first, không opinionated
   - "Flowbite" — Tailwind component library
   - "none" — không dùng thư viện UI nào
   - "Tôi cần thời gian research" — dừng backbone, điền DESIGN.md sau rồi chạy lại
   ```

5. **Nếu user chọn một library cụ thể:**
   - Ghi tên library + version (hỏi thêm version nếu user chưa cung cấp) + docs link vào DESIGN.md Section 10.
   - Đánh dấu "Đã chốt" trong DESIGN.md.
   - Gate passed → tiếp tục Step 5.2 ngay trong cùng run.

6. **Nếu user chọn "none":**
   - Ghi `none` vào DESIGN.md Section 10.
   - Đánh dấu "Đã chốt".
   - Gate passed → tiếp tục Step 5.2 với baseline = `none`.

7. **Nếu user chọn "Tôi cần thời gian research":**
   - In message:

     ```
     ⏸️  Đã dừng ở gate 5.1a. DESIGN.md đã được tạo với library = TBD.

     Khi đã chốt thư viện UI:
     - Cách 1: Mở DESIGN.md → điền Section 10 "Thư viện UI" → chạy lại backbone.
     - Cách 2: Chạy lại backbone, em sẽ hỏi lại câu này.

     Gợi ý: Shadcn UI, MUI, Ant Design, Chakra UI, Tailwind UI, Flowbite...
     Hoặc chọn "none" nếu không dùng thư viện nào.
     ```

   - DỪNG. Không tạo control-type-library.

Sau khi user chốt library và chạy lại backbone:
- Backbone đọc lại DESIGN.md, phát hiện library đã được điền → skip Step 5.1 (files đã tồn tại), hỏi lại gate 5.1a nếu vẫn TBD, hoặc qua gate 5.1a vào Step 5.2 nếu đã chốt.

### Step 5.2 — Persist Control Type Library [BẮT BUỘC khi có UI, sau Gate 5.1a]

**Owner: Lead BA only. Module BA MUST NOT create or modify this file.**

Chỉ chạy step này sau khi Step 5.1a gate passed (library đã chốt trong DESIGN.md).

1. **Copy template:** `~/.claude/templates/control-type-library-template.md` (fallback: [../../../templates/control-type-library-template.md](../../../templates/control-type-library-template.md)) vào backbone directory.
   - File bắt đầu với baseline = `none`, 20 control type đầy đủ.

2. **Cập nhật baseline theo DESIGN.md library selection:**

   1. Đọc library docs (dùng `docs-seeker` skill hoặc WebFetch link docs từ DESIGN.md).
   2. Điền bảng Baseline trong control-type-library:
      - `Thư viện UI`: tên library từ DESIGN.md (vd `Shadcn UI`), hoặc `none` nếu không dùng.
      - `Phiên bản`: phiên bản đã chọn trong DESIGN.md.
      - `Docs tham chiếu`: link docs component của library.
   3. Nếu baseline = `none` → dừng. Giữ nguyên 20 control type.
   4. Nếu baseline = tên thư viện → so sánh từng control type với library default:

      | Hành động | Điều kiện |
      |-----------|-----------|
      | Giữ nguyên section | Behaviour **khác** library default (deviation) |
      | Xóa dòng behaviour đó | Behaviour **trùng** library default |
      | Giữ nguyên section | Library **không có** control type đó |
      | Giữ nguyên | Edge Case section — luôn giữ, đó là project-specific |

      Ví dụ: Shadcn Button mặc định có `disabled` state → xóa dòng `disabled` trong Default States của Button. Shadcn không có Stepper → giữ nguyên toàn bộ Stepper section.

   5. Không xóa heading hay cấu trúc section của control type. Chỉ xóa dòng behaviour cụ thể.
   6. Sau khi prune xong, file chỉ còn: baseline info + deviation behaviour + edge case.
   7. Module BA không sửa file này. Khi cần deviation mới → escalate lên Lead BA qua `impact`.

Also refresh `paths.project_home` using `~/.claude/templates/project-home-template.md` (fallback: [../../../templates/project-home-template.md](../../../templates/project-home-template.md)) so non-technical BAs can resume without understanding slug/date/module internals.

Project Home refresh must summarize phạm vi đã chốt, điều kiện tiến hành từng tài liệu, bước tiếp theo an toàn, and runtime quick prompts. Apply the wording-layer policy from `core/contract-behavior.md`: replace internal terms (`source of truth`, `decision ledger`, `artifact gate`, `canon`, `compile receipt`, `index`) with the approved Vietnamese labels. It is a dashboard only; do not duplicate full requirements or replace `backbone.md`.

The project memory must persist only the reusable anti-hallucination layer:

- canonical vocabulary and naming
- approved scope, actor, navigation, and rule decisions
- accepted assumptions with triggers for re-validation
- rejected assumptions or false trails that must not reappear
- accepted corrections and push-back triggers

Backbone rules:

- treat the backbone as the primary authoring source after intake
- do not draft FRD, stories, or SRS directly from raw intake once the backbone exists
- when UI-backed scope exists, lock portal ownership and route-group ownership here before any module-level screen work starts
- when UI-backed scope exists, persist `paths.design_doc` and `paths.shared_shell_contract` covering ALL portals from the Portal Matrix; module BAs are prohibited from creating or editing these files
- promote only the selected option's portal/module/actor/constraint decisions
- do not import rejected options or the full comparison into `backbone.md`
- keep the artifact concise and decision-oriented
- treat generated index/state/memory artifacts as `agent_facing` or `machine_facing`; keep them compact and do not duplicate source-of-truth requirement text
- keep `paths.backbone_index` as a navigator only: section names, trace IDs, module/feature hints, and short summaries; do not duplicate full requirement text
- do not self-certify `paths.backbone_index` as `current`; only the validator may promote it from `unknown`
- keep `project-memory.md` runtime-neutral so Claude Code, Codex, and Antigravity can all resume from the same accepted facts
