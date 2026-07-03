# Danh sách thông điệp dùng chung (Message List)

## Metadata

| Field | Value |
| --- | --- |
| source_artifact | `plans/{slug}-{date}/02_backbone/backbone.md` |
| generated_by_command | `ba-start backbone` |
| status | draft |
| owner | Lead BA |

## Message List

| code | type | canonical_text | surface | applies_to | owner | status | source | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MSG-ERR-01 | ERR | [Canonical message text] | inline | [module/screen/field scope] | Lead BA | active | [source] | [notes] |

## Usage Rules

- Module artifacts must reference these codes instead of redefining shared messages.
- New `MSG-*` codes must be added here before module screens or contracts can use them.
- Reusing an existing code with different message text is blocked.
