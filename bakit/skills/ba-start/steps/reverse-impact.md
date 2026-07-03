# BA Start Step - Reverse Impact

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md` (Reverse Mode Behavior section)

## Memory Read Scope

- **Must read:** `core/contract.yaml`, `core/contract-behavior.md`
- **Must read:** `paths.reverse_baseline_lock`, `paths.reverse_focus_excerpts`
- **May read:** `paths.reverse_index` (for context on scanned files), `paths.reverse_evidence_ledger` (when exists, to avoid re-classifying already classified entries)
- **Must NOT read:** full backbone, full SRS, full stories, memory shards, `log.md`
- **No-broad-read rule:** only files in `paths.reverse_read_manifest` may be re-read; any other file requires `READ_ESCALATION`

## Scope

Classify each unclassified evidence entry into one of three change lanes. Do not mutate canonical artifacts. Write results to `paths.reverse_evidence_ledger`.

## Prerequisites

- `paths.reverse_baseline_lock` must exist. If missing, stop and tell the user to run `/ba-start reverse --slug <slug>` first.
- `paths.reverse_focus_excerpts` must exist. If missing, stop and tell the user to run `/ba-start reverse --slug <slug>` first.
- If `--evidence-ids` is supplied, classify only those entries. Otherwise classify all unclassified entries.

## Change Lane Definitions

| Lane | Meaning | Promotion path |
| --- | --- | --- |
| `as_built_drift` | Behavior exists in code but is absent from or contradicts the documented baseline | `reverse promote` → backbone or SRS |
| `future_state_request` | Desired behavior not yet implemented in code | Forward lifecycle: backbone → FRD → stories |
| `mixed_change` | Contains both as-built and future-state elements | Must be split before promotion |

Classification rules:

- If the evidence shows code that already exists and runs but is undocumented: `as_built_drift`.
- If the evidence describes a desired behavior with no corresponding code: `future_state_request`.
- If the evidence mixes both (e.g. partial implementation with aspirational comments): `mixed_change`.
- If the evidence cannot be classified from source alone: mark `unverifiable_in_v1` and leave `lane: unclassified`.
- Never infer intent beyond what the source text directly states.

## Classification Steps

### Step RI1 — Load Evidence

Read `paths.reverse_focus_excerpts` and, if it exists, `paths.reverse_evidence_ledger`.

Build a working list of entries to classify:
- If `--evidence-ids` supplied: use only those IDs.
- Otherwise: all entries with `lane: unclassified` or no `lane` field.

### Step RI2 — Classify Each Entry

For each entry:

1. Read the excerpt text from `paths.reverse_focus_excerpts`.
2. Apply the lane definitions above.
3. If classification is ambiguous, ask the user one focused question before assigning.
4. Assign `lane`, `confidence` (`high|medium|low`), and a one-line `rationale`.

### Step RI3 — Write Evidence Ledger

Write or update `paths.reverse_evidence_ledger` with all classified entries.

Each entry format:

```
| EV-{NNN} | {file_path} | {short_claim} | {lane} | {confidence} | {rationale} | false |
```

Ledger columns: `evidence_id`, `file`, `claim`, `lane`, `confidence`, `rationale`, `promoted`.

Set `stale_status: unknown` on the ledger header until a validator confirms it.

### Step RI4 — Update Drift State

Write `paths.reverse_drift_state` as JSON:

```json
{
  "documented_commit": "<hash from baseline lock>",
  "as_built_drift_count": 0,
  "future_state_request_count": 0,
  "mixed_change_count": 0,
  "unclassified_count": 0,
  "promoted_count": 0,
  "last_classified_at": "<ISO-8601>"
}
```

### Step RI5 — Output Summary

Print:

```text
Reverse Impact Classification

Commit: {documented_commit}
Entries classified: {count}

  as_built_drift:       {count}
  future_state_request: {count}
  mixed_change:         {count}
  unclassified:         {count}

Evidence ledger: plans/{slug}-{date}/00_reverse/reverse-evidence-ledger.md

Next steps:
  Promote as-built drift:
    /ba-start reverse promote --slug {slug} --evidence-ids <id,...>

  Route future-state items to forward lifecycle:
    /ba-start backbone --slug {slug}

  Split mixed items before promoting:
    Re-run /ba-start reverse impact --slug {slug} --evidence-ids <mixed-ids>
    and answer the clarifying questions to split each entry.
```

## Wireframe Note

Wireframes are always `not-applicable` in reverse mode. Do not suggest `/ba-start wireframes` as a next step from this command.
