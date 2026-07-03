---
type: screen
module: "{module_slug}"
screen_id: "SCR-{NN}"
slug: "{screen-slug}"
portal_id: "{PORTAL-ID}"
nav_schema_id: "{NAV-SCHEMA-ID}"
expected_active_menu: "{menu item}"
actor: "{actor}"
ascii_status: pending
status: draft
linked_usecases: []
linked_stories: []
source_backbone_ids: []
created: "{YYYY-MM-DD}"
owner: "{@handle}"
changelog:
  - {YYYY-MM-DD} | /srs | initial draft
---

# SCR-{NN}: {screen title}

## Overview

| Field | Value |
|---|---|
| Portal ID | {PORTAL-ID} |
| Nav Schema ID | {NAV-SCHEMA-ID} |
| Expected Active Menu Item | {menu item} |
| Navigation Region Visible | Yes / No |
| Entry Conditions | {condition} |
| Exit Conditions | {condition} |
| Actor | {actor} |
| Linked Use Cases | UC-{module}-{slug} |
| Linked Stories | US-{module}-{NNN} |

## Fields

| Field ID | Field Name | Control Type | Display Rules | Behaviour Rules | Validation Rules |
|---|---|---|---|---|---|
| SCR-{NN}-F01 | {field} | `{control_type_id}` | {label, placeholder, visibility, default, read-only} | (default) | {CR-VAL-NN -> MSG-ERR-NN inline} |
| SCR-{NN}-F02 | {field} | `button (primary)` | Label: "{label}" | (default) | — |

### Behaviour Rules — Kế thừa & Override

| Cách ghi | Ý nghĩa |
|----------|---------|
| `(default)` | Kế thừa toàn bộ behaviour từ Control Type Library (`02_backbone/control-type-library.md`) |
| `(default), thêm: {mô tả}` | Kế thừa + bổ sung edge case |
| `**Khác default:** {mô tả}` | Override hoàn toàn, không kế thừa |

Khi ghi `(default)`, behaviour mặc định được áp dụng tự động:
- Điều kiện disabled/active của button, điều kiện hiển thị của field
- Số lần ấn tối đa (1 lần cho button, không giới hạn cho checkbox)
- Cách hiển thị lỗi validation (inline dưới field, toast góc dưới)
- Hành vi focus/blur, mở/đóng dropdown, pagination threshold

### Behaviour Rules Naming Sheet

Dùng từ chuẩn từ Terminology (`02_backbone/control-type-library.md`):

| Pattern | Correct (Business) | Wrong (Technical) |
|---|---|---|
| Navigate to screen | ấn -> mở SCR-LRN-12 (My Learning) | Click -> redirect /learn |
| Open overlay | ấn -> mở modal SCR-FORGOT-PW | Click -> showModal('forgot') |
| Close overlay | ấn ngoài modal -> đóng, quay về màn cha | Click -> close() |
| Submit form | ấn -> kiểm tra -> xác thực -> đúng: mở SCR-XXX, sai: toast MSG-ERR-01 | Click -> POST /api/auth |
| Show message | Sau khi gửi -> toast xanh MSG-SUC-01 "Đã gửi link reset" | showSuccessToast() |
| Toggle state | ấn -> bật/tắt field Y, hiện section Z | setDisabled(false) |
| Inherit default | (default) — kế thừa từ Control Type Library | (để trống — LLM tự nghĩ ra behaviour) |

## Actions

| Action ID | Label | Control | Trigger | Outcome |
|---|---|---|---|---|
| ACT-{NN}-01 | {action label} | {button/link/icon} | {user gesture} | {system response or navigation} |

## Control States

> Bắt buộc với mọi interactive control (button, toggle, dropdown, ...).

| Control | State | Condition |
|---------|-------|-----------|
| {button/field name} | disabled | {khi nào} |
| {button/field name} | active | {khi nào} |
| {button/field name} | loading | {khi nào} |

## Validation Rules

- {CR-VAL-NN}: {rule description}

## Message Placement

> Bắt buộc nếu màn hình có ít nhất 1 MSG-* được reference.

| Message Code | Surface | Trigger Condition | Position | Dismiss |
|---|---|---|---|---|
| MSG-ERR-01 | inline | {khi nào} | Dưới field {field_name} | — |
| MSG-ERR-02 | toast | {khi nào} | Góc phải dưới | Tự tắt sau 5s |
| MSG-SUC-01 | toast | {khi nào} | Góc phải dưới | Tự tắt sau 3s |
| MSG-WRN-01 | banner | {khi nào} | Trên cùng màn hình | User ấn X |

### Surface enum

| Surface | Position format | Ví dụ |
|--------|----------------|-------|
| `inline` | "Dưới field {field_name}" / "Trên field {field_name}" | Dưới field Email |
| `toast` | "Góc phải dưới" / "Góc phải trên" / "Giữa trên" / "Góc trái dưới" | Góc phải dưới |
| `banner` | "Trên cùng màn hình" / "Dưới cùng màn hình" | Trên cùng màn hình |
| `modal` | "Giữa màn hình" | Giữa màn hình |

### Dismiss format

| Dismiss | Ý nghĩa |
|--------|---------|
| `—` | Không áp dụng (inline message tự hiện/mất theo validation) |
| `Tự tắt sau Ns` | Tự động biến mất sau N giây |
| `User ấn X` | User phải ấn nút đóng |
| `User ấn nút hành động` | User phải ấn nút hành động cụ thể |
| `Không tắt đến khi {condition}` | Chỉ tắt khi điều kiện được đáp ứng |

## States

| State ID | Name | Description |
|---|---|---|
| {SCR-NN-DEFAULT} | Default | {description} |
| {SCR-NN-EMPTY} | Empty | {description} |
| {SCR-NN-ERROR} | Error | {description} |

## ASCII Wireframe

### Quy ước marker vị trí message

- **Inline:** marker `▼ MSG-ERR-XX` ngay dưới field bị lỗi
- **Toast:** vẽ zone toast góc màn hình
- **Banner:** vẽ banner bar trên/dưới cùng
- **Message Zones legend:** bắt buộc ghi chú bên dưới mỗi wireframe

### Default State

```
+--------------------------------------------------+
| {Screen Title}                                   |
+--------------------------------------------------+
| {field label}: [________________]                |
|                                                  |
| [{Action Button}]                                |
+--------------------------------------------------+

Message Zones: (none in default state)
```

### Empty State

```
+--------------------------------------------------+
| {Screen Title}                                   |
+--------------------------------------------------+
| (Chưa có dữ liệu)                                |
| [{Call to Action}]                               |
+--------------------------------------------------+

Message Zones: (none in empty state)
```

### Error State

```
+--------------------------------------------------+
| {Screen Title}                                   |
+--------------------------------------------------+
| {field label}: [abc@xyz]                         |
| ▼ MSG-ERR-01: {error message}                    |
| [{Action Button}]                                |
+--------------------------------------------------+

Message Zones:
  Inline: dưới field {field_name} (MSG-ERR-01)
```

### State với toast (ví dụ)

```
+--------------------------------------------------+
| {Screen Title}                                   |
+--------------------------------------------------+
| ...nội dung màn hình...                          |
|                                                  |
|              ┌──────────────────┐                |
|              │ ✓ MSG-SUC-01     │                |
|              └──────────────────┘                |
+--------------------------------------------------+

Message Zones:
  Toast area: góc phải dưới (MSG-SUC-01: tự tắt sau 3s)
```

### State với banner (ví dụ)

```
+--------------------------------------------------+
| ┌──────────────────────────────────────────────┐ |
| │ ⚠ MSG-WRN-01: {warning message}          ✕  │ |
| └──────────────────────────────────────────────┘ |
| {Screen Title}                                   |
+--------------------------------------------------+
| ...nội dung màn hình...                          |
+--------------------------------------------------+

Message Zones:
  Banner area: trên cùng màn hình (MSG-WRN-01: user ấn X để đóng)
```

## Overlay Context (if applicable — modal, drawer, dialog)

| Field | Value |
|---|---|
| Parent Screen | SCR-{NN} |
| Render Mode | modal / drawer / dialog |
| Backdrop Behavior | ấn ra ngoài -> đóng, quay về SCR-{NN} (không lưu thay đổi) |

### Close Triggers

| Trigger | Outcome | Lưu thay đổi? |
|---|---|---|
| ấn nút X (góc phải trên) | Đóng, quay về SCR-{NN} | Không |
| ấn ra ngoài (backdrop) | Đóng, quay về SCR-{NN} | Không |
| ấn phím Esc | Đóng, quay về SCR-{NN} | Không |
| ấn nút "Hủy" | Đóng, quay về SCR-{NN} | Không |
| Submit thành công (ACT-{NN}-01) | Đóng, mở SCR-{NN+1} | Có |

### Success / Error Return

| Outcome | Behavior |
|---|---|
| Success | {đóng -> mở SCR-XXX, toast MSG-SUC-XX} |
| Error | {giữ nguyên popup, hiện lỗi} |
