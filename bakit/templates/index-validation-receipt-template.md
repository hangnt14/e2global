---
receipt_type: index_validation_receipt
receipt_id: ""
slug: ""
date: ""
module: ""
index_key: ""
index_path: ""
source_artifact: ""
source_hash: ""
validated_at: ""
validated_by: ""
stale_status: ""
invalidated_at: ""
invalidated_reason: ""
---

# Index Validation Receipt

## Fields

| Field | Value |
| --- | --- |
| receipt_type | index_validation_receipt |
| receipt_id | IVR-{YYMMDD}-{NN} |
| slug | {slug} |
| date | {date} |
| module | {module or "system"} |
| index_key | {backbone_index \| userstories_index \| usecases_index \| ascii_screen_index} |
| index_path | {path to the index file} |
| source_artifact | {path to the source artifact the index was built from} |
| source_hash | {sha256 of source artifact at validation time} |
| validated_at | {YYYY-MM-DDTHH:mm:ssZ} |
| validated_by | {validate-index-quality \| runtime validator id} |
| stale_status | {current \| stale \| unknown} |
| invalidated_at | {YYYY-MM-DD if superseded; blank when active} |
| invalidated_reason | {reason if invalidated; blank when active} |

## Lifecycle Notes

- **Active / current:** `stale_status: current`, `validated_at` is set, `invalidated_at` is blank.
- **Stale:** source artifact was mutated after `validated_at`; set `stale_status: stale`. Downstream steps must not trust a stale index for routing.
- **Unknown:** index was just generated but not yet validated; producer must leave `stale_status: unknown` and run `validate-index-quality` before any downstream step treats it as current.
- **Invalidation trigger:** any mutation to the source artifact (backbone, user stories, use cases, ASCII screens, or SRS slices) invalidates the corresponding index receipt. A new validation run is required before the index can be used for routing.
- **Self-certification ban:** the producer step must never promote `stale_status` from `unknown` to `current`. Only the validator script or runtime validator may do so.
