---
receipt_type: options_receipt
receipt_id: ""
slug: ""
date: ""
selected_option: ""
options_status: ""
approved_by: ""
approved_at: ""
skipped: false
invalidated_at: ""
invalidated_reason: ""
---

# Options Receipt

## Fields

| Field | Value |
| --- | --- |
| receipt_type | options_receipt |
| receipt_id | OR-{YYMMDD}-{NN} |
| slug | {slug} |
| date | {date} |
| selected_option | {option-NN or "skipped"} |
| options_status | {completed \| skipped \| not-needed} |
| approved_by | {user or role} |
| approved_at | {YYYY-MM-DD} |
| skipped | {true when --skip was used; false otherwise} |
| invalidated_at | {YYYY-MM-DD if superseded; blank when active} |
| invalidated_reason | {reason if invalidated; blank when active} |

## Decision Summary

{1-2 sentences: which option was selected (or why skipped) and the key rationale.}

## Lifecycle Notes

- **Active:** receipt exists, `invalidated_at` is blank, `options_status` is `completed`, `skipped`, or `not-needed`.
- **Superseded:** user re-selects a different option; set `invalidated_at` and `invalidated_reason` on the old receipt, write a new one.
- **Backbone gate:** backbone step must find an active options receipt (or `options_status: skipped` / `not-needed` in `paths.plan`) before proceeding. If neither exists, emit `GOVERNANCE_BLOCK: options_receipt missing` and stop.
- **First-pass exception:** not applicable — options receipt is required before backbone creation unless options were explicitly skipped.
