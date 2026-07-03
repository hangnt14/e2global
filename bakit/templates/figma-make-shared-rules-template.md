# Quy tắc dùng chung cho Figma Make (Figma Make Shared Rules)

## Hard guardrails

- Chỉ dùng field có trong `screen-field-contract.yaml`
- Không thêm screen ngoài danh sách đã duyệt
- Không đổi top-level navigation, `Portal ID`, `Nav Schema ID`, hoặc `Expected Active Menu Item`
- Nếu rule thiếu hoặc mơ hồ, bỏ qua thay vì tự phát minh
- Giữ nguyên thuật ngữ label, action, state, và feedback surface theo artifact BA-kit

## Reusable review checks

- Không có extra field
- Không thiếu required state
- Không drift validation surface
- Không drift active menu / navigation visibility
- Không đổi hierarchy chính của layout đã khóa trong `DESIGN.md`
