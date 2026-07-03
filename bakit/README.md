# BA-kit Course

<div align="center">

[![bakit-org - bakit](https://img.shields.io/static/v1?label=bakit-org&message=bakit&color=blue&logo=github)](https://github.com/bakit-org/bakit)

[![License](https://img.shields.io/badge/License-Commercial-blue)](#license)

[![view - Documentation](https://img.shields.io/badge/view-Documentation-blue?style=for-the-badge)](https://docs.bakit.ai.vn)

[![Made with Bash](https://img.shields.io/badge/Bash->=3-blue?logo=gnu-bash&logoColor=white)](https://www.gnu.org/software/bash/)
[![Made with Python](https://img.shields.io/badge/Python->=3.13-blue?logo=python&logoColor=white)](https://python.org)

[![Agent - Claude Code](https://img.shields.io/badge/Agent-Claude_Code-2ea44f&logo=claudecode)](https://claude.com/product/claude-code)
[![Agent - CodeX](https://img.shields.io/badge/Agent-CodeX-2ea44f)](https://openai.com/codex/)
[![Agent - Antigravity 2.0](https://img.shields.io/badge/Agent-Antigravity_2.0-2ea44f)](https://antigravity.google/)
[![Agent - Antigravity CLI](https://img.shields.io/badge/Agent-Antigravity_CLI-2ea44f)](https://antigravity.google/)
[![Agent - Antigravity IDE](https://img.shields.io/badge/Agent-Antigravity_IDE-2ea44f)](https://antigravity.google/)

</div>

BA-kit Course là phiên bản đầy đủ nhất — playbook Business Analysis cho Claude Code, Codex, và Antigravity. Repo này biến agent thành một BA workstation có lifecycle rõ ràng, artifact có cấu trúc, collaboration theo module, và handoff đủ chuẩn cho stakeholder/engineering. Dành cho học viên khoá học BA-kit.



## License

BA-kit is distributed under a commercial proprietary source-available license.
This commercial proprietary license is provided on a source-available basis.

Access to this repository does not grant redistribution rights. Customers may
use, privately fork, and internally customize BA-kit only within the single
legal entity that purchased or was granted access, subject to the terms in
`LICENSE` and any applicable order form or MSA.

Tài liệu chi tiết: [BA-kit GitBook](https://bakit.gitbook.io/)

Nếu mới dùng lần đầu, đọc guide thực hành trước: [BA-kit Step-by-Step Guide](docs/ba-kit-step-by-step-guide.md).

## BA Làm Gì Với BA-kit?

BA có thể dùng ngôn ngữ tự nhiên thay vì nhớ command:

```text
Tôi có tài liệu yêu cầu mới, hãy tạo dự án BA
Tiếp tục dự án warehouse-rfp, bước tiếp theo là gì?
Đánh giá thay đổi: Export CSV phải có audit log
Phân tích ngược hệ thống hiện tại để tạo as-built SRS
Tôi nhận module auth-flow
Gửi module auth-flow cho Lead BA review
Đồng bộ module reporting với main trước khi làm tiếp
Xuất gói bàn giao cho stakeholder
```

Agent sẽ map intent sang workflow an toàn:

- Lifecycle BA: intake, options khi cần, backbone, stories, FRD, SRS with mandatory ASCII, package.
- Reverse BA: quét code/evidence để dựng as-built SRS, khóa baseline commit, theo dõi drift, và chỉ promote nội dung có evidence rõ.
- Collaboration BA: claim module, check conflict, create review packet, optional GitHub PR handoff.
- Git/GitHub là implementation detail; commit, push, PR, merge chỉ chạy khi user approve rõ.

## Các Actor và Các Bước

BA-kit phục vụ 6 actor chính. Mỗi actor có chuỗi bước riêng, bắt đầu từ khởi tạo dự án đến bàn giao.

### 1. Lead BA / Solo BA — Điều Phối & Khởi Tạo

Lead BA chịu trách nhiệm toàn bộ dự án khi solo, hoặc điều phối module khi multi-BA.

| # | Bước | Command / Hành Động | Output Chính |
|---|------|---------------------|--------------|
| 1 | **Cài đặt BA-kit** | `./install.sh` → `ba-kit doctor` | Skills, rules, templates vào `~/.claude/` |
| 2 | **Khởi tạo dự án** | `/ba-start intake <file>` hoặc `/ba-do Tôi có tài liệu...` | `PROJECT-HOME.md`, `01_intake/intake.md`, `01_intake/plan.md` |
| 3 | **Review intake** | Đọc `intake.md`, trả lời câu hỏi gap analysis | Intake chuẩn hóa: stakeholder, goal, scope, mode |
| 4 | **Options** (nếu cần) | `/ba-start options --slug <slug>` → `--select option-N` hoặc `--skip` | `01_intake/options/comparison.md` |
| 5 | **Xây backbone** | `/ba-start backbone --slug <slug>` | `02_backbone/backbone.md`, `project-memory.md`, shared rules/messages |
| 6 | **Chốt UI/IA** (nếu có UI) | Persist `DESIGN.md` + `shared-shell-contract.md` | Portal matrix, nav schema, shell variant |
| 7a | **Solo: viết module** | Chạy `stories` → `srs` cho từng module (xem bảng Module BA) | `03_modules/{module}/*` |
| 7b | **Multi-BA: chia module** | Tạo `COLLAB-HOME.md`, giao module cho từng BA | Module list, owner map, write scope |
| 8 | **Review cross-module** | `/ba-start status --slug <slug>`, `/ba-collab status --slug <slug>` | Phát hiện conflict terminology, rule/message code, menu |
| 9 | **Package bàn giao** | `/ba-start package --slug <slug>` | `04_compiled/compiled-frd.html`, `compiled-srs.html` |
| 10 | **Xử lý thay đổi** | `/ba-start impact --slug <slug> "mô tả..."` | Impact report, đề xuất command cần chạy lại |

### 2. Module BA — Viết Artifact Trong Module Được Giao

Module BA chỉ làm việc trong module đã nhận, không sửa module khác hay shared shell.

| # | Bước | Command / Hành Động | Output Chính |
|---|------|---------------------|--------------|
| 1 | **Nhận module** | `/ba-collab Tôi nhận module <module>` | `MODULE-HOME.md` |
| 2 | **Viết user stories** | `/ba-start stories --slug <slug> --module <module>` | `userstories/index.md`, `us-*.md` |
| 3 | **Viết FRD** (nếu cần) | `/ba-start frd --slug <slug> --module <module>` | `frd.md` |
| 4 | **Viết SRS canon** | `/ba-start srs --slug <slug> --module <module>` | `usecases/*.md`, `ascii-screen/*.md`, `srs/*.md`, `srs-index.md`, `srs.md` |
| 5 | **Kiểm tra SRS** | `ba-kit doctor-srs plans/{slug}-{date}/03_modules/{module}` | Xác nhận canon đúng schema, Behaviour Rules hợp lệ, compile receipt hợp lệ |
| 6 | **Gửi review** | `/ba-collab Gửi module <module> cho Lead BA review` | `delegation/review-packets/{module}.md` |
| 7 | **Sửa theo feedback** | Quay lại bước 4-5, chỉ sửa canon, compile lại `srs.md` | Canon cập nhật, receipt mới |

### 3. Stakeholder — Cung Cấp Yêu Cầu & Phê Duyệt

Stakeholder không chạy command. Họ tương tác qua BA.

| # | Bước | Hành Động |
|---|------|-----------|
| 1 | **Cung cấp yêu cầu** | Gửi file (PDF, doc, slide) hoặc mô tả bằng text |
| 2 | **Trả lời gap analysis** | BA hỏi → stakeholder chốt: ai, mục tiêu, scope, ưu tiên |
| 3 | **Review intake + backbone** | Đọc `intake.md` và `backbone.md`, xác nhận scope trước khi BA viết downstream |
| 4 | **Review options** (nếu có) | Xem `options/comparison.md`, chọn phương án |
| 5 | **Review SRS/FRD** | Đọc `compiled-srs.html` hoặc `compiled-frd.html` trong browser |
| 6 | **Đưa change request** | Báo BA: "Xuất CSV phải có audit log" → BA chạy `impact` |
| 7 | **Phê duyệt deliverables** | Xác nhận package cuối trước khi handoff cho dev/test |

### 4. UI/UX Designer — Thiết Kế Giao Diện Từ Canon

Designer làm việc downstream, không định nghĩa requirement mới.

| # | Bước | Hành Động | Input |
|---|------|-----------|-------|
| 1 | **Đọc design direction** | Nắm visual tone, component baseline, layout principles | `designs/{slug}/DESIGN.md` |
| 2 | **Đọc shared shell** | Nắm portal matrix, nav schema, active menu | `02_backbone/shared-shell-contract.md` |
| 3 | **Sync Figma** (optional) | `/ba-figma-sync --slug <slug> --module <module>` | `ascii-screen/*.md` → Figma frames |
| 4 | **Báo mismatch** | Nếu Figma khác canon → báo BA sửa canon trước, sync lại sau | `figma-mismatch-report.md` |

**Nguyên tắc:** Canon là source of truth. Không sửa canon từ Figma.

### 5. QC / Test Lead — Kiểm Tra Chất Lượng Module SRS

QC đọc module canon để đánh giá mức độ sẵn sàng cho test design.

| # | Bước | Hành Động | Output |
|---|------|-----------|--------|
| 1 | **QC review module** | `/ba-start srs` xong → tự động trigger QC, hoặc chạy `qc-uc-review` | `qc-review/{module}-qc-review-report-vN.md` |
| 2 | **Đọc canon** | Duyệt `usecases/*.md`, `ascii-screen/*.md`, `srs/*.md`, field contract | — |
| 3 | **Chấm điểm & báo gap** | Verdict readiness, completeness score (0-100%), gap report | QC report + question backlog |
| 4 | **Block nếu < 70%** | Gate cứng: score < 70 → BA phải sửa canon trước khi test design | — |

### 6. Developer — Nhận Đặc Tả Để Triển Khai

Developer nhận SRS compiled làm input chính cho implementation.

| # | Bước | Input |
|---|------|-------|
| 1 | **Đọc SRS compiled** | `04_compiled/compiled-srs.html` hoặc `03_modules/{module}/srs.md` |
| 2 | **Đọc use case** | `usecases/uc-*.md` — main flow, alternate flow, pre/post conditions |
| 3 | **Đọc screen spec** | `ascii-screen/*.md` — field table, display/behaviour/validation rules, ASCII wireframe, states |
| 4 | **Đọc data model** (nếu có) | `srs/erd.md` |
| 5 | **Đọc shared rules** | `02_backbone/common-rules.md`, `message-list.md` — CR-*, MSG-* codes |
| 6 | **Implement** | Code theo field contract, validation rules, screen states |

---

## Flow Hiện Tại

```text
Raw input
-> Intake + Gap Analysis
-> PROJECT-HOME.md
-> Option pack + comparison khi intake cần nhiều hướng solution
-> Requirements Backbone
-> Module canon artifacts: FRD / userstories/*.md / usecases/*.md / ascii-screen/*.md / srs/*.md
-> DESIGN.md + shared-shell-contract.md
-> Compiled SRS deliverable (`srs.md`) with screen descriptions + ASCII wireframes
-> Optional Figma sync as downstream consumer
-> Optional tool lane: screen-field-contract + Make control pack + conformance review
-> Final SRS + HTML package
```

Với teamwork:

```text
Lead BA chia module
-> COLLAB-HOME.md
-> Module BA nhận module
-> MODULE-HOME.md
-> Module BA tạo/cập nhật artifact trong module scope
-> review packet
-> Lead BA review / approve / integrate
-> optional GitHub PR, approval-gated
```

## Artifact Chính

| Artifact | Vai trò |
| --- | --- |
| `PROJECT-HOME.md` | Dashboard BA-facing: trạng thái, bước tiếp theo, câu hỏi cần chốt, prompt nhanh cho runtime |
| `01_intake/intake.md` | Input đã chuẩn hóa, gap analysis, câu hỏi mở |
| `01_intake/plan.md` | Kế hoạch artifact sẽ sinh theo mode/gate |
| `01_intake/options/*` | Bộ phương án solution và bảng so sánh trước backbone |
| `02_backbone/backbone.md` | Tài liệu gốc sau khi chốt phạm vi |
| `02_backbone/common-rules.md` | Registry duy nhất cho rule code dùng chung `CR-*` |
| `02_backbone/message-list.md` | Registry duy nhất cho message code dùng chung `MSG-*` |
| `02_backbone/shared-rule-message-index.md` | Index gọn để runtime đọc trước khi mở registry đầy đủ |
| `02_backbone/project-memory.md` | Bộ nhớ dự án: thuật ngữ, quyết định, assumptions, corrections |
| `COLLAB-HOME.md` | Dashboard cộng tác: ai làm module nào, review status, blocker |
| `03_modules/{module}/MODULE-HOME.md` | Dashboard riêng cho Module BA: scope được sửa, checklist review |
| `03_modules/{module}/frd.md` | Functional Requirements Document theo module |
| `03_modules/{module}/userstories/*.md` + `userstories/index.md` | User stories và acceptance criteria |
| `03_modules/{module}/srs.md` | SRS/use case/screen spec theo module |
| `ascii-screen/*.md` / `usecases/*.md` / `srs/*.md` | Canon authoring sources; mỗi UI-backed screen phải có ASCII wireframe |
| `03_modules/{module}/screen-field-contract.yaml` | Contract máy đọc được cho field/rule/state/navigation sau Step 8.1 |
| `03_modules/{module}/tool-lanes/tool-lane-state.md` | Lane đã chọn cho Step 9: `manual` mặc định hoặc tool lane opt-in |
| `05_tool-lanes/figma-make/*` | Shared prompt skeleton và shared component contracts cho Figma Make |
| `03_modules/{module}/tool-lanes/figma-make/make-*.md` | Legacy/optional prompt pack theo module cho Figma Make |
| `03_modules/{module}/tool-lanes/figma-make/prototype-conformance-*.md` | Legacy/optional checklist và report reject gate cho output từ tool lane |
| `delegation/review-packets/{module}.md` | Gói gửi Lead BA review |
| `04_compiled/*.html` | Bản HTML stakeholder review/edit trong browser |
| `designs/{slug}/DESIGN.md` | Design direction runtime cho UI handoff |

`PROJECT-HOME.md`, `COLLAB-HOME.md`, và `MODULE-HOME.md` là trang điều phối. Tài liệu gốc vẫn là `backbone.md`, sau đó là `intake.md` và module artifacts.

## Cấu Trúc Thư Mục

```text
plans/
  {slug}-{date}/
    PROJECT-HOME.md
    COLLAB-HOME.md
    00_source/
      manifest.json
      summary.md
      chunks/
      chunk-index.md
    00_reverse/
      reverse-baseline-lock.json
      reverse-index.md
      reverse-focus-excerpts.md
      reverse-evidence-ledger.md
      reverse-drift-state.json
      reverse-read-manifest.ndjson
    01_intake/
      intake.md
      plan.md
      options/
        index.md
        option-01.md
        option-02.md
        option-03.md
        comparison.md
        options-receipt.md
    02_backbone/
      backbone.md
      backbone-index.md
      common-rules.md
      message-list.md
      shared-rule-message-index.md
      shared-shell-contract.md
      shared-shell-index.md
      impact-receipt.md
      index-validation-receipt.md
      package-snapshot.md
      project-memory.md
      project-memory/
        index.md
        log.md
        hot/
          canonical-vocabulary.md
          approved-decisions.md
          pushback-triggers.md
        warm/
          modules/
            {module_slug}.md
        cold/
    03_modules/
      {module_slug}/
        MODULE-HOME.md
        frd.md
        userstories/
          index.md
          us-{story_slug}.md
        ascii-screen/
          index.md
          {screen_slug}.md
        usecases/
          index.md
          uc-{usecase_slug}.md
          diagrams.md
        srs/
          spec.md
          flows.md
          states.md
          erd.md
        srs.md
        srs-compile-receipt.json
          srs-group-f.md
        srs-compile-receipt.json
        screen-field-contract.yaml
        tool-lanes/
          tool-lane-state.md
          figma-make/
            make-guidelines.md
            make-prompt-pack.md
            prototype-conformance-checklist.md
            prototype-conformance-report.md
        figma-sync/
          figma-sync-report.md
          figma-mismatch-report.md
    04_compiled/
      compiled-frd.html
      compiled-srs.html
    05_tool-lanes/
      figma-make/
        shared-rules.md
        shared-prompt-skeleton.md
        shared-component-contracts.md
    delegation/
      packets/
      review-packets/

designs/
  {slug}/
    DESIGN.md
```

## Cài Đặt Nhanh

> Repo access is granted per licensed customer account. If you need access for
> another legal entity, affiliate, contractor, or client organization, that use
> requires a separate written commercial grant.

### Claude Code

```bash
git clone https://github.com/anhdam2/bakit.git
cd bakit
./install.sh
```

Sau đó restart Claude Code.

### Codex

Repo-native: mở repo này trong Codex, Codex đọc `AGENTS.md`.

Bundle install:

```bash
bash scripts/install-codex-ba-kit.sh
```

### Antigravity

```bash
bash scripts/install-antigravity-ba-kit.sh
```

Script cài CLI `ba-kit`, ghi installation manifest, và tạo Knowledge Item workflow cho Antigravity.

## Command Surface

BA non-tech nên bắt đầu bằng natural language qua router:

```text
/ba-do Tôi có tài liệu yêu cầu mới, hãy tạo dự án BA
/ba-do Tiếp tục dự án warehouse-rfp
/ba-do Phân tích ngược hệ thống hiện tại để tạo as-built SRS
/ba-do Tôi nhận module auth-flow
/ba-do Gửi module auth-flow cho Lead BA review
```

Command-level fallback:

```text
/ba-start
/ba-start options --slug warehouse-rfp
/ba-start options --slug warehouse-rfp --select option-02
/ba-start options --slug warehouse-rfp --skip
/ba-start backbone --slug warehouse-rfp
/ba-start srs --slug warehouse-rfp --module auth-flow
/ba-start package --slug warehouse-rfp
/ba-start status --slug warehouse-rfp
/ba-start reverse --slug warehouse-rfp
/ba-start reverse impact --slug warehouse-rfp
/ba-figma-sync --slug warehouse-rfp --module auth-flow
/ba-collab Tôi nhận module auth-flow
/ba-collab Gửi module auth-flow cho Lead BA review
```

Dùng `options` khi intake cho thấy cần 1-3 hướng solution trước khi viết `backbone.md`. Step này tạo option pack + comparison dưới `01_intake/options/*`, rồi chốt `--select` hoặc `--skip` rõ ràng trước khi sang backbone.

Dùng `reverse` khi mục tiêu là dựng tài liệu as-built từ hệ thống đang chạy hoặc code đã commit. Reverse lane chỉ promote nội dung có evidence rõ, không suy diễn business intent, không dùng cho future-state request, và bỏ qua wireframes vì không đề xuất UI mới. Nếu user đang yêu cầu thay đổi mong muốn trong tương lai, chuyển sang `impact` hoặc lifecycle forward bình thường.

## Tool Lane Sau SRS

- ASCII wireframe luôn bắt buộc trong `03_modules/{module}/ascii-screen/*.md` và được compile vào `srs.md`.
- Nếu user opt-in `figma-make`, BA-kit không dùng raw `srs.md` làm prompt chính.
- `srs` phải compile `screen-field-contract.yaml` sau Group C / Step 8.1.
- Tool lane đọc contract này để sinh:
  - shared prompt assets ở `05_tool-lanes/figma-make/`
  - `03_modules/{module}/tool-lanes/figma-make/make-guidelines.md`
  - `03_modules/{module}/tool-lanes/figma-make/make-prompt-pack.md`
  - `03_modules/{module}/tool-lanes/figma-make/prototype-conformance-checklist.md`
  - `03_modules/{module}/tool-lanes/figma-make/prototype-conformance-report.md`
- Requirement drift phát hiện từ prototype phải route qua `impact`, không back-write vào SRS.

Chi tiết: [docs/figma-make-lane.md](./docs/figma-make-lane.md)

CLI helper:

```bash
ba-kit doctor
ba-kit install-plantuml
ba-kit update
ba-kit status --slug warehouse-rfp
ba-kit collab status --slug warehouse-rfp
```

## Teamwork Và GitHub

BA-kit hỗ trợ module collaboration nhưng không bắt BA học Git trước.

BA nói:

```text
Tôi nhận module reporting
Đồng bộ module reporting với main
Kiểm tra module reporting trước khi gửi review
Tạo PR cho module reporting
```

Agent xử lý nội bộ:

- Resolve đúng project/module.
- Kiểm tra module ownership và write scope.
- Cập nhật `COLLAB-HOME.md`, `MODULE-HOME.md`, review packet.
- Chạy impact nếu thay đổi chạm requirement/shared decision.
- Chỉ commit/push/PR/merge khi user approve rõ.
- Nếu conflict nghiệp vụ hoặc Git conflict, dừng và báo file/section cần Lead BA quyết định.

## Wireframe Handoff

`/ba-start srs` đang chuyển dần sang mô hình canon-first:

- `03_modules/{module}/ascii-screen/*.md`
- `03_modules/{module}/usecases/*.md`
- `03_modules/{module}/srs/spec.md`
- `03_modules/{module}/srs/flows.md`, `srs/states.md`, `srs/erd.md` khi cần
- `03_modules/{module}/usecases/index.md`
- `03_modules/{module}/ascii-screen/index.md`
- `03_modules/{module}/srs.md` như compiled deliverable đầy đủ

Direct edit nên đi vào canon sources trước, rồi mới compile lại `srs.md`.

Guardrail nhanh:

```bash
ba-kit doctor-srs plans/{slug}-{date}/03_modules/{module}
ba-kit check-write-scope --command figma-sync plans/{slug}-{date}/03_modules/{module}/ascii-screen/scr-01.md
```

`doctor-srs` kiểm tra `ascii-screen/index.md`, screen canon schema, Behaviour Rules trong `ascii-screen/*.md` khi có screen canon, source-of-truth invariants, và compile receipt. `check-write-scope` dùng cho hook/runtime để chặn lệnh downstream như Figma sync sửa nhầm canon.

`/ba-start wireframes` chỉ còn là compatibility validation command. Flow hiện tại không tạo legacy wireframe pack artifacts. Nếu ASCII thiếu hoặc stale, chạy lại `/ba-start srs --slug <slug> --module <module>`.

User hoặc designer có thể attach mockup ngoài vào đúng section trong SRS. Mockup không phải source of truth và không thay thế ASCII wireframe.

Figma MCP sync là lane riêng sau SRS canon:

```text
/ba-figma-sync --slug {slug} --module {module}
/ba-do Đồng bộ Figma cho module {module} của dự án {slug}
```

Nó chỉ đọc `ascii-screen/index.md`, `ascii-screen/*.md`, `DESIGN.md`, `shared-shell-contract.md`, và `shared-rule-message-index.md`, rồi ghi `figma-sync/figma-sync-report.md` hoặc `figma-sync/figma-mismatch-report.md`. Nếu Figma khác canon, sửa canon trước rồi sync lại; không sửa Figma rồi coi đó là requirement mới.

## Nâng Cấp

```bash
ba-kit doctor
ba-kit install-plantuml
ba-kit update
```

`ba-kit doctor` kiểm tra runtime readiness. `ba-kit install-plantuml` auto cài PlantUML local bằng package manager phù hợp để HTML packaging ưu tiên render diagram tại máy. `ba-kit update` fast-forward source repo và reinstall các runtime đã cài.

## BA-kit Editions

BA-kit có 3 phiên bản, mỗi bản phục vụ một đối tượng khác nhau:

| | Solo Basic (free) | Solo Pro (paid) | BA-kit Course (repo này) |
|---|---|---|---|
| **Đối tượng** | BA mới, dự án nhỏ | BA solo chuyên nghiệp | Học viên khoá học |
| **Skills** | 5 | 8 | 14 |
| **Cài đặt** | Copy thủ công | `install.sh` + CLI | `install.sh` + CLI |
| **Scripts / Hooks** | ❌ | ✅ | ✅ |
| **Lifecycle** | Cơ bản | Đầy đủ | Đầy đủ |
| **Templates** | Đầy đủ | Đầy đủ | Đầy đủ |
| **Stitch sync** | ❌ | ✅ | ✅ |
| **Content audit** | ❌ | ✅ | ✅ |
| **Auto index / guardrails** | ❌ (thủ công) | ✅ (cơ bản) | ✅ (đầy đủ) |
| **Self-update** | ❌ | ✅ | ✅ |
| **Figma sync** | ❌ | ❌ | ✅ |
| **QC review** | ❌ | ❌ | ✅ |
| **Multi-BA collab** | ❌ | ❌ | ✅ |
| **Reverse engineering** | ❌ | ❌ | ✅ |
| **Notion publish** | ❌ | ❌ | ✅ |
| **QC export bridge** | ❌ | ❌ | ✅ |
| **Context budget (full)** | ❌ | ❌ | ✅ |
| **Tool lanes** | ❌ | ❌ | ✅ |
| **Project memory shards** | ❌ | ❌ | ✅ |
| **Ghi đè khi cài** | Bị Solo Pro/Course ghi đè | Bị Course ghi đè | Không bị ghi đè |

`install.sh` của bản cao hơn sẽ ghi đè bản thấp hơn nếu cùng installed location.

## Đọc Tiếp

- [BA-kit GitBook](https://bakit.gitbook.io/)
- [Getting Started](docs/getting-started.md)
- [Codex Setup](docs/codex-setup.md)
- [Antigravity Setup](docs/antigravity-setup.md)
- [Skill Catalog](docs/skill-catalog.md)
- [BA Methodology Guide](docs/ba-methodology-guide.md)
- [Design Artifacts](designs/README.md)
