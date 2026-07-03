# BA Start Step - Reverse Status

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md` (Reverse Mode Behavior section)

## Memory Read Scope

- **Must read:** `core/contract.yaml`, `core/contract-behavior.md`
- **Must read:** `paths.reverse_baseline_lock` (when exists) — header fields only
- **May read:** `paths.reverse_index` (stat + header only), `paths.reverse_drift_state` (when exists), `paths.reverse_evidence_ledger` (summary counts only, no full content read)
- **Must NOT read:** full backbone, full SRS, full stories, memory shards, `log.md`, `paths.reverse_focus_excerpts` (full content), `paths.reverse_read_manifest` (full content)

## Scope

Inspect the reverse lane and print a compact progress checklist. No mutation.

## Prerequisites

- Resolve slug and date using `ba-kit resolve --slug <slug>`.
  The CLI uses `find -type d` internally for correct directory discovery.
  Do not use `Glob` — it only matches files, not directories.
- If slug or date is ambiguous, stop and ask.
- `paths.reverse_baseline_lock` must exist. If missing, print the exact path and tell the user to run `/ba-start reverse --slug <slug>` first.

## Output Format

```text
Reverse Lane Status

Project: {slug}
Date set: {date}
Documented commit: {hash} ({scan_timestamp})

[Baseline]
- [x] reverse-baseline-lock.json — {scan_timestamp}
- [x] reverse-read-manifest.ndjson — {file_count} files scanned

[Index]
- [x|!| ] reverse-index.md — stale_status: {unknown|current|stale}
  validated_at: {value or blank}
  validated_by: {value or blank}

[Evidence]
- [x| ] reverse-focus-excerpts.md — {entry_count} excerpts
- [x| ] reverse-evidence-ledger.md — {total} entries
    as_built_drift: {count}
    future_state_request: {count}
    mixed_change: {count}
    unclassified: {count}
    promoted: {count}

[Drift]
- [x| ] reverse-drift-state.json — {present|absent}

[Focus Areas]
{list each focus area from baseline lock}

Next recommended action:
{derived from evidence state — see rules below}

Guardrail code:
{FOCUS_SELECTION_REQUIRED | REVERSE_REFRESH_REQUIRED | REVERSE_TRACE_COVERAGE_REQUIRED | REVERSE_READ_SCOPE_ESCALATION | none}
```

## Status Rules

- If `reverse_baseline_lock` is absent: print missing path and stop.
- If `reverse_index` stale_status is `unknown` or `stale`: flag with `[!]` and suggest running `reverse refresh`.
- If evidence ledger has `unclassified` entries: recommend `/ba-start reverse impact`.
- If evidence ledger has `as_built_drift` entries not yet promoted: recommend `/ba-start reverse promote`.
- If evidence ledger has `future_state_request` entries: recommend forward lifecycle commands.
- If all entries are promoted and no unclassified remain: print "Reverse lane complete. Consider running `/ba-start backbone` to continue forward lifecycle."
- If focus selection is missing, stale drift is detected, trace coverage is incomplete, or read scope escalated, print the matching reverse guardrail code explicitly.
- Do not read artifact content beyond header fields and counts to produce this output.
