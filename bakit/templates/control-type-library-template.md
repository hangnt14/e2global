# Control Type Library — {project_name}

> Single source of truth cho mọi UI control type + default behaviour.
> Mỗi screen canon kế thừa default behaviour từ đây. Chỉ mô tả thêm khi KHÁC default.
> File này nằm trong `02_backbone/`, do Lead BA sở hữu.
>
> **Hai chế độ hoạt động:** xem mục [Baseline](#baseline).
> - Baseline = `none`: file này là **source of truth đầy đủ**.
> - Baseline = tên thư viện: file này là **deviation log**, chỉ ghi behaviour khác library default.
> - Lead BA chốt baseline trong backbone Step 5.1, sau khi DESIGN.md đã có library. Module BA không sửa file này.

## Cách sử dụng

Trong screen canon (`ascii-screen/*.md`), cột Behaviour Rules:

| Cách ghi | Ý nghĩa |
|----------|---------|
| `(default)` | Kế thừa toàn bộ behaviour từ file này |
| `(default), thêm: {mô tả}` | Kế thừa + bổ sung edge case |
| `**Khác default:** {mô tả}` | Override hoàn toàn |

---

## Baseline

Trong backbone Step 5.1, sau khi `DESIGN.md` đã chốt thư viện UI, Lead BA điền bảng dưới:

| Trường | Giá trị |
|--------|---------|
| Thư viện UI | `none` |
| Phiên bản | — |
| Docs tham chiếu | — |

**Quy tắc theo baseline:**

| Baseline | Ý nghĩa | Cách dùng file này |
|----------|---------|-------------------|
| `none` | Không dùng thư viện UI. | 20 control type bên dưới là **source of truth đầy đủ**. Mọi behaviour mặc định mô tả tại đây. |
| `{tên thư viện}` (vd: Shadcn UI) | Có dùng thư viện UI. | 20 control type bên dưới CHỈ ghi **deviation** (khác biệt so với library default). Behaviour không có trong file này → ngầm hiểu theo library docs. |

**Đối với Lead BA, trong backbone Step 5.1:**

1. Đọc `DESIGN.md` → xác định thư viện UI (nếu có).
2. Cập nhật bảng Baseline ở trên: điền tên thư viện, phiên bản, link docs.
3. Nếu baseline là thư viện:
   - Xóa các behaviour trùng với library default khỏi từng control type (giữ lại cấu trúc section, chỉ xóa dòng behaviour).
   - Chỉ giữ lại các behaviour **khác** library default.
   - Ví dụ: nếu Shadcn button đã có `disabled` state → không cần mô tả lại trong file này.
4. Nếu baseline là `none`:
   - Giữ nguyên toàn bộ 20 control type.
   - Điều chỉnh behaviour theo đặc thù dự án nếu cần.
5. Khi thư viện nâng cấp (version bump): review từng deviation, cập nhật nếu library đã thay đổi.

---

## Terminology (chuẩn toàn dự án)

### Hành động người dùng

| Từ chuẩn | Từ cấm |
|----------|--------|
| ấn | bấm, nhấn, nhấp, click, tap |
| chọn | select, pick, lựa |
| điền | nhập, gõ, type, enter |
| kéo | drag, kéo thả |
| vuốt | swipe, scroll (mobile gesture) |
| giữ | hold, long-press |

### Điều hướng

| Từ chuẩn | Từ cấm |
|----------|--------|
| mở | open, navigate to, redirect, chuyển đến, đến, vào |
| đóng | close, dismiss, tắt (màn hình/popup) |
| quay về | go back, return, back |

### Hiển thị

| Từ chuẩn | Từ cấm |
|----------|--------|
| hiện | show, display, xuất hiện, render |
| ẩn | hide, disappear, vanish |
| bật | on, enable, activate |
| tắt | off, disable, deactivate |

### Xử lý dữ liệu

| Từ chuẩn | Từ cấm |
|----------|--------|
| lưu | save, persist, store |
| xóa | delete, remove, clear, destroy |
| kiểm tra | validate, check, verify |
| xác thực | authenticate, verify, auth |
| tìm | search, query, filter |
| tải lên | upload |
| tải xuống | download |
| gửi | send, submit, dispatch |
| hủy | cancel, abort, discard |

---

## Control Types

### 1. Text Input (`text_input`)

**Mô tả:** Ô điền text 1 dòng.

**Default Display:**
- Label trên, placeholder trong ô

**Default Behaviour:**
- Ấn vào ô → viền sáng (focus)
- Rời khỏi ô → tự động kiểm tra, hiện lỗi inline dưới field nếu có
- Khi nhiều lỗi → xét lỗi theo thứ tự FE trước (field gần đầu form báo trước)
- Icon bên trái hiển thị khi field có chức năng tìm kiếm; icon bên phải hiển thị khi field hỗ trợ hiện/ẩn mật khẩu hoặc xóa nội dung

**Default States:**
| State | Hiển thị | Điều kiện |
|-------|---------|-----------|
| default | Viền xám, trống | Chưa tương tác |
| focused | Viền xanh, con trỏ nhấp nháy | Đang điền |
| filled | Viền xám, có text | Đã điền, rời focus |
| disabled | Mờ, không ấn được | Không đủ quyền / chờ điều kiện |
| error | Viền đỏ + inline message dưới ô | Kiểm tra thất bại |
| read-only | Không viền, text hiển thị như label | Chỉ xem |

**Edge Case cần mô tả thêm:**
- Format đặc biệt (số điện thoại, mã số thuế, số tài khoản)
- Có auto-complete/suggest
- Giới hạn ký tự đặc biệt (chỉ số, không dấu, không khoảng trắng)
- Prefix/suffix cố định (vd: "VNĐ", "kg")

---

### 2. Text Area (`textarea`)

**Mô tả:** Ô điền text nhiều dòng.

Kế thừa toàn bộ từ `text_input`.

**Khác biệt:**
- Nhiều dòng, resize dọc (mặc định)
- Hiện đếm ký tự bên dưới khi có giới hạn ký tự

**Edge Case cần mô tả thêm:**
- Giới hạn ký tự cụ thể (vd: tối đa 500 ký tự)
- Không cho phép resize
- Toolbar rich text (xem `rich_text_editor`)

---

### 3. Button (`button`)

**Mô tả:** Nút để thực hiện hành động.

**Sub-types:**

| Variant | Dùng cho |
|---------|---------|
| primary | Hành động chính (Lưu, Gửi, Xác nhận, Đăng nhập) |
| secondary | Hành động phụ (Hủy, Quay lại) |
| danger | Hành động phá hủy (Xóa, Xác nhận xóa) |
| ghost | Hành động không nổi bật (Chỉnh sửa, Xem chi tiết) |
| icon | Chỉ có icon (X đóng, bánh răng cài đặt) |

**Default Behaviour:**
- **Ấn 1 lần duy nhất** → disable ngay sau khi ấn (chống double-click)
- Nếu hành động cần thời gian chờ → hiện loading state
- Thành công → thực hiện outcome (mở màn, toast, đóng popup...)
- Thất bại → hiện lỗi dạng toast, button trở về active
- Với button trong form: lỗi hiển thị inline dưới field tương ứng, không dùng toast

**Default States:**
| State | Hiển thị | Điều kiện |
|-------|---------|-----------|
| active | Màu variant, ấn được | Đủ điều kiện để ấn |
| disabled | Mờ, không ấn được | Thiếu điều kiện (form chưa điền đủ, thiếu quyền) |
| loading | Spinner + text "Đang xử lý...", không ấn được | Đang chờ kết quả |
| hidden | Ẩn hoàn toàn | Không áp dụng trong context hiện tại |

**Default disabled condition cho button (primary) của form:**
- Mọi field required chưa điền → disabled
- Có field đang báo lỗi kiểm tra → disabled
- Tất cả required đã điền + không có lỗi → active

**Edge Case cần mô tả thêm:**
- Button ấn được nhiều lần (vd: nút "+" thêm dòng, nút tăng/giảm số lượng)
- Button không có loading state (hành động tức thời)
- Button disabled với điều kiện đặc biệt (vd: chỉ active trong giờ hành chính)
- Button có confirm step (vd: ấn "Xóa" → hiện popup "Bạn có chắc?")
- Button dạng link (điều hướng không có hành động)

---

### 4. Dropdown / Select (`dropdown`)

**Mô tả:** Danh sách thả xuống để chọn 1 giá trị.

**Default Display:**
- Label trên, placeholder "Chọn..." trong ô
- Mũi tên xuống bên phải

**Default Behaviour:**
- Ấn vào → mở danh sách option xuống dưới
- Ấn 1 option → đóng danh sách, hiển thị giá trị đã chọn
- Ấn ra ngoài → đóng danh sách, giữ giá trị cũ
- Gõ phím → nhảy tới option bắt đầu bằng ký tự đó

**Default States:**
| State | Hiển thị |
|-------|---------|
| default | Placeholder "Chọn..." |
| open | Danh sách option hiện xuống |
| selected | Giá trị đã chọn hiển thị |
| disabled | Mờ, không ấn được |
| error | Viền đỏ, inline message |

**Edge Case cần mô tả thêm:**
- Dropdown có search (gõ để lọc option)
- Multi-select (chọn nhiều option)
- Dropdown load data từ danh sách động
- Dropdown có phân cấp (Tỉnh → Huyện → Xã)
- Option có group/divider

---

### 5. Checkbox (`checkbox`)

**Mô tả:** Ô vuông tích/bỏ tích.

**Default Display:**
- Ô vuông + label bên phải
- Đứng 1 mình hoặc trong group

**Default Behaviour:**
- Ấn → toggle trạng thái (tích/bỏ tích)
- Trong group: mỗi checkbox độc lập, không ảnh hưởng lẫn nhau

**Default States:**
| State | Hiển thị |
|-------|---------|
| unchecked | Ô trống |
| checked | Ô có dấu ✓ |
| indeterminate | Ô có dấu — (chọn tất cả khi chỉ 1 phần được chọn) |
| disabled | Mờ, không ấn được |

**Edge Case cần mô tả thêm:**
- Checkbox "Chọn tất cả" (parent-child: chọn/bỏ chọn tất cả child)
- Số lượng tối thiểu/tối đa được chọn trong group
- Checkbox có điều kiện disable từng option riêng

---

### 6. Radio Button (`radio`)

**Mô tả:** Nút tròn chọn 1 trong nhiều.

**Default Display:**
- Nút tròn + label bên phải
- Luôn trong group (≥ 2 options)

**Default Behaviour:**
- Ấn 1 option → chọn option đó, bỏ chọn option khác trong group
- Luôn có 1 option được chọn mặc định (không thể bỏ chọn tất cả)

**Default States:**
| State | Hiển thị |
|-------|---------|
| unselected | Nút tròn rỗng |
| selected | Nút tròn có chấm giữa |
| disabled | Mờ, không ấn được |

**Edge Case cần mô tả thêm:**
- Radio KHÔNG có default selection (cho phép bỏ trống tất cả)
- Radio option thay đổi nội dung/hiển thị form bên dưới
- Radio hiển thị dạng button group (không phải nút tròn)

---

### 7. Date Picker (`date_picker`)

**Mô tả:** Ô chọn ngày với calendar popup.

**Default Display:**
- Label trên, placeholder "DD/MM/YYYY", icon lịch bên phải

**Default Behaviour:**
- Ấn vào ô hoặc icon → mở calendar popup
- Chọn ngày → đóng calendar, hiển thị ngày đã chọn
- Ấn ra ngoài → đóng calendar, giữ giá trị cũ
- Có thể điền tay (tự động format DD/MM/YYYY)

**Default States:**
| State | Hiển thị |
|-------|---------|
| default | Placeholder "DD/MM/YYYY" |
| open | Calendar popup hiển thị |
| selected | Ngày đã chọn hiển thị |
| disabled | Mờ, không ấn được |
| error | Viền đỏ, inline message |

**Edge Case cần mô tả thêm:**
- Giới hạn khoảng ngày (min/max date)
- Chọn khoảng ngày (range: từ ngày → đến ngày)
- Disable ngày cụ thể (Chủ nhật, ngày lễ)
- Chọn tháng/năm không cần ngày cụ thể

---

### 8. Toggle / Switch (`toggle`)

**Mô tả:** Công tắc bật/tắt.

**Default Display:**
- Label trái, switch phải

**Default Behaviour:**
- Ấn → bật/tắt ngay lập tức (không cần confirm)

**Default States:**
| State | Hiển thị |
|-------|---------|
| off | Switch trái, màu xám |
| on | Switch phải, màu xanh |
| disabled | Mờ, không ấn được |

**Edge Case cần mô tả thêm:**
- Toggle cần confirm trước khi đổi trạng thái
- Toggle thay đổi hiển thị form bên dưới
- Toggle có label thay đổi theo trạng thái (Bật/Tắt)

---

### 9. Table / Data Grid (`table`)

**Mô tả:** Bảng dữ liệu nhiều dòng, nhiều cột.

**Default Display:**
- Header row với tên cột, data rows bên dưới
- Có đường kẻ phân cách hàng
- Có checkbox chọn dòng khi có bulk action

**Default Behaviour:**
- Danh sách > 10 items → tự động hiện pagination
- Ấn header cột → sắp xếp tăng dần/giảm dần (nếu cột hỗ trợ sort)
- Ấn 1 dòng → mở chi tiết (màn tương ứng)
- Chọn dòng (checkbox) → hiện bulk action bar
- Mặc định 10 items / trang

**Default States:**
| State | Hiển thị |
|-------|---------|
| populated | Danh sách có dữ liệu |
| loading | Skeleton |
| empty | "Chưa có dữ liệu" + CTA khi có hành động phù hợp |
| error | "Không tải được dữ liệu" + nút thử lại |
| with-selection | Hiện bulk action bar khi ≥ 1 dòng được chọn |

**Edge Case cần mô tả thêm:**
- Table không có pagination (luôn < 10 dòng)
- Table có expandable row (ấn → mở chi tiết inline trong dòng)
- Table có drag & drop sắp xếp lại hàng
- Table có bộ lọc riêng cho từng cột
- Table có cột ẩn/hiện (column visibility toggle)
- Số items mỗi trang khác mặc định (20, 50)
- Cho phép user chọn số items/trang

---

### 10. File Upload (`file_upload`)

**Mô tả:** Khu vực tải file lên.

**Default Display:**
- Khu vực thả file (đường viền đứt) kèm nút "Tải lên"
- Định dạng hỗ trợ: PDF, JPG, PNG, DOCX

**Default Behaviour:**
- Ấn khu vực → mở file picker của hệ điều hành
- Kéo thả file vào → tự động tải lên
- Đang tải → hiện progress bar + tên file
- Tải xong → hiện tên file + kích thước + nút X để xóa
- Giới hạn mặc định: 1 file, tối đa 10MB

**Default States:**
| State | Hiển thị |
|-------|---------|
| default | Khu vực thả file trống |
| dragging | Viền sáng khi đang kéo file qua |
| uploading | Progress bar |
| done | Tên file + kích thước + nút X |
| error | "File quá lớn" / "Sai định dạng" |

**Edge Case cần mô tả thêm:**
- Upload nhiều file cùng lúc
- Dung lượng tối đa khác (20MB, 50MB)
- Định dạng đặc biệt (chỉ CSV, chỉ ảnh)
- Preview ảnh trước khi upload
- Upload folder (không chỉ file)

---

### 11. Search / Autocomplete (`search`)

**Mô tả:** Ô tìm kiếm có gợi ý.

**Default Display:**
- Input có icon kính lúp bên trái, placeholder "Tìm..."
- Kết quả hiện dưới dạng dropdown bên dưới

**Default Behaviour:**
- Gõ → sau 300ms → gọi tìm kiếm (debounce)
- Kết quả hiện dưới dạng dropdown
- Ấn kết quả → chọn, điền vào ô
- Ấn Enter → tìm với text hiện tại
- Ấn X trong ô → xóa text, đóng kết quả
- Ấn ra ngoài → đóng dropdown kết quả

**Default States:**
| State | Hiển thị |
|-------|---------|
| default | Placeholder "Tìm..." |
| focused | Đang gõ, chưa có kết quả |
| searching | Spinner nhỏ trong ô |
| results-shown | Dropdown kết quả hiện |
| no-results | "Không tìm thấy kết quả" |
| selected | Giá trị đã chọn hiển thị trong ô |

**Edge Case cần mô tả thêm:**
- Thời gian debounce khác (100ms, 500ms)
- Số kết quả tối đa hiển thị
- Tìm kiếm có phân trang kết quả
- Hiển thị kết quả theo category/group
- Tìm kiếm có lịch sử (recent searches)

---

### 12. Modal (`modal`)

**Mô tả:** Cửa sổ popup giữa màn hình, có backdrop.

**Default Display:**
- Chính giữa màn hình, backdrop mờ phía sau
- Có nút X góc phải trên
- Nút chính (Lưu/Xác nhận) + nút phụ (Hủy) hiển thị khi modal cần xác nhận hành động

**Default Behaviour:**
- Backdrop không cuộn được (scroll lock)
- Ấn X → đóng, quay về màn cha, không lưu
- Ấn ra ngoài (backdrop) → đóng, quay về màn cha, không lưu (giống X)
- Phím Esc → đóng, giống X
- Nút "Hủy" hiển thị khi modal có hành động hủy → giống X
- Nút chính (Lưu/Xác nhận) → kiểm tra → lưu → đóng → quay về màn cha hoặc mở màn tiếp theo

**Default States:**
| State | Hiển thị |
|-------|---------|
| open | Hiện giữa màn hình, backdrop mờ |
| closing | Biến mất dần (fade out) |

**Edge Case cần mô tả thêm:**
- Modal KHÔNG cho đóng khi ấn ra ngoài (bắt buộc chọn action)
- Modal có nhiều bước (wizard/stepper)
- Modal xác nhận xóa (danger variant, nút đỏ)
- Modal full màn hình (mobile)
- Modal không có nút X (chỉ đóng qua action button)

---

### 13. Drawer (`drawer`)

**Mô tả:** Panel trượt từ cạnh màn hình.

**Default Display:**
- Trượt từ phải sang, che 1 phần màn hình
- Có backdrop mờ phía sau
- Có nút X góc trên

**Default Behaviour:**
- Ấn X → đóng, trượt ngược lại, không lưu
- Ấn ra ngoài (backdrop) → giống X
- Hành vi nút chính/phụ giống Modal

**Default States:**
| State | Hiển thị |
|-------|---------|
| open | Panel hiện, backdrop mờ |
| closing | Trượt ngược lại |

**Edge Case cần mô tả thêm:**
- Drawer trượt từ trái / dưới lên / trên xuống
- Drawer full màn hình
- Drawer không có backdrop (nội dung bên dưới vẫn tương tác được)

---

### 14. Toast (`toast`)

**Mô tả:** Thông báo popup nhỏ, tự biến mất.

**Default Display:**
- Góc phải dưới màn hình
- Icon + text. Nút X hiển thị khi toast cho phép user tự đóng

**Default Behaviour:**
- Xuất hiện: fade in (0.3s) → hiển thị N giây → fade out (0.3s)
- Tự động biến mất:
  - Success (MSG-SUC-*): 3 giây
  - Error (MSG-ERR-*): 5 giây
  - Warning (MSG-WRN-*): 5 giây
  - Info (MSG-INF-*): 3 giây
- Nhiều toast → xếp chồng từ dưới lên
- Toast mới đẩy toast cũ lên trên

**Default States:**
| State | Hiển thị |
|-------|---------|
| appearing | Fade in |
| visible | Hiển thị đầy đủ |
| disappearing | Fade out |

**Edge Case cần mô tả thêm:**
- Toast có action button (vd: "Hoàn tác")
- Toast không tự tắt (phải ấn X)
- Vị trí khác (góc trái dưới, giữa trên, góc phải trên)
- Toast stack tối đa (vd: tối đa 3 toast cùng lúc)

---

### 15. Banner (`banner`)

**Mô tả:** Thanh thông báo ngang.

**Default Display:**
- Thanh ngang, trên cùng màn hình (dưới header khi có)
- Icon + text + nút X bên phải

**Default Behaviour:**
- KHÔNG tự tắt — user phải ấn X để đóng
- Màu sắc theo loại:
  - Error: nền đỏ nhạt, chữ đỏ đậm
  - Warning: nền vàng nhạt, chữ vàng đậm
  - Info: nền xanh nhạt, chữ xanh đậm
  - Success: nền xanh lá nhạt, chữ xanh lá đậm

**Default States:**
| State | Hiển thị |
|-------|---------|
| visible | Hiển thị đầy đủ |
| dismissed | Đã đóng (không hiện lại trong session) |

**Edge Case cần mô tả thêm:**
- Banner có action button (vd: "Cập nhật ngay", "Thử lại")
- Banner đếm ngược tự tắt
- Banner hiện ở dưới cùng thay vì trên cùng
- Banner cố định (sticky) khi cuộn trang

---

### 16. Pagination (`pagination`)

**Mô tả:** Điều khiển phân trang cho table/list.

**Default Display:**
- Dưới cùng table/list
- `[<] [1] [2] [3] ... [>]  |  1-10 / 45 kết quả`

**Default Behaviour:**
- Chỉ xuất hiện khi danh sách > 10 items
- Mặc định 10 items / trang
- Ấn số trang → tải trang đó
- Ấn `<` / `>` → trang trước/sau
- Trang hiện tại được tô đậm, không ấn được
- Đang tải dữ liệu → disable toàn bộ pagination

**Default States:**
| State | Hiển thị |
|-------|---------|
| default | Hiển thị đầy đủ |
| loading | Mờ, không ấn được |
| single-page | Ẩn (chỉ 1 trang) |

**Edge Case cần mô tả thêm:**
- Số items mỗi trang khác (20, 50, 100)
- Cho phép user chọn số items/trang
- Phân trang không có số trang (chỉ "Xem thêm" / infinite scroll)
- Phân trang với jump-to-page (điền số trang để nhảy)

---

### 17. Tabs (`tabs`)

**Mô tả:** Thanh tab để chuyển đổi nội dung.

**Default Display:**
- Thanh ngang các tab, tab active có gạch chân
- Nội dung tab hiện bên dưới

**Default Behaviour:**
- Ấn tab → chuyển nội dung bên dưới (không reload trang)
- Tab inactive vẫn hiển thị nhưng nội dung ẩn
- Mặc định tab đầu tiên được chọn

**Default States:**
| State | Hiển thị |
|-------|---------|
| active | Gạch chân, chữ đậm |
| inactive | Chữ thường, không gạch chân |
| disabled | Mờ, không ấn được |

**Edge Case cần mô tả thêm:**
- Tab load dữ liệu khi được chọn (lazy load)
- Tab có badge số lượng
- Tab dọc (vertical tabs bên trái)
- Tab có icon + text
- Tab cuộn ngang nếu quá nhiều

---

### 18. Breadcrumb (`breadcrumb`)

**Mô tả:** Đường dẫn phân cấp.

**Default Display:**
- `Trang chủ > Danh mục > Chi tiết`
- Dấu `>` phân cách giữa các cấp

**Default Behaviour:**
- Ấn segment → quay về màn ở cấp đó
- Segment cuối cùng (trang hiện tại) → không ấn được, chữ đậm

**Default States:**
| State | Hiển thị |
|-------|---------|
| active | Ấn được, màu link |
| current | Không ấn được, chữ đậm |

**Edge Case cần mô tả thêm:**
- Breadcrumb rút gọn (dấu `...` khi quá dài)
- Breadcrumb có dropdown ở segment giữa
- Hiển thị icon thay vì text cho cấp đầu

---

### 19. Stepper / Wizard (`stepper`)

**Mô tả:** Chuỗi các bước tuần tự.

**Default Display:**
- Các bước ngang, bước hiện tại tô màu, bước đã qua có dấu ✓
- Nút "Tiếp tục" và "Quay lại" bên dưới

**Default Behaviour:**
- Ấn "Tiếp tục" → kiểm tra bước hiện tại → qua bước sau
- Ấn "Quay lại" → về bước trước, giữ dữ liệu đã điền
- KHÔNG được ấn bước chưa tới (strict mode)
- Bước cuối: nút "Tiếp tục" → "Hoàn thành"

**Default States:**
| State | Hiển thị |
|-------|---------|
| completed | Dấu ✓ xanh, ấn được để quay lại |
| current | Tô màu xanh, chữ đậm |
| pending | Mờ, không ấn được |

**Edge Case cần mô tả thêm:**
- Cho phép ấn bước bất kỳ (non-linear)
- Bước không bắt buộc (có thể bỏ qua)
- Bước có điều kiện (chỉ hiện nếu đáp ứng điều kiện)
- Stepper dọc thay vì ngang

---

### 20. Rich Text Editor (`rich_text_editor`)

**Mô tả:** Vùng soạn thảo văn bản có định dạng.

**Default Display:**
- Toolbar (bold, italic, underline, link, list, image) + vùng soạn thảo

**Default Behaviour:**
- Kế thừa các behaviour cơ bản từ `textarea`
- Paste ảnh → tự động tải lên (nếu hỗ trợ)
- Kéo thả ảnh vào vùng soạn thảo → chèn vào vị trí con trỏ

**Default States:**
| State | Hiển thị |
|-------|---------|
| default | Toolbar + vùng soạn thảo trống |
| focused | Viền xanh, con trỏ nhấp nháy |
| disabled | Mờ, không tương tác được |
| error | Viền đỏ |

**Edge Case cần mô tả thêm:**
- Giới hạn kích thước ảnh trong editor
- Chỉ cho phép 1 số định dạng (vd: không cho chèn ảnh)
- Custom toolbar (chỉ bold, italic, link)
- Giới hạn tổng dung lượng nội dung
- Auto-save khi gõ
