# Reverse Index

<!-- agent_facing: navigator index of scanned artifacts and their evidence status. -->
<!-- Not a source of truth. Valid only against documented_commit in reverse-baseline-lock.json. -->

index_type: reverse_index
source_artifact: plans/{slug}-{date}/00_reverse/reverse-baseline-lock.json
documented_commit: <git-commit-hash>
generated_at: <ISO-8601-datetime>
stale_status: unknown
validated_at:
validated_by:

## Focus Areas

| Focus ID | Label | Scanned Files | Evidence Count | Status |
| --- | --- | --- | --- | --- |
| FA-01 | <focus-area-label> | 0 | 0 | pending |

## Scanned Artifacts

| # | File Path | Type | Evidence IDs | Drift Lane | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | <path> | code\|config\|doc\|schema | | unclassified | |

## Evidence Summary

| Evidence ID | File | Claim | Lane | Promoted | Ledger Ref |
| --- | --- | --- | --- | --- | --- |
| EV-001 | <path> | <short claim> | as_built_drift\|future_state_request\|mixed_change | false | |

## Read Manifest Reference

Allowlisted files for subsequent reverse commands: `plans/{slug}-{date}/00_reverse/reverse-read-manifest.ndjson`

Any file not in the manifest requires `READ_ESCALATION` before access.

## Notes

- All entries are valid only against `documented_commit`.
- After `reverse_refresh`, re-validate all entries before treating as current.
- `stale_status` must remain `unknown` until validator sets `validated_at` and `validated_by`.
