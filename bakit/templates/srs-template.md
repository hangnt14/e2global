# Đặc tả yêu cầu phần mềm (Software Requirements Specification)

> **Tài liệu tổng hợp:** Bản SRS này được compile tự động từ các file nguồn chuẩn. Không chỉnh sửa trực tiếp. Nguồn: `srs/spec.md`, `userstories/us-*.md`, `usecases/uc-*.md`, `ascii-screen/*.md`, `srs/flows.md`, `srs/states.md`, `srs/erd.md`.

## Tóm tắt dành cho BA và stakeholder

**Dự án (Project):** [Tên dự án]
**Module:** [Tên module]
**Ngày compile (Compiled):** [YYYY-MM-DD]

## Mục đích và phạm vi (Purpose and Scope)

[Mục đích và phạm vi của module — điền từ backbone]

## Yêu cầu chức năng (Functional Requirements)

| Mã (ID) | Yêu cầu (Requirement) | Ưu tiên (Priority) | Nguồn (Source) |
| --- | --- | --- | --- |
| FR-{module}-001 | [Yêu cầu] | [Must/Should/Could] | [Nguồn] |

## User Stories

Danh sách user story được compile từ `userstories/us-*.md`.

| Mã US | Tiêu đề | Vai trò | Tính năng | Lợi ích | Ưu tiên | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| US-001 | [Tiêu đề] | [Vai trò] | [Tính năng] | [Lợi ích] | [P0/P1/P2] | [draft] |

## Đặc tả Use Case (Use Case Specifications)

Mô tả các tương tác chính của hệ thống. Mỗi use case được compile từ `usecases/uc-*.md`.

| Mã UC | Tên UC | Tác nhân chính | Trigger | Điều kiện tiên quyết | Hậu điều kiện |
| --- | --- | --- | --- | --- | --- |
| UC-{module}-{slug} | [Tên] | [Tác nhân] | [Trigger] | [ĐK] | [HK] |

## Mô tả màn hình (Screen Descriptions)

Mô tả chi tiết từng màn hình được compile từ `ascii-screen/*.md`. Mỗi màn hình bao gồm: fields, actions, control states, message placement, và ASCII wireframe.

## Yêu cầu phi chức năng (Non-Functional Requirements)

| Mã (ID) | Danh mục (Category) | Yêu cầu (Requirement) | Mục tiêu (Target) |
| --- | --- | --- | --- |
| NFR-{module}-001 | [Hiệu năng/Bảo mật/Usability] | [Yêu cầu] | [Mục tiêu] |

## Tham chiếu quy tắc/thông điệp dùng chung

Các rule và message dùng chung được compile từ backbone. Module artifact tham chiếu bằng code (`CR-*`, `MSG-*`).

### Common Rules (từ `02_backbone/common-rules.md`)

| Code | Type | Rule Statement | Applies To | Edge Cases |
| --- | --- | --- | --- | --- |
| CR-VAL-01 | VAL | [Quy tắc] | [Phạm vi] | [Edge case] |

### Message List (từ `02_backbone/message-list.md`)

| Code | Type | Canonical Text | Surface | Applies To |
| --- | --- | --- | --- | --- |
| MSG-ERR-01 | ERR | [Nội dung] | [inline/toast/banner] | [Phạm vi] |

### Control Type Library (từ `02_backbone/control-type-library.md`)

Các control type dùng trong module. Xem file đầy đủ để biết default behaviour và edge cases.

| Control Type | Mô tả | Interactive |
| --- | --- | --- |
| `text_input` | Text Input | Yes |
| `button` | Button (primary/secondary/danger/ghost/icon) | Yes |

## Sơ đồ luồng dữ liệu (Data Flow Diagrams)

Được compile từ `srs/flows.md`.

## Sơ đồ thực thể quan hệ (Entity Relationship Diagram)

Được compile từ `srs/erd.md`.
