# Synthesis Prompts

Internal guidance for each intake section during synthesis.
Read this alongside `evidence-to-intake-mapping.md`.

## General Principles

- **Observe, don't invent.** Only write what evidence supports. Mark inferences with "⚠ inferred".
- **Vietnamese output.** All section content in Vietnamese unless evidence is English-only.
- **Verbatim where possible.** Use actual button text, form labels, page titles from DOM.
- **Explicit gaps.** Better to list an open question than to guess a business rule.
- **One requirement per line.** Never bundle two behaviors into one requirement.

---

## Section Prompts

### Thông tin dự án

Extract from `manifest.json`:
```
Tên dự án: [hostname from url, title-cased]
Ngày: [timestamp → DD/MM/YYYY]
Người yêu cầu: [leave blank]
Tài liệu gốc: Crawl từ [url] — [pagesVisited] trang, [timestamp]
```

### Bối cảnh kinh doanh — Vấn đề cần giải quyết

Prompt yourself: "Nhìn vào trang chủ và các trang chính, hệ thống này giải quyết vấn đề gì cho ai?"

Look at:
1. Homepage hero heading (h1) — usually states the value proposition
2. Meta description — often a concise problem statement
3. Feature section headings — enumerate what problems are solved

Write 2-4 sentences. Start with: "Hệ thống [tên] giúp [đối tượng] [giải quyết vấn đề]..."

If unclear: "⚠ Mục đích chính của hệ thống chưa rõ từ quan sát bên ngoài. Xem Câu hỏi mở #1."

### Bối cảnh kinh doanh — Mục tiêu kinh doanh

Look for conversion signals:
- Signup/register CTAs → goal: user acquisition
- Pricing/upgrade pages → goal: revenue/conversion
- Dashboard/analytics → goal: retention/engagement
- Contact/demo forms → goal: lead generation

Write as measurable goals where possible:
- "Tăng số lượng đăng ký tài khoản mới"
- "Chuyển đổi người dùng free sang paid plan"

### Bối cảnh kinh doanh — Các bên liên quan

Identify actors from:
- Login page: role selection dropdowns, separate login URLs (/admin/login vs /login)
- Navigation: "Admin Panel", "My Account", "Dashboard"
- URL patterns: /admin/*, /user/*, /api/v1/users/*
- Form labels: "Tên khách hàng", "Mã nhân viên"

Table format:
```
| Tên / Vai trò | Mức quan tâm / Ảnh hưởng | Ghi chú |
| Người dùng cuối | Cao / Trực tiếp | Inferred từ /login, /dashboard |
| Admin | Cao / Trực tiếp | Inferred từ /admin/* URLs |
```

### Yêu cầu thô

For EACH form found in `evidence-index.md` → Forms Detected:
```
[N]. [Actor] có thể [form action verb] thông qua form [page URL]
     Fields: [field1 (type)], [field2 (type, required)], ...
```

For EACH significant button/link group:
```
[N]. [Actor] có thể [button text action] tại [page URL]
```

For EACH API endpoint in `evidence-index.md` → API Endpoints:
```
[N]. Hệ thống hỗ trợ [METHOD] [URL pattern] — [inferred purpose from URL]
```

Order: authentication flows first, then core features, then admin/secondary.

### Màn hình và giao diện

For EACH page in `evidence-index.md` → Pages table:
```
| [Page title or URL] | [1-sentence description from screenshot + DOM] | [depth, has-form, has-table] |
```

Description formula: "[Page purpose] — [key elements visible]"
Examples:
- "Trang đăng nhập — form email/password, link quên mật khẩu, nút đăng nhập"
- "Dashboard chính — bảng thống kê, menu điều hướng, danh sách gần đây"

### Quy trình và luồng

From `sitemap.json` edges, identify chains:

Step 1: Group edges by starting point
Step 2: Find chains (A→B→C) by following edges
Step 3: Name each chain by its purpose

Format:
```
| Quy trình / Luồng | Mô tả | Ghi chú |
| Đăng nhập | / → /login → /dashboard | 3 bước |
| Thanh toán | /products → /cart → /checkout → /confirm | 4 bước |
```

If edges are sparse (few links captured): "⚠ Luồng đầy đủ chưa xác định — cần crawl sâu hơn hoặc đăng nhập."

### Ràng buộc và giả định

**Constraints** — write only what evidence directly supports:
- External services from `network.ndjson` URLs (stripe.com, googleapis.com, etc.)
- Auth requirement: "Các trang /dashboard/* yêu cầu đăng nhập (redirect về /login)"
- Browser features: "Sử dụng JavaScript (SPA — React/Vue/Angular detected from DOM)"

**Assumptions** — mark all with "⚠ giả định":
- "⚠ Backend API tại /api/* — chi tiết không quan sát được từ bên ngoài"
- "⚠ Dữ liệu người dùng lưu server-side"
- "⚠ Validation logic phía server không quan sát được"

### Tuân thủ và quy định

Signals to look for:
- Cookie banner in screenshots → GDPR/PDPA
- `/privacy`, `/terms`, `/cookie-policy` in sitemap → data governance
- Stripe/PayPal in network → PCI DSS scope
- `/verify-email`, `/2fa` in sitemap → security compliance
- Age gate in screenshots → content regulation

If no signals: "Không quan sát được yêu cầu tuân thủ cụ thể. Cần xác nhận với stakeholder."

### Câu hỏi mở

Always include these 6 standard gaps:
```
1. Business rules: Điều kiện validation phía server cho các form là gì?
2. Post-submit workflow: Hệ thống xử lý gì sau khi form được submit?
3. Permission model: Quyền hạn chi tiết của từng role là gì?
4. Data model: Cấu trúc dữ liệu đằng sau các màn hình là gì?
5. Error handling: Các luồng lỗi và thông báo lỗi là gì?
6. Gated content: Các trang yêu cầu đăng nhập có nội dung gì?
```

Add site-specific gaps:
- Any URL patterns that returned 403/404 during crawl
- Any forms where action URL was unclear
- Any navigation items that led outside the crawled domain

### Ghi chú phân tích

Always include:
```
- Nguồn: Crawl tự động từ [url] lúc [timestamp]
- Phạm vi: [pagesVisited] trang, depth tối đa [maxDepth], [screenshotCount] screenshots
- Trang không capture được: [list robots-blocked or depth-exceeded URLs if known]
- Trang login-gated: Các trang yêu cầu xác thực không được crawl
- Độ tin cậy: Thông tin nghiệp vụ (⚠ inferred) cần xác nhận với stakeholder
- Công cụ: BA-kit reverse-web v1.0, Playwright chromium
```
