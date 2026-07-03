# Trang điều phối dự án BA (Project Home)

> File này là dashboard thân thiện cho BA non-tech. Nó không thay thế `intake.md`, `backbone.md`, `project-memory.md`, hoặc artifact module. Agent phải dùng file này để định hướng người dùng, nhưng vẫn đọc source-of-truth đúng theo contract trước khi mutate artifact.

**Dự án:** [Tên dự án]
**Slug:** [initiative-slug]
**Phiên bản artifact:** [YYMMDD-HHmm]
**Chế độ:** [lite | hybrid | formal]
**Cập nhật lần cuối:** [YYYY-MM-DD HH:mm]
**Runtime gần nhất:** [claude-code | codex | antigravity | mixed]

> Trạng thái lifecycle chuẩn trong dashboard này: `recommended` = nên làm tiếp nhưng chưa bắt đầu, `in-progress` = đang thực hiện, `completed` = đã xong/đã chốt, `skipped` = chủ động bỏ qua có lý do, `not-needed` = không cần cho dự án này. Chỉ dùng tập trạng thái này, không quay lại bộ nhãn task-board cũ.

## 1. Tôi Đang Ở Đâu?

| Hạng mục | Trạng thái | Ý nghĩa cho BA |
| --- | --- | --- |
| Tiếp nhận yêu cầu | [recommended | in-progress | completed] | Đã gom và chuẩn hóa thông tin đầu vào chưa |
| Phương án giải pháp | [recommended | in-progress | completed | skipped | not-needed] | Đã cần brainstorm và chốt hướng solution trước backbone chưa |
| Khung yêu cầu đã chốt | [recommended | in-progress | completed] | Đã có tài liệu gốc để sinh tài liệu chưa |
| User stories | [recommended | in-progress | completed | skipped | not-needed] | Có cần bàn giao cho team Agile không |
| FRD | [recommended | in-progress | completed | skipped | not-needed] | Có cần tài liệu yêu cầu chức năng chi tiết không |
| SRS | [recommended | in-progress | completed | skipped | not-needed] | Có cần đặc tả hệ thống/use case/screen không |
| Handoff UI | [recommended | in-progress | completed | skipped | not-needed] | Có cần gói constraint để user tự vẽ mockup không |
| Gói bàn giao HTML | [recommended | in-progress | completed | skipped | not-needed] | Có bản stakeholder review trong browser chưa |

## 1a. Danh Sách Module

| Module ID | Tên module | Module BA | Trạng thái | Ghi chú |
| --- | --- | --- | --- | --- |
| MOD-01 | [Tên module] | [@BA-handle hoặc TBD] | [recommended / in-progress / completed] | [Ghi chú] |

## 2. Bước Tiếp Theo Được Khuyến Nghị

**Nên làm tiếp:** [Mô tả bằng ngôn ngữ BA]

**Lý do:** [Gắn với mục tiêu, rủi ro, hoặc artifact còn thiếu]

**Agent sẽ chạy nội bộ:** `[ba-start/ba-next/ba-impact command equivalent]`

**Nếu bạn không chắc, hãy hỏi agent:** `Tôi nên làm bước nào tiếp theo cho dự án này?`

## 3. Việc Cần User Chốt

| Câu hỏi / Quyết định | Vì sao cần chốt | Nếu chưa chốt thì ảnh hưởng |
| --- | --- | --- |
| [Decision] | [Reason] | [Impact] |

## 4. Bản Đồ Artifact Dễ Hiểu

| Tên BA nhìn thấy | File kỹ thuật | Khi nào dùng |
| --- | --- | --- |
| Trang điều phối dự án | `PROJECT-HOME.md` | Xem trạng thái, bước tiếp theo, câu hỏi cần chốt |
| Phiếu tiếp nhận yêu cầu | `01_intake/intake.md` | Lưu input đã chuẩn hóa và gap |
| Kế hoạch xử lý | `01_intake/plan.md` | Decision ledger cho optioning status, khuyến nghị bước tiếp theo, và tài liệu cần sinh |
| Bộ phương án giải pháp | `01_intake/options/*` | Xem các option solution và bảng so sánh trước khi chốt backbone |
| Khung yêu cầu đã chốt | `02_backbone/backbone.md` | Tài liệu gốc sau khi chốt phạm vi |
| Bộ nhớ dự án | `02_backbone/project-memory.md` | Thuật ngữ, quyết định, giả định đã chốt |
| Tài liệu module | `03_modules/{module}/...` | FRD, stories, SRS, UI handoff theo phân hệ |
| Trang cộng tác | `COLLAB-HOME.md` | Ai làm module nào, review status, blocker |
| Bản bàn giao HTML | `04_compiled/*.html` | Stakeholder review/edit trong browser |

## 5. Prompt Nhanh Theo Runtime

### Claude Code

```text
/ba-do Tôi muốn tiếp tục dự án [slug]. Hãy đọc PROJECT-HOME.md và cho tôi bước tiếp theo.
```

### Codex

```text
Use AGENTS.md. Read PROJECT-HOME.md for the BA-facing state, then use the BA-kit contract to run the next safe step for slug [slug].
```

### Antigravity

```text
Đọc PROJECT-HOME.md của dự án [slug], cho tôi biết bước BA tiếp theo và chạy workflow an toàn tương ứng.
```

## 6. Từ Điển Tên Gọi Thân Thiện

| BA nói | Agent hiểu |
| --- | --- |
| Tạo dự án mới / phân tích tài liệu mới | `intake` hoặc full lifecycle |
| Tiếp tục dự án | `ba-next` rồi step được khuyến nghị |
| Brainstorm phương án / chốt option | `options` |
| Khung yêu cầu đã chốt | `backbone` |
| Đánh giá thay đổi | `impact` |
| Chuẩn bị handoff UI | `wireframes` |
| Xuất gói bàn giao | `package` |
| Kiểm tra trạng thái | `status` |
| Nhận module / gửi review / tạo PR | `ba-collab` |

## 7. Lưu Ý An Toàn

- Nếu yêu cầu thay đổi trong lúc đang viết FRD/SRS/UI, agent phải đánh giá ảnh hưởng trước khi sửa.
- Nếu có nhiều phiên bản artifact hoặc nhiều module, agent phải hỏi lại thay vì tự chọn.
- File này là trang điều phối. Khi có mâu thuẫn, tài liệu gốc vẫn là `backbone.md`, sau đó là `intake.md`.
