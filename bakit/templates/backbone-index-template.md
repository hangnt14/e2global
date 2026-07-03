# Chỉ mục backbone (Backbone Index)

## Metadata

| Field | Value |
| --- | --- |
| index_type | backbone |
| source_artifact | `plans/{slug}-{date}/02_backbone/backbone.md` |
| source_hash | [sha256] |
| generated_at | [YYYY-MM-DDTHH:mm:ssZ] |
| generated_by_command | `ba-start backbone` |
| stale_status | unknown |
| validated_at | [YYYY-MM-DDTHH:mm:ssZ after validator pass; blank when pending or failed] |
| validated_by | [`validate-index-quality` or runtime validator id; blank when pending or failed] |
| coverage_summary | [Các section và trace anchor trong backbone] |

Producer note: index mới sinh phải giữ `stale_status: unknown`; chỉ validator mới được điền `validated_at`, `validated_by`, và nâng lên `current`.

## Section Index

| Section | Anchor / Heading | Trace IDs | Module / Feature | Short Summary |
| --- | --- | --- | --- | --- |
| [Section name] | [Heading] | [FR-01, ACT-01] | [module/feature] | [1-2 dòng tóm tắt] |

## Producer Instructions (BẮT BUỘC — KHÔNG ĐƯỢC BỎ QUA)

Khi tạo backbone-index.md, PHẢI tuân thủ các quy tắc sau:

### 1. source_hash — PHẢI tính SHA256 thật
- Đọc file `backbone.md`.
- Chạy `python3 -c "import hashlib; print(hashlib.sha256(open('backbone.md','rb').read()).hexdigest())"`.
- Điền kết quả vào `source_hash`. KHÔNG để `[sha256]`, KHÔNG để `to-be-computed`, KHÔNG để placeholder.

### 2. Anchor / Heading — PHẢI khớp CHÍNH XÁC với backbone.md
- Copy-paste nguyên văn heading từ `backbone.md` (bao gồm cả dấu câu, khoảng trắng, chữ hoa/thường).
- Ví dụ: nếu backbone.md có heading `Mục tiêu kinh doanh và chỉ số thành công`, thì Anchor/Heading cũng phải là `Mục tiêu kinh doanh và chỉ số thành công`, KHÔNG viết tắt thành `Mục tiêu kinh doanh`.

### 3. Trace IDs — MỖI DÒNG PHẢI CÓ ÍT NHẤT 1 ID
- Mỗi dòng index PHẢI có ít nhất 1 Trace ID hợp lệ từ backbone.md.
- KHÔNG dùng `—` (em dash) nếu không có ID.
- ID family tương ứng với section:
  - BG-* → Mục tiêu kinh doanh
  - ACT-* → Nhóm người dùng và tác nhân
  - PORTAL-* → Ma trận portal
  - F-* → Bản đồ tính năng
  - F-* → Bản đồ tính năng
  - MOD-* → Danh sách module
  - FR-* → Backbone yêu cầu chức năng
  - NFR-* → Backbone yêu cầu phi chức năng
  - EP-* → Story Map
  - SCR-* → UI và màn hình
  - A1, A2, ... → Assumptions
  - R-* → Risks

### 4. Mỗi section trong backbone.md PHẢI có 1 dòng index
- Tất cả các heading cấp ≤ 3 trong backbone.md đều phải có dòng index tương ứng.
- KHÔNG được bỏ sót section nào.

### 5. Sau khi write — CHẠY NGAY validator
```bash
ba-kit validate-index --index-key backbone_index --slug {slug} --date {date} --writeback
```

### 6. Pre-Validation Self-Audit (BẮT BUỘC trước khi chạy validator)

Trước khi chạy `ba-kit validate-index`, PHẢI tự kiểm tra:

- [ ] Mọi Trace ID trong index dùng đúng prefix được phép: BG, ACT, PORTAL, F, MOD, FR, NFR, EP, R, SCR, MEM, A{N}
- [ ] FR IDs trong backbone.md dùng định dạng **zero-padded thống nhất**: `FR-01, FR-02` (KHÔNG `FR-1, FR-2`)
- [ ] R IDs dùng định dạng `R-` prefix có dấu gạch ngang: `R-1, R-2` (KHÔNG `R1, R2`)
- [ ] Mọi Trace ID trong index tồn tại dưới dạng **CHÍNH XÁC chuỗi ký tự** trong backbone.md (không suy đoán, không viết tắt)
- [ ] KHÔNG có ID ngoài allowed families trong Trace IDs (không `D1-D8`, `OQ-BB-01`, `DESIGN`, `NEXT`, `FRD`, `STORIES`, `SRS`, `PACKAGE`)
- [ ] Mỗi dòng index có ít nhất 1 Trace ID hợp lệ (KHÔNG dùng `—` thay thế)
- [ ] `source_hash` đã được tính lại từ backbone.md **hiện tại** (SHA256 thật, không placeholder)

Nếu phát hiện vi phạm → sửa backbone.md và/hoặc index TRƯỚC KHI chạy validator. Không dùng validator như công cụ khám phá lỗi.
