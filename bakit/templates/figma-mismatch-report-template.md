# Figma Mismatch Report

## Metadata

| Field | Value |
| --- | --- |
| report_type | figma-mismatch |
| project_slug | [slug] |
| module_slug | [module-slug] |
| source_index | `./ascii-screen/index.md` |
| generated_at | [YYYY-MM-DDTHH:mm:ssZ] |
| generated_by_command | `ba-figma-sync` |
| mismatch_status | [open / resolved / accepted] |

## Mismatches

| mismatch_id | severity | screen_id | state_id | field_or_region | canon_value | figma_value | required_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FM-001 | block | SCR-XXX-01 | ST-DEFAULT | active_menu | dashboard | reports | update Figma frame or route canon impact |

## Resolution Notes

- [ ] FM-001: [Resolution]

## Routing Rule

- Figma-only mismatch: fix Figma and rerun sync.
- Requirement/label/flow mismatch: route through SRS canon source, validate, compile `srs.md`, then rerun sync.
