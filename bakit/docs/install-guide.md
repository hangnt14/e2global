# Hướng dẫn cài đặt BA-kit

## Yêu cầu

- Máy tính có kết nối Internet
- Tài khoản GitHub đã được cấp quyền truy cập vào kho mã nguồn BA-kit (`bakit-org/bakit`)
- macOS, Linux, hoặc Windows (với Git Bash)

## Cài đặt BA-kit

### Bước 1: Tải BA-kit

Tải mã nguồn BA-kit từ GitHub và giải nén vào thư mục trên máy.

### Bước 2: Chạy lệnh cài đặt

Mở **Terminal** (macOS/Linux) hoặc **Git Bash** (Windows), di chuyển vào thư mục BA-kit và chạy:

```bash
cd duong-dan-den-thu-muc-ba-kit
bash install.sh
```

### Bước 3: Làm theo hướng dẫn trên màn hình

Hệ thống sẽ tự động cài đặt và hỏi bạn một số câu hỏi.

---

## Kịch bản 1: Bạn là BA độc lập (không thuộc tổ chức)

Sau khi cài đặt xong, BA-kit sẽ hỏi bạn có muốn **kích hoạt bản quyền** không.

1. Chọn **C** (Có) để kích hoạt.
2. Khi được hỏi **"Bạn có mã doanh nghiệp không?"**, chọn **K** (Không).
3. Trình duyệt sẽ tự động mở trang GitHub. Nếu không, mở thủ công địa chỉ hiển thị trên màn hình.
4. **Nhập mã xác nhận** hiển thị trên màn hình vào trang GitHub.
5. Nhấn **"Authorize"** để cấp quyền.
6. Quay lại Terminal — hệ thống sẽ tự động hoàn tất.

Sau khi kích hoạt, bạn có thể dùng tất cả các tính năng của BA-kit.

---

## Kịch bản 2: Bạn là BA trong doanh nghiệp/tổ chức

Trước khi cài đặt, bạn cần nhận từ **quản lý dự án**:

| Thông tin | Là gì? | Ví dụ |
|-----------|--------|-------|
| **Mã doanh nghiệp** | Mã định danh tổ chức của bạn | `abc-corp-2024` |
| **Địa chỉ máy chủ doanh nghiệp** | Trang web quản lý của tổ chức | `https://ba.congty.com` |

Sau khi cài đặt xong, BA-kit sẽ hỏi bạn có muốn **kích hoạt bản quyền** không.

1. Chọn **C** (Có) để kích hoạt.
2. Khi được hỏi **"Bạn có mã doanh nghiệp không?"**, chọn **C** (Có).
3. **Nhập mã doanh nghiệp** do quản lý cấp.
4. **Nhập địa chỉ máy chủ doanh nghiệp** do quản lý cấp.
5. Trình duyệt sẽ tự động mở trang GitHub — làm theo hướng dẫn trên màn hình.
6. Sau khi xác nhận GitHub, hệ thống sẽ tự động kết nối với máy chủ doanh nghiệp.

Nếu máy chủ doanh nghiệp từ chối, **bản quyền cá nhân vẫn hoạt động**. Liên hệ quản lý để kiểm tra.

---

## Kích hoạt lại bản quyền

Nếu bản quyền hết hạn hoặc bị thu hồi, chạy lệnh sau trong Terminal:

```bash
ba-kit reauth
```

Lệnh này sẽ kiểm tra bản quyền hiện tại và hướng dẫn bạn đăng ký lại nếu cần.

---

## Xem thống kê sử dụng

Mở trình duyệt và truy cập:

```
http://localhost:9090
```

Trang này hiển thị số token bạn đã dùng, các kỹ năng đã chạy, và dự án đang làm.

---

## Gỡ cài đặt

Để gỡ BA-kit, xoá các thư mục sau:

```bash
rm -rf ~/.claude/ba-kit
rm -rf ~/.claude/skills/ba-*
rm -f ~/.local/bin/ba-kit
```

---

## Câu hỏi thường gặp

### Tôi không có trình duyệt (máy chủ SSH)

Khi màn hình hiển thị địa chỉ GitHub và mã xác nhận, hãy **mở địa chỉ đó trên điện thoại** và nhập mã. Hệ thống sẽ tự động phát hiện khi bạn xác nhận xong.

### "Không kết nối được với máy chủ bản quyền"

Kiểm tra kết nối Internet. BA-kit sẽ hoạt động thử trong 7 ngày. Sau đó cần kết nối Internet để kiểm tra lại.

### "Tài khoản GitHub chưa được cấp quyền"

Tài khoản GitHub của bạn chưa có quyền truy cập vào kho mã nguồn BA-kit. **Liên hệ quản lý dự án** để được thêm vào danh sách cộng tác viên của `bakit-org/bakit`.
