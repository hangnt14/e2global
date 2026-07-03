# Cài Đặt và Cấu Hình Antigravity

Antigravity hoạt động dựa trên cơ chế nạp bối cảnh hệ thống (system context). Nó có khả năng ghi nhớ dài hạn bằng bộ nhớ kiến thức (Knowledge Items - KIs), do đó, BA-kit chạy rất mạnh trên hệ máy này.

## Cách Dùng Trực Tiếp (Repo Native)

Nếu bạn chỉ cần mượn repo này để bắt đầu công việc:
1. Mở IDE kết nối với Antigravity.
2. Trỏ đường viền vào gốc của repo BA-kit.
3. Antigravity sẽ tự động đọc cấu trúc chỉ thị ở `GEMINI.md` (báo cáo quyền hạn) và `AGENTS.md` (mạng lưới routing).
4. Chat câu lệnh tiếng việt bình thường để làm việc:
```text
"Tạo cấu trúc workflow cho ứng dụng web bán sách"
"Tiếp tục dự án QL Kho, tôi nên làm gì tiếp?"
"Đánh giá thay đổi: xuất Excel phải ghi audit log"
"Chuẩn bị handoff UI cho phân hệ đăng nhập"
"Tôi nhận module thanh toán"
"Gửi module thanh toán cho Lead BA review"
```

## Cách Tích Hợp Sâu (Lưu Bộ Nhớ Cứng)

Nếu bạn muốn Antigravity của bạn "nạp" luôn bộ não BA-kit vào sâu bên trong tủy sống để xài lúc nào cũng được:
Chạy lệnh gốc này ở màn hình Terminal:
```bash
bash scripts/install-antigravity-ba-kit.sh
```
Nó sẽ:
1. Khởi tạo một Gói Kiến Thức `ba-kit-workflow` KI vào `~/.gemini/antigravity/knowledge/`.
2. Gắn lệnh tiện ích `ba-kit` vào `~/.local/bin`. 
3. Lưu vết cài đặt vào Data Tracking Manifest để nâng cấp về sau bằng lệnh `ba-kit update`.

## Routing Và Kích Hoạt Prompt
Trái với Claude (dùng dấu gạch chéo `/`), Antigravity định tuyến luồng công việc của bạn bằng ngôn ngữ tự nhiên tiếng Việt mượt mà. Đội ngũ phát triển đã nhúng sâu Auto-routing detection rule.

Chỉ cần gõ:
- "Impact đánh giá rủi ro cho chức năng xuất file PDF" (Kích hoạt change management)
- "Status của dự án QL Kho" (Kích hoạt kiểm thử độ hoàn chỉnh file document).
- "Chạy gói FRD" (Kích hoạt bộ kỹ năng xây dựng yêu cầu tính năng). 

## Adapter Guardrail Bảo Thủ (v1)

Với các lệnh có hard guardrail là `frd`, `stories`, `package`, `status`, `next`, Antigravity
không được giả định rằng runtime có hook chặn file-path như Codex hoặc Claude Code.

Luồng đúng ở v1 là chạy guardrail bên ngoài runtime rồi mới bơm packet ngắn vào Antigravity:

1. Chạy preflight:
```bash
python3 scripts/guardrail-preflight.py --repo . --command <cmd> --slug <slug> --date <date> --module <module>
```
Truoc do, neu vua tao hoac refresh `backbone_index`, `stories_index`, `srs_index`, hay chay:
```bash
python3 scripts/validate-index-quality.py --repo . --index-key <backbone_index|stories_index|srs_index> --slug <slug> --date <date> --writeback
```
Voi `stories_index` va `srs_index`, them `--module <module>` de validator resolve dung source artifact.
2. Nếu JSON trả về `status=block`, dừng ngay và chạy `refresh_command` được trả về. Không mở đọc rộng để "chữa cháy".
3. Nếu JSON trả về `status=warn`, chỉ tiếp tục khi operator cung cấp `READ_ESCALATION` rõ path và lý do; nếu không thì fail closed.
4. Nếu JSON trả về `status=ok` và có `excerpt_plan`, dựng excerpt hẹp:
```bash
python3 scripts/guardrail-build-excerpts.py --repo . --index-key <backbone_index|stories_index|srs_index> --slug <slug> --date <date> --module <module> --output-dir .tmp/guardrail/<trace-id>
```
5. Chỉ bơm vào Antigravity packet nhỏ nhất đủ cho action:
   - **probe** (`status=block` hoặc no-op): `output_mode=probe`, `status`, `command`, `resolved_slug`, `message` — không thêm field khác.
   - **delta** (`status=ok`/`warn` với index hiện tại): probe fields + `indexes.<name>.state`, `action_guardrail` (nếu có), `allow_reads`, `excerpt_path` (nếu đã build).
   - **full** (escalation, broad read, hoặc không có index hiện tại): delta fields + `deny_reads`, `canonical_state_summary`, `canonical_next_command`, `refresh_command` (nếu block).
   - Xem `CLAUDE.md` Runtime Guardrails → Output Modes để biết định nghĩa field chuẩn.
6. Sau khi runtime phản hồi, lưu reads manifest thủ công hoặc qua wrapper rồi audit:
```bash
python3 scripts/guardrail-audit.py --preflight <preflight.json> --reads-manifest <reads.json>
```

Không dùng Antigravity v1 để hứa hẹn:
- chặn native theo `allow_reads` / `deny_reads`
- tự pause giữa chừng để hỏi HITL
- tự suy diễn broad read khi chưa có `READ_ESCALATION`

## UX Cho BA Non-Tech

BA-kit tạo `plans/{slug}-{date}/PROJECT-HOME.md` như trang điều phối dự án:
- Đang ở bước nào
- Bước BA tiếp theo nên làm
- Câu hỏi cần user chốt
- Prompt nhanh cho Antigravity, Codex, Claude
- Mapping tên dễ hiểu sang workflow nội bộ

Antigravity có thể tham khảo file này khi user nói "tiếp tục dự án", nhưng với `status` và
`next` thì `PROJECT-HOME.md` chỉ là dashboard. Trạng thái chuẩn vẫn phải chốt từ artifact
canonical theo contract; dashboard không được ghi đè lifecycle state hoặc next-step resolution.

Với `frd`, `stories`, `package`, Antigravity không nên discovery-read full `backbone.md`,
`stories.md`, `srs.md`, hoặc nguồn raw chỉ vì user nhắc tới chúng. Hãy đi theo verdict của
preflight, validator state, va excerpt đã được dựng trước. Moi action routeable tu backbone
nen nhac lai packet index-first gon, khong duoc dua vao tri nho cua session truoc.

## UX Cộng Tác Module

BA có thể dùng NLP thay vì Git:
- "Tôi nhận module auth-flow"
- "Kiểm tra module payment trước khi gửi review"
- "Tôi làm xong module payment, gửi Lead BA review"
- "Tạo PR cho module payment"

Agent route sang `ba-collab`, cập nhật `COLLAB-HOME.md`, `MODULE-HOME.md`, và review packet. Commit/push/PR/merge chỉ chạy khi user approve rõ.
