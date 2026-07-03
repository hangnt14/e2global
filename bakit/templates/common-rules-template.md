# Danh mục quy tắc dùng chung (Common Rules)

## Metadata

| Field | Value |
| --- | --- |
| source_artifact | `plans/{slug}-{date}/02_backbone/backbone.md` |
| generated_by_command | `ba-start backbone` |
| status | draft |
| owner | Lead BA |

## Common Rules

| code | type | rule_statement | applies_to | edge_cases | owner | status | source | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CR-VAL-01 | VAL | [Canonical validation rule statement] | [module/screen/field scope] | [edge case: điều kiện + kết quả mong đợi. Phân cách bởi dấu chấm.] | Lead BA | active | [source] | [notes] |
| CR-DIS-01 | DIS | Hiện pagination khi danh sách > 10 items | Màn hình có `table`, danh sách, bảng | = 10 items: không pagination, hiện hết. 0 items: hiện empty state. | Lead BA | active | backbone | — |
| CR-BEH-01 | BEH | Button submit của form disabled khi required field chưa điền | `button (primary)` trong form | Form không có required field: button luôn active. Form có lỗi validation: button disabled. | Lead BA | active | backbone | — |

## Usage Rules

- Module artifacts must reference these codes instead of redefining shared rules.
- New `CR-*` codes must be added here before module screens or contracts can use them.
- Reusing an existing code with different meaning is blocked.
