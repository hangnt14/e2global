## Yêu cầu chức năng

| Mã (ID) | Yêu cầu (Requirement) | Ưu tiên (Priority) | Nguồn (Source) | Tiêu chí chấp nhận (Acceptance Criteria) |
| --- | --- | --- | --- | --- |
| FR-auth-001 | User login với email/password | Must | Backbone | Login thành công trong 3 lần thử |
| FR-auth-002 | Hiển thị thông báo lỗi khi sai password | Must | Backbone | Hiển thị "Sai mật khẩu" sau lần thử thứ 3 |

## Yêu cầu phi chức năng

| Mã (ID) | Danh mục (Category) | Yêu cầu (Requirement) | Mục tiêu (Target) |
| --- | --- | --- | --- |
| NFR-auth-001 | Hiệu năng | Login response < 2s | 95th percentile |
