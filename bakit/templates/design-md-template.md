# DESIGN.md - [Tên dự án]

## Metadata

- Project: [Tên dự án]
- Slug: [initiative-slug]
- Date: [YYMMDD-HHmm]
- Owner: [BA owner / approver]
- Reference direction: [Custom brief | Brand guide | External DESIGN.md inspiration]
- Status: [Draft | Approved]

## 0. Phạm vi áp dụng (Scope Of Use)

- Product / flow covered: [Phạm vi]
- App type: [web-app | mobile-app]
- Primary audience: [Người dùng chính]
- This file is the visual direction document for manual wireframe creation, ASCII rendering, and external design handoff in `designs/{slug}/`.
- Machine-readable portal, navigation, shell, and layout ownership belongs in `plans/{slug}-{date}/02_backbone/shared-shell-contract.md`.

## 1. Visual Theme & Atmosphere

- Mood keywords: [Ví dụ: operational, premium, calm, data-dense]
- Brand impression: [Mô tả]
- Density: [Compact | Balanced | Spacious]
- Visual priorities: [Ví dụ: clarity first, fast scanning, guided completion]

## 2. Information Architecture (Portals & Navigation)

### 2.1 Portal Summary

| Portal ID | Portal / App | Target Actor | Owned Screen Families / Route Groups | Notes |
| --- | --- | --- | --- | --- |
| [PORTAL-ADMIN] | [Tên portal, VD: Admin Portal] | [Role, VD: System Admin] | [Dashboard, Users, Settings] | [Portal sở hữu nhóm màn hình nào] |

- Global navigation pattern: [Sidebar | Top bar | Bottom tabs]
- Routing persistence: [Cách menu giữ trạng thái active / Hệ thống Breadcrumbs]

### 2.2 Navigation Schema

Phần này là schema bắt buộc để kiểm tra menu consistency giữa các screen trong cùng portal.
`Menu Item List` là danh sách active-menu path được phép dùng trong Screen Contract Plus. Với menu con, ghi theo dạng `Parent (Child A, Child B)` hoặc active path rõ ràng `Parent > Child`; SRS không được tự tạo path khác ngoài danh sách này.
Trong flow canon-first, phần này là visual/BA-facing snapshot. Contract máy đọc được phải được đồng bộ sang `shared-shell-contract.md`.

| Portal ID | Nav Schema ID | Navigation Pattern | Menu Item List | Default Landing | Active / Selected Rule | Breadcrumb / Back Rule | Hidden / Contextual Nav Exceptions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [PORTAL-ADMIN] | [NAV-ADMIN-01] | [Glass top bar / Sidebar / Bottom tabs] | [Dashboard, Users, Settings] | [Dashboard] | [Highlight item khớp route group hiện tại] | [Breadcrumbs hiển thị từ cấp 2 trở xuống] | [Modal xác nhận không render menu] |

## 3. Color Palette & Roles

| Role | Color | Usage | Notes |
| --- | --- | --- | --- |
| Primary background | [#HEX] | [Usage] | [Notes] |
| Primary text | [#HEX] | [Usage] | [Notes] |
| Accent / CTA | [#HEX] | [Usage] | [Notes] |
| Success | [#HEX] | [Usage] | [Notes] |
| Warning | [#HEX] | [Usage] | [Notes] |
| Error | [#HEX] | [Usage] | [Notes] |
| Border / Divider | [#HEX] | [Usage] | [Notes] |

## 4. Typography Rules

| Level | Font / Style | Size / Weight | Usage |
| --- | --- | --- | --- |
| Display | [Rule] | [Rule] | [Usage] |
| Heading | [Rule] | [Rule] | [Usage] |
| Body | [Rule] | [Rule] | [Usage] |
| Label | [Rule] | [Rule] | [Usage] |
| Mono / Data | [Rule] | [Rule] | [Usage] |

## 5. Component Stylings

- Button style: [Shape, emphasis, states]
- Input and form style: [Density, labels, validation]
- Table / list style: [Headers, row density, empty states]
- Card / panel style: [Borders, shadows, sections]
- Navigation style: [Sidebar, tabs, top bar, breadcrumbs]
- Feedback style: [Toast, inline error, banners, dialogs]
- Shared-navigation governance: [Module chỉ snapshot schema, không tự đổi global menu]

## 6. Layout Principles

- Grid and spacing philosophy: [Rule]
- Content width and breakpoints: [Rule]
- Section hierarchy: [Rule]
- Mobile / responsive priority: [Desktop-first | Mobile-first | Balanced]

## 7. Depth & Elevation

- Surface model: [Flat | Layered | Mixed]
- Border radius direction: [Rule]
- Shadow / border treatment: [Rule]
- Overlays and modal treatment: [Rule]

## 8. Do's and Don'ts

### Do

- [Approved pattern]
- [Approved pattern]

### Don't

- [Anti-pattern]
- [Anti-pattern]

## 9. Responsive Behavior

- Navigation collapse behavior: [Rule]
- Table/list adaptation: [Rule]
- Form adaptation: [Rule]
- Minimum touch/interaction targets: [Rule]

## 10. Thư viện UI / UI Library

> **Quan trọng:** Mục này là gate bắt buộc trước khi tạo `control-type-library.md`.
> Khi chạy backbone lần đầu, để `TBD`. Sau khi research và chốt thư viện, điền tên + phiên bản cụ thể rồi chạy lại backbone để tạo `control-type-library.md`.

| Trường | Giá trị |
|--------|---------|
| Thư viện UI | `TBD` |
| Phiên bản | `TBD` |
| Docs tham chiếu | `TBD` |
| Ghi chú | [Lý do chọn library này, trade-off, hoặc "none" nếu không dùng thư viện nào] |

**Trạng thái chốt:** [ ] Chưa chốt / [ ] Đã chốt

- Nếu Thư viện UI = `TBD` hoặc trống → backbone sẽ DỪNG ở gate 5.1a, chưa tạo `control-type-library.md`.
- Nếu Thư viện UI = `none` → gate passed, tạo control-type-library với baseline = `none`.
- Nếu Thư viện UI = tên library cụ thể (vd `Ant Design 5.x`) → gate passed, tạo control-type-library với pruning theo library.

## 11. Design Handoff Guide

- Use this file as the system design document before creating any manual wireframe or mockup for this project.
- Use the shared shell contract as the source for machine-readable portal, navigation, shell, layout, and active-menu validation.
- Follow the approved visual tone, color roles, typography rules, and component styling consistently across all frames.
- Strictly adhere to the Portals & Navigation architecture. Make sure global menus and sitemaps are present and consistent in all screens of their respective portals.
- Keep behavior aligned with use cases and Screen Contract Plus. Do not invent flows that are not documented.
- Every global navigation screen must show the correct active/selected state defined by the matching `Nav Schema ID`.
- If a screen intentionally hides global navigation, document the exception explicitly instead of silently omitting the menu.
- Use Shadcn UI as the fallback component baseline only when this file leaves a detail unspecified.
- When the final mockup is ready, the user must manually reference or insert it into the final SRS.
