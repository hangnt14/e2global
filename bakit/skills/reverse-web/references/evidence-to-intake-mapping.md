# Evidence → Intake Template Mapping

This file guides the session AI during synthesis.
Read this AFTER `evidence/evidence-index.md` and BEFORE filling sections.

## Section Mapping Table

| Evidence source | Intake section (Vietnamese) | What to extract | Confidence guidance |
|----------------|----------------------------|-----------------|---------------------|
| `manifest.json` | **Thông tin dự án** | URL, crawl date, pages visited, config | High — factual metadata |
| Screenshots (vision) + `dom/*.json` headings | **Bối cảnh kinh doanh → Vấn đề cần giải quyết** | What problem the site solves, target audience, business domain | Medium — inferred from UI |
| Screenshots + headings + meta description | **Bối cảnh kinh doanh → Mục tiêu kinh doanh** | Business goals visible from site (e.g. "increase sales", "manage projects") | Medium — inferred |
| `dom/*.json` nav items + page titles | **Bối cảnh kinh doanh → Các bên liên quan** | User roles visible (admin, customer, guest, member) | Medium — inferred from nav/auth patterns |
| `dom/*.json` forms + buttons + links | **Yêu cầu thô** | Every observable user action: form submissions, button clicks, navigation flows | High — directly observed |
| `evidence-index.md` pages table + screenshots | **Màn hình và giao diện** | Screen inventory: one row per unique URL | High — directly observed |
| `sitemap.json` edges + `dom/*.json` nav | **Quy trình và luồng** | Multi-step flows: login→dashboard, checkout→confirm, etc. | High — directly observed |
| `network.ndjson` + `dom/*.json` | **Ràng buộc và giả định** | Tech stack clues, API patterns, external services, browser requirements | Medium — inferred |
| `network.ndjson` auth patterns + cookie headers | **Tuân thủ và quy định** | Auth mechanisms, session handling, cookie consent, data collection | Medium — inferred |
| (gaps in evidence) | **Câu hỏi mở** | What CANNOT be determined from external observation | High — explicit gaps |
| (crawl metadata + confidence notes) | **Ghi chú phân tích** | Crawl limitations, low-confidence inferences, pages not captured | High — factual |

---

## Section-by-Section Guidance

### 1. Thông tin dự án (Project Information)

Fill the table from `manifest.json`:
- **Tên dự án**: derive from URL hostname (e.g. `example.com` → "Example")
- **Ngày**: use `manifest.json` → `timestamp` field (ISO → DD/MM/YYYY)
- **Người yêu cầu**: leave blank (unknown from external crawl)
- **Tài liệu gốc**: `evidence/manifest.json` + crawl URL

### 2. Bối cảnh kinh doanh (Business Context)

**Vấn đề cần giải quyết:**
- Look at: homepage screenshot, meta description, hero section headings
- Ask: "What pain point does this site address?"
- Example: "Quản lý dự án cho nhóm nhỏ" or "Bán hàng trực tuyến"

**Mục tiêu kinh doanh:**
- Look at: CTA buttons, pricing pages, signup flows
- Ask: "What does the business want users to do?"
- Example: "Tăng đăng ký tài khoản", "Tăng doanh thu qua checkout"

**Các bên liên quan:**
- Look at: login page (role selection), nav items (Admin, User, Guest)
- Common patterns: `admin`, `user`, `customer`, `member`, `guest`, `moderator`
- Fill table with inferred roles + "Ghi chú: inferred from UI"

### 3. Yêu cầu thô (Raw Requirements)

List EVERY observable user action as a numbered requirement.
Use verbatim DOM text where possible (button labels, form titles).

Format: `{N}. [Actor] có thể [action] thông qua [screen/form]`

Examples:
- `1. Người dùng có thể đăng nhập thông qua form /login (email + password)`
- `2. Người dùng có thể tìm kiếm sản phẩm thông qua search bar trên homepage`
- `3. Admin có thể xem danh sách đơn hàng tại /admin/orders`

Sources: all `dom/*.json` → forms (action + inputs), buttons (text), links (text + href)

### 4. Màn hình và giao diện (Screens and UI)

One row per unique URL from `evidence-index.md` pages table.

| Màn hình / Thành phần | Mô tả | Ghi chú |
|----------------------|-------|---------|
| Homepage (/) | Landing page with hero, features, CTA | Depth 0 |
| Login (/login) | Email + password form, forgot password link | Has form |

- **Mô tả**: combine screenshot observation + DOM headings + meta description
- **Ghi chú**: note depth, has-form, has-table flags from index

### 5. Quy trình và luồng (Processes and Workflows)

Identify multi-step flows from `sitemap.json` edges.

Look for patterns:
- Auth flow: `/` → `/login` → `/dashboard`
- Checkout: `/products` → `/cart` → `/checkout` → `/confirmation`
- Onboarding: `/signup` → `/verify-email` → `/setup` → `/dashboard`

Format each flow as a table row with description.

### 6. Ràng buộc và giả định (Constraints and Assumptions)

**Ràng buộc (Constraints):**
- From `network.ndjson`: external API domains observed (e.g. Stripe, Google Analytics)
- From DOM: browser-specific features (e.g. File API, WebSocket)
- From screenshots: mobile/desktop layout clues

**Giả định (Assumptions):**
- "Hệ thống yêu cầu đăng nhập để truy cập các trang /dashboard/*"
- "API backend tại /api/* — chi tiết nội bộ không quan sát được"
- "Dữ liệu người dùng được lưu server-side (không thấy localStorage)"

### 7. Tuân thủ và quy định (Compliance)

Look for:
- Cookie consent banners (GDPR/PDPA signal)
- Login/auth patterns (session vs JWT from network headers)
- Privacy policy / terms links
- Payment forms (PCI DSS signal if Stripe/PayPal observed)
- Age verification

If nothing observed: "Không quan sát được yêu cầu tuân thủ cụ thể từ bên ngoài."

### 8. Câu hỏi mở (Open Questions)

ALWAYS include these standard gaps for external-only observation:

1. Business rules behind validation (what makes a form submission valid?)
2. Backend workflow logic (what happens after form submit?)
3. User permission model (what can each role actually do?)
4. Data retention and privacy policies
5. Integration details (what do the observed external APIs actually do?)
6. Error handling flows (what happens on failure?)
7. Any pages not captured (login-gated, depth > max, robots-blocked)

Add site-specific gaps discovered during synthesis.

### 9. Ghi chú phân tích (Parsing Notes)

Always include:
- Crawl stats: pages captured, max depth, date
- Pages NOT captured (login-gated, robots-blocked, depth exceeded)
- Low-confidence inferences (mark with "⚠ inferred")
- Screenshot quality issues (if any pages timed out or had loading errors)
- Evidence freshness (timestamp from manifest)
