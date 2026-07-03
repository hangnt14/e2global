---
receipt_type: impact_receipt
receipt_id: ""
slug: ""
date: ""
module: ""
artifact: ""
approved_by: ""
approved_at: ""
approval_basis: ""
change_class: ""
invalidated_at: ""
invalidated_reason: ""
---

# Impact Receipt

## Fields

| Field | Value |
| --- | --- |
| receipt_type | impact_receipt |
| receipt_id | IR-{YYMMDD}-{NN} |
| slug | {slug} |
| date | {date} |
| module | {module or "system"} |
| artifact | {target artifact path} |
| approved_by | {user or role} |
| approved_at | {YYYY-MM-DD} |
| approval_basis | {brief reason — scope change, new feature, correction, etc.} |
| change_class | {scope-change \| content-update \| wording-only} |
| invalidated_at | {YYYY-MM-DD if superseded; blank when active} |
| invalidated_reason | {reason if invalidated; blank when active} |

## Scope Summary

{1-3 sentences describing what change was approved and why.}

## Affected Artifacts

- {artifact path 1}
- {artifact path 2}

## Lifecycle Notes

- **Active:** receipt exists, `invalidated_at` is blank, `approved_at` is set.
- **Superseded:** a newer receipt covers the same artifact; set `invalidated_at` and `invalidated_reason`.
- **Refresh trigger:** any scope change, actor change, or structural rewrite requires a new receipt. Wording-only fixes are exempt — use `change_class: wording-only` and skip the impact run.
- **First-pass exception:** receipt is not required when the target artifact does not yet exist.
