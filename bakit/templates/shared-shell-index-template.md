# Shared Shell Index

## Metadata

| Field | Value |
| --- | --- |
| index_type | shared-shell |
| source_artifact | `plans/{slug}-{date}/02_backbone/shared-shell-contract.md` |
| source_hash | [sha256] |
| generated_at | [YYYY-MM-DDTHH:mm:ssZ] |
| generated_by_command | `ba-start srs` |
| stale_status | unknown |

## Portal Registry

| portal_id | portal_name | target_actor | path |
| --- | --- | --- | --- |
| PORTAL-ADMIN | [Portal Name] | [Actor] | `./shared-shell-contract.md#portals` |

## Navigation Schema Registry

| nav_schema_id | portal_id | pattern | menu_keys | path |
| --- | --- | --- | --- | --- |
| NAV-XXX-01 | PORTAL-ADMIN | sidebar | dashboard | `./shared-shell-contract.md#nav-xxx-01` |

## Shell Variant Registry

| shell_variant | navigation_region | header_region | path |
| --- | --- | --- | --- |
| SHELL-APP-DEFAULT | sidebar_left | topbar | `./shared-shell-contract.md#shell-variants` |

## Layout Variant Registry

| layout_variant | purpose | required_regions | path |
| --- | --- | --- | --- |
| LAYOUT-LIST-01 | List page | page_header,filter_bar,data_table,pagination | `./shared-shell-contract.md#layout-variants` |
