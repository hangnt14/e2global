# Figma Sync Report

## Metadata

| Field | Value |
| --- | --- |
| report_type | figma-sync |
| project_slug | [slug] |
| module_slug | [module-slug] |
| source_index | `./ascii-screen/index.md` |
| shared_shell_contract | `../../02_backbone/shared-shell-contract.md` |
| design_doc | `designs/{slug}/DESIGN.md` |
| generated_at | [YYYY-MM-DDTHH:mm:ssZ] |
| generated_by_command | `ba-figma-sync` |
| sync_status | [synced / partial / blocked] |

## Screen Sync Summary

| screen_id | state_id | frame_name | figma_page | sync_status | notes |
| --- | --- | --- | --- | --- | --- |
| SCR-XXX-01 | ST-DEFAULT | SCR-XXX-01__DEFAULT | [Page] | synced | [Notes] |

## Source Inputs

| input_type | path | source_hash |
| --- | --- | --- |
| screen | `./ascii-screen/scr-xxx-01.md` | [sha256] |
| shared_shell | `../../02_backbone/shared-shell-contract.md` | [sha256] |
| design_doc | `designs/{slug}/DESIGN.md` | [sha256] |

## Read-back Verification

| check | result | notes |
| --- | --- | --- |
| field_labels_match | [pass/fail] | [Notes] |
| action_labels_match | [pass/fail] | [Notes] |
| active_menu_matches | [pass/fail] | [Notes] |
| required_states_present | [pass/fail] | [Notes] |
| overlay_context_present | [pass/fail] | [Notes] |

## Non-mutating Rule

This report records Figma canvas sync only. It must not redefine BA canon. Any mismatch that affects requirements, labels, states, navigation, or behavior must route through canon source edits and a new compiled SRS.
