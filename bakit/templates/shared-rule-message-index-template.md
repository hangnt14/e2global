# Chỉ mục rule/message dùng chung (Shared Rule Message Index)

## Metadata

| Field | Value |
| --- | --- |
| index_type | shared-rule-message |
| source_common_rules | `plans/{slug}-{date}/02_backbone/common-rules.md` |
| source_message_list | `plans/{slug}-{date}/02_backbone/message-list.md` |
| generated_at | [YYYY-MM-DDTHH:mm:ssZ] |
| generated_by_command | `validate-shared-rule-message-registry --write-index` |
| stale_status | unknown |
| validated_at | [YYYY-MM-DDTHH:mm:ssZ after validator pass; blank when pending or failed] |
| validated_by | [`validate-shared-rule-message-registry` or runtime validator id; blank when pending or failed] |

Producer note: read this index before opening full shared registries. Read full registry files only when this index is missing, stale, or exact text is required.

## Rule Code Index

| code | type | summary | source_anchor | applies_to | owner | status |
| --- | --- | --- | --- | --- | --- | --- |
| CR-VAL-01 | VAL | [Short rule summary] | common-rules.md#CR-VAL-01 | [scope] | Lead BA | active |

## Message Code Index

| code | type | summary | source_anchor | applies_to | owner | status |
| --- | --- | --- | --- | --- | --- | --- |
| MSG-ERR-01 | ERR | [Short message summary] | message-list.md#MSG-ERR-01 | [scope] | Lead BA | active |

## Collision And Scope Signals

| signal | value |
| --- | --- |
| rule_count | 0 |
| message_count | 0 |
| duplicate_codes | 0 |
| stale_refs | 0 |
| module_local_definitions | 0 |
