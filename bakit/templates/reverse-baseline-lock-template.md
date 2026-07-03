# Reverse Baseline Lock

<!-- machine_facing: JSON record stored as reverse-baseline-lock.json in 00_reverse/. -->
<!-- This template documents the expected fields. Actual artifact is JSON, not markdown. -->

```json
{
  "documented_commit": "<git-commit-hash>",
  "scan_timestamp": "<ISO-8601-datetime>",
  "slug": "<project-slug>",
  "date": "<YYMMDD-HHmm>",
  "focus_selection": [],
  "locked_files": [],
  "scanned_by": "<command>",
  "v1_constraints": {
    "source_only": true,
    "no_runtime_probes": true,
    "no_app_execution": true,
    "no_live_endpoint_verification": true
  },
  "canonical": false,
  "note": "00_reverse artifacts are supporting evidence only. Not in source_of_truth_order."
}
```

## Fields

| Field | Type | Description |
| --- | --- | --- |
| `documented_commit` | string | Git commit hash at time of baseline scan. All reverse claims are valid only against this commit. |
| `scan_timestamp` | string | ISO-8601 datetime when the baseline scan was performed. |
| `slug` | string | Project slug resolved at scan time. |
| `date` | string | Project date token resolved at scan time. |
| `focus_selection` | array | Selected focus areas scoped during the `reverse` command. Empty means full scan. |
| `locked_files` | array | Repo-relative files bound to `documented_commit` for later drift checks. |
| `scanned_by` | string | Command that produced this lock (`reverse` or `reverse_refresh`). |
| `v1_constraints` | object | Source-only constraints enforced in v1. All fields must be `true`. |
| `canonical` | boolean | Always `false`. Reverse artifacts are never canonical source of truth. |
| `note` | string | Human-readable reminder that this artifact is evidence only. |

Legacy compatibility:
- `locked_at` may appear instead of `scan_timestamp`
- `focus_areas` may appear instead of `focus_selection`
