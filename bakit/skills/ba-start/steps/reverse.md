# BA Start Step - Reverse

This step handles three reverse lane commands: `reverse` (entry/baseline scan), `reverse refresh`, and `reverse promote`.

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md` (Reverse Mode Behavior section)

## Memory Read Scope

- **Must read:** `core/contract.yaml`, `core/contract-behavior.md`
- **May read:** `paths.reverse_baseline_lock` (when exists), `paths.reverse_index` (when exists), `paths.reverse_evidence_ledger` (promote only)
- **Must NOT read:** full backbone, full SRS, full stories, memory shards, `log.md` — unless explicitly escalated
- **No-broad-read rule:** after baseline scan, only files listed in `paths.reverse_read_manifest` may be re-read without emitting `READ_ESCALATION`

## V1 Hard Constraints

**NEVER** do any of the following in reverse mode v1:

- Execute application code or scripts
- Make live HTTP/API calls or probe running services
- Query databases or read runtime state
- Run test suites or build pipelines
- Infer behavior from anything other than committed source files

If a claim requires runtime verification, mark it `unverifiable_in_v1` in the evidence ledger.

---

## Command: `reverse` (Baseline Scan and Lock)

### Prerequisites

- Resolve slug and date using `ba-kit resolve --slug <slug>`.
  The CLI uses `find -type d` internally for correct directory discovery.
  Do not use `Glob` — it only matches files, not directories.
- If slug or date is ambiguous, stop and ask.
- If `paths.reverse_baseline_lock` already exists, print the path and ask whether to overwrite before proceeding.

### Step R1 — Resolve Commit

Determine `documented_commit`:

1. If `--commit <hash>` was supplied, use it.
2. Otherwise run `git rev-parse HEAD` to capture the current HEAD commit.
3. Record the hash and current ISO-8601 timestamp.

If git is unavailable or the repo has no commits, stop and ask the user to supply `--commit <hash>` manually.

### Step R2 — Focus Selection (HITL Gate)

Present the user with a list of available focus areas based on the repository structure. Suggested focus areas:

- `api` — API endpoints, routes, controllers
- `data-model` — database schemas, models, migrations
- `auth` — authentication and authorization logic
- `ui` — frontend components, screens, forms
- `config` — configuration files, environment variables
- `docs` — existing documentation, README, specs
- `integrations` — third-party service integrations, webhooks
- `business-rules` — domain logic, validation, workflows

Ask the user to select one or more focus areas, or confirm `all` for a full scan.

**This is a blocking HITL gate. Do not proceed to Step R3 until focus areas are confirmed.**

### Step R3 — Baseline Scan

For each selected focus area, scan only committed source files (no runtime execution):

- Read relevant files within the focus area scope.
- Extract evidence: behaviors, rules, data structures, API contracts, screen flows, business logic.
- Record every file read in `paths.reverse_read_manifest` as an NDJSON line:
  `{"file": "<path>", "focus": "<area>", "read_at": "<ISO-8601>", "commit": "<hash>"}`

Scan rules:

- Read only files tracked by git at `documented_commit`.
- Skip generated files, build artifacts, and lock files unless they contain schema or contract definitions.
- Keep excerpts short — capture the minimum text needed to support a claim.
- Do not infer behavior beyond what the source text directly states.

### Step R4 — Build Reverse Index

Write `paths.reverse_index` using `templates/reverse-index-template.md`:

- List every scanned file with its focus area and evidence count.
- Set `stale_status: unknown` — do not set `validated_at` or `validated_by`.
- Set `documented_commit` to the hash from Step R1.

### Step R5 — Build Focus Excerpts

Write `paths.reverse_focus_excerpts`:

- One section per focus area.
- Each section: file path, excerpt (≤20 lines), evidence claim, confidence (`high|medium|low`).
- Mark any claim that cannot be verified from source alone as `unverifiable_in_v1`.

### Step R6 — Write Baseline Lock

Write `paths.reverse_baseline_lock` as JSON:

```json
{
  "documented_commit": "<hash>",
  "scan_timestamp": "<ISO-8601>",
  "slug": "<slug>",
  "date": "<date>",
  "focus_selection": ["<area>", ...],
  "locked_files": ["<repo-relative-path>", "..."],
  "scanned_by": "reverse",
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

Compatibility note: older reverse artifacts may still use `locked_at` and `focus_areas`.
New writes must use `scan_timestamp` and `focus_selection`.

### Step R7 — Output Summary

Print:

```text
Reverse Baseline Scan Complete

Commit: <hash>
Timestamp: <ISO-8601>
Focus areas: <list>
Files scanned: <count>
Evidence entries: <count>

Baseline lock: plans/{slug}-{date}/00_reverse/reverse-baseline-lock.json
Reverse index: plans/{slug}-{date}/00_reverse/reverse-index.md
Read manifest: plans/{slug}-{date}/00_reverse/reverse-read-manifest.ndjson

Next: /ba-start reverse impact --slug <slug>
      to classify evidence before promoting to backbone.
```

---

## Command: `reverse refresh`

### Prerequisites

- `paths.reverse_baseline_lock` must exist. If missing, stop and tell the user to run `reverse` first.

### Steps

1. Resolve new `documented_commit` from `--commit <hash>` or `git rev-parse HEAD`.
2. If the new commit matches the existing `documented_commit`, print "Already at this commit. No refresh needed." and stop.
3. Ask the user to confirm overwrite of existing reverse artifacts before proceeding.
4. Re-run Steps R3–R6 with `"scanned_by": "reverse_refresh"`.
5. Mark all existing evidence ledger entries as `needs-revalidation` (do not delete them).
6. Print a refresh summary showing old commit → new commit and evidence count delta.

---

## Command: `reverse promote`

### Prerequisites

- `paths.reverse_baseline_lock` must exist.
- `paths.reverse_evidence_ledger` must exist.
- `--evidence-ids <id,...>` must be supplied.

### Promotion Rules

- Only `as_built_drift` items may be promoted directly to backbone or SRS.
- `future_state_request` items must be routed to the forward lifecycle — print the recommended command and stop.
- `mixed_change` items must be split by `reverse impact` first — print the instruction and stop.
- Each promotion batch requires explicit user approval before any canonical artifact is mutated.

### Steps

1. Read `paths.reverse_evidence_ledger` and extract the specified evidence IDs.
2. Validate each entry's `lane` field:
   - `as_built_drift` → eligible for promotion
   - `future_state_request` → print routing instruction, stop
   - `mixed_change` → print split instruction, stop
   - `unclassified` → print "Run `reverse impact` first to classify", stop
3. For eligible entries, show the user a promotion preview:
   - Evidence ID, claim text, target artifact (backbone or SRS section), proposed change
4. Ask for explicit approval per batch before writing.
5. On approval, apply the narrowest possible update to the target canonical artifact.
6. Mark promoted entries in the ledger with `promoted: true` and `promoted_at: <ISO-8601>`.
7. Print a promotion summary.

### Transition to Forward Lifecycle

After promotion, if the evidence set contains `future_state_request` items:

```text
Future-state items found. These require forward lifecycle authoring:
  /ba-start backbone --slug <slug>   (if backbone needs updating)
  /ba-start stories --slug <slug> --module <module>
  /ba-start srs --slug <slug> --module <module>
```

Wireframes are always `not-applicable` in reverse mode. Do not suggest `/ba-start wireframes` as a reverse lane output.
