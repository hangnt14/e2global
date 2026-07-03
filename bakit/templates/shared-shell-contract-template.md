# Shared Shell Contract

## Metadata

- Project: [Project]
- Slug: [slug]
- Status: [Draft | Approved]
- Owner scope: system

## Portals

| portal_id | portal_name | target_actor | notes |
| --- | --- | --- | --- |
| PORTAL-ADMIN | [Portal Name] | [Actor] | [Notes] |

## Navigation Schemas

### NAV-XXX-01

| key | label | route_pattern | visible |
| --- | --- | --- | --- |
| dashboard | Dashboard | /dashboard | Yes |

## Shell Variants

| shell_variant | navigation_region | header_region | breadcrumb_region | content_width | allowed_overrides |
| --- | --- | --- | --- | --- | --- |
| SHELL-APP-DEFAULT | sidebar_left | topbar | page_top | fluid | navigation_region_visible,page_header_actions |

## Layout Variants

| layout_variant | purpose | required_regions | notes |
| --- | --- | --- | --- |
| LAYOUT-LIST-01 | List page | page_header,filter_bar,data_table,pagination | [Notes] |

## Shared Components

| component_id | type | owned_by | notes |
| --- | --- | --- | --- |
| CMP-SIDEBAR-01 | sidebar | system | [Notes] |

## Active Menu Rules

| nav_schema_id | rule | notes |
| --- | --- | --- |
| NAV-XXX-01 | exact_route_or_declared_key | [Notes] |

## Exceptions

| exception_code | applies_to | rule |
| --- | --- | --- |
| NAV-HIDDEN-MODAL | modal,drawer | navigation_region_visible_may_be_false |

## Change Control

- Module-level artifacts may reference but must not redefine these contracts.
- Any global navigation or shell change must route through system-level review.
