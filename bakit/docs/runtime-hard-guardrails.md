# Runtime Hard Guardrails

BA-kit needs a portable hard-guardrail layer that works across Codex, Claude Code, and Antigravity without inflating model input on every run.

This document defines the preferred design for command-scoped read enforcement where guidance already requires index-first or source-of-truth-first behavior.

For the producer-side issuance and validation rules that determine whether an index may become `current`, see [runtime-index-quality-hardening.md](./runtime-index-quality-hardening.md).

## Goals

- enforce deterministic read order for critical commands
- keep the enforcement logic outside the model whenever possible
- reuse the existing contract, behavior shards, index metadata, and parity harness
- support Codex, Claude Code, and Antigravity with one portable core plus thin adapters
- keep runtime prompt additions short enough to remain low-token

## Priority Scope

The first hard-guardrail rollout should cover these behaviors:

1. `frd` and `stories` must read `paths.backbone_index` first and must not discovery-read the full `paths.backbone` when the index is current.
2. `package` must use `paths.backbone_index`, `paths.stories_index`, and `paths.srs_index` first for discovery and must not broad-read full intake/backbone/stories/SRS artifacts when those indexes are current.
3. `status` and `next` may read `paths.project_home`, but must never let it override canonical artifact state.
4. `srs` must write canon sources first (`screens/`, `usecases/`, optional `data/`, optional `flows/`), then compile `srs.md` with `srs-compile-receipt.json`.
5. `figma-sync` must read canon + shared shell and write only sync/mismatch reports; it must not mutate BA canon or shared shell files.

## Why A Hook Layer Exists

The shared contract already expresses the desired policy:

- `frd` and `stories` start from `paths.backbone_index` and use targeted backbone sections only when the index is current.
- `package` uses indexes first and may read full markdown only when exact compilation or validation requires it.
- `status` and `next` treat `paths.project_home` as a dashboard, not as source of truth.

These rules are currently guidance plus parity intent. The guardrail layer upgrades them into deterministic runtime behavior.

## Definitions

### Current Index

An index is considered `current` when all of the following are true:

1. the index file exists
2. `stale_status` is `current`
3. `source_artifact` resolves to the exact expected artifact path
4. `source_hash` matches the current contents of `source_artifact`
5. `validated_at` and `validated_by` confirm the index passed producer-side validation
6. the index contains enough routing coverage for the command's requested scope
7. when excerpt delivery is required, the routed heading set resolves to at least one extractable source section

If any of those checks fail, the index state is not current and must be treated as `stale` or `unknown`.

### Index Freshness State Machine

Guardrail scripts should classify index freshness using these deterministic states:

| State | Meaning | Default Runtime Action |
| --- | --- | --- |
| `current` | metadata is internally consistent, producer-validated, and source hash matches the current source artifact | allow index-first execution |
| `stale` | index exists but was generated from an older source artifact revision or is missing needed routing coverage | block index-first assumptions and require refresh or escalation |
| `missing` | index file does not exist at the expected path | block index-first assumptions and require refresh or escalation |
| `contradictory` | metadata conflicts materially with runtime expectations, such as wrong source artifact path, malformed metadata, or source/type mismatch | fail closed and require refresh before continuing |
| `unknown` | metadata is incomplete and the hook cannot determine freshness safely | fail closed unless the command contract explicitly allows escalation |

Classification rules:

1. missing file at the expected index path -> `missing`
2. malformed or absent required metadata fields, including producer validation fields required by the index contract -> `contradictory`
3. `source_artifact` resolves to a different artifact type or path than the command expects -> `contradictory`
4. `source_hash` mismatch against the current source artifact -> `stale`
5. `stale_status` set to `stale` or `unknown` in the file metadata -> preserve that state unless stronger evidence forces `contradictory`
6. routing table exists but does not cover the requested module, feature, or anchor slice -> `stale`
7. index-scoped excerpt delivery is required but no extractable source section can be produced from the routed headings -> `stale`
8. only when none of the above trigger may the index be classified as `current`

For v1, `source_hash` mismatch alone should classify as `stale`, not `contradictory`. `contradictory` is reserved for cases where trusting the file would be structurally unsafe rather than merely outdated.

### Discovery Read

A discovery read is any read used to decide what to author, compare, validate, or route to next.

Examples:

- scanning backbone headings to find the right feature for stories
- scanning SRS to find cross-reference targets during package assembly
- scanning `PROJECT-HOME.md` to infer lifecycle state

### Exact-Content Read

An exact-content read is a read of the currently targeted artifact because the command must consume the exact markdown content for rendering, validation, or excerpt generation.

Examples:

- reading full `srs.md` while converting that exact file to HTML
- reading a narrow backbone section after the index already identified the target anchor

## Portable Architecture

The guardrail design uses three deterministic layers.

### 1. Preflight

Run before the model:

- resolve command, slug, date, and module
- resolve relevant indexes and source artifacts
- compute whether each index is `current`, `stale`, `missing`, or `contradictory`
- compute the allowlist and denylist for the command
- decide whether targeted excerpts can be built automatically
- precompute canonical status or next-step summaries when runtime scope must stay compact
- block the run early when policy requires a refresh or escalation

Preflight may inspect broader source-of-truth artifacts to derive a deterministic summary, but that must not widen the runtime read allowlist delivered to the model.

### 2. Read Enforcement

Run during the model session when the runtime supports path-aware interception, or simulate it through controlled context delivery when it does not.

Expected behavior:

- allow only the index plus contract files for discovery when the index is current
- deny full-source discovery reads that bypass the index
- allow narrow source excerpts derived from index anchors
- require explicit escalation when broad reads are still necessary

### 3. Post-Run Audit

Run after the model:

- inspect the runtime trace or the adapter-delivered context manifest
- verify the model did not bypass the allowed read scope
- verify any broad read was accompanied by a valid escalation reason
- fail the run when actual reads violate the command guardrail

## Low-Token Strategy

The model should not receive the full guardrail policy again on every run.

Instead, the adapter should inject a short verdict such as:

```text
GUARDRAIL: cmd=stories idx=backbone current=1 allow=backbone_index,excerpt deny=backbone_full
```

or:

```text
GUARDRAIL_BLOCK: cmd=package reason=srs_index_stale refresh=ba-start srs --slug <slug> --module <module>
```

All heavy logic stays in deterministic scripts. The model receives only:

- a compact verdict
- the exact allowed paths
- any generated excerpt files
- when the action is backbone-routeable, a tiny per-action `ACTION_GUARDRAIL` reminder that reasserts `navigation_source=backbone_index`

This design should reduce average prompt size for large artifacts because the model no longer needs to open full source-of-truth files just to find the relevant slice.

## Portable-Core Versus Runtime-Hint Fields

To keep Codex, Claude Code, and Antigravity aligned, guardrail payloads should distinguish mandatory portable-core data from optional runtime-hint data.

### Portable-Core Fields

These fields must be supported consistently across all runtimes:

- `status`
- `command`
- `resolved_slug`
- `resolved_module` when applicable
- `guardrail_mode`
- `reason` for block or warning states
- `message`
- `indexes.<name>.state`
- `refresh_command` when blocked

### Runtime-Hint Fields

These fields improve ergonomics but may be delivered differently per runtime:

- `allow_reads`
- `deny_reads`
- `excerpt_plan`
- explicit absolute paths to generated excerpt files
- trace-manifest references used by post-run audit

Antigravity may consume runtime-hint fields as injected packet content rather than native file-path permissions. Codex and Claude Code may consume them as allowlists or wrapper manifests.

## Command Contracts

### `frd`

When `paths.backbone_index` is current:

- must read `core/contract.yaml`
- must read `core/contract-behavior.md`
- must read `paths.backbone_index`
- may read `paths.plan`
- may read generated targeted backbone excerpt files
- must not discovery-read full `paths.backbone`

Allowed broad read:

- only through `READ_ESCALATION`
- only when the index is missing, stale, contradictory, or insufficient for the requested feature slice

### `stories`

When `paths.backbone_index` is current:

- must read `core/contract.yaml`
- must read `core/contract-behavior.md`
- must read `paths.backbone_index`
- may read `paths.plan` when needed
- may read `paths.frd` when it already exists and the current mode justifies it
- may read generated targeted backbone excerpt files
- must not discovery-read full `paths.backbone`

### `package`

Discovery phase:

- must read `core/contract.yaml`
- must read `core/contract-behavior.md`
- must read current index files first
- may read compact memory or `paths.memory_index`
- must not discovery-read full raw source, intake, backbone, stories, or SRS artifacts when the relevant indexes are current

Exact-content phase:

- may read the full artifact currently being compiled or validated
- must emit `READ_ESCALATION` when a full read is required because an index is missing, stale, or contradictory

### `srs`

- must read `paths.backbone_index`, `paths.stories_index`, `paths.design_doc`, `paths.shared_shell_contract`, and `paths.shared_shell_index` when present
- must author requirement behavior into canon sources before updating the compiled deliverable
- may write `paths.screen_root`, `paths.usecase_root`, `paths.module_erd`, `paths.flow_root`, `paths.srs_index`, `paths.srs`, and `paths.srs_compile_receipt`
- must not treat `paths.srs` as the direct-edit source when canon sources exist
- must refresh `paths.srs_compile_receipt` after compiling `paths.srs`
- post-run should execute `ba-kit doctor-srs <module_root>` or equivalent validators

### `figma-sync`

- must read `paths.srs_index` before individual screen canon files
- may read `paths.screen_root`, `paths.design_doc`, `paths.shared_shell_contract`, `paths.shared_shell_index`, and `paths.srs_compile_receipt`
- may write only `paths.figma_sync_report` and `paths.figma_mismatch_report` inside the repo
- must not write `paths.srs`, `paths.srs_index`, `paths.screen_root`, `paths.usecase_root`, `paths.design_doc`, or `paths.shared_shell_contract`
- must block when the compile receipt is missing or stale, because Figma must represent the same canon that the SRS deliverable represents

### `status`

- may read `paths.project_home`
- may read `paths.project_memory` header fields and `paths.memory_index`
- must resolve canonical state from contract artifacts, not from dashboard prose
- must warn when `paths.project_home` conflicts with canonical artifacts
- must not let dashboard text override lifecycle state, source of truth, or next-step resolution
- runtime delivery should stay compact: `PROJECT-HOME.md`, compact memory header, and `memory_index` only by default
- should emit a deterministic `canonical_state_summary` from artifact state so adapters can inject the conclusion directly instead of asking the runtime to infer it from `PROJECT-HOME.md`

### `next`

- may read `paths.project_home`
- may read `paths.project_memory` header fields and `paths.memory_index`
- must compute the next safe command from exact artifact presence and contract gates
- must warn when `paths.project_home` disagrees with canonical artifacts
- must not recommend a step that only the dashboard suggests when canonical artifacts disagree
- runtime delivery should stay compact: `PROJECT-HOME.md`, compact memory header, and `memory_index` only by default
- should emit a deterministic `canonical_next_command` when canonical artifacts are sufficient to resolve the next safe step

## Escalation Contract

`READ_ESCALATION` is valid only when all of the following are true:

1. the command has already attempted index-first routing
2. the index was classified `missing`, `stale`, `unknown`, or `contradictory`, or the routed slice was insufficient
3. the escalation target path is named explicitly
4. the reason states why the index could not safely satisfy the read

Canonical output format:

```text
READ_ESCALATION: {command} read {path} due to {reason}.
```

Guardrail-covered commands must not emit `READ_ESCALATION` merely for convenience. It is a fail-closed override, not a generic fallback.

## Adapter Strategy By Runtime

### Codex

Preferred mode:

- wrapper calls preflight before `codex exec`
- adapter exposes only allowed files or generated excerpts when possible
- post-run audit inspects available trace output when supported

Fallback mode:

- wrapper injects only the compact guardrail verdict plus excerpt paths
- adapter treats any direct full-source read request as a block unless an escalation file is present

### Claude Code

Preferred mode:

- use available path-aware tool constraints or hook points for read enforcement
- reuse the same preflight and audit scripts as Codex

Fallback mode:

- wrapper plus excerpt-only delivery, same as Codex fallback

### Antigravity

Antigravity must assume the most conservative adapter until richer hook support is confirmed.

Preferred mode for v1:

- run preflight outside the runtime
- deliver only portable-core context plus compact excerpts
- do not rely on runtime-native file-path enforcement
- encode any block or warning in the injected packet

This keeps Antigravity aligned with the same guardrail outcome even when native hook injection or tool interception is unavailable.

## Script Responsibilities

The repo-level core should eventually provide these scripts:

### `scripts/guardrail-preflight.py`

Responsibilities:

- parse runtime input context
- resolve the active BA command
- resolve artifact paths
- evaluate index freshness
- emit a compact guardrail verdict
- write an allowlist manifest for the adapter

### `scripts/guardrail-build-excerpts.py`

Responsibilities:

- read the relevant index
- select anchors or sections for the requested slice
- extract compact markdown snippets from source artifacts
- write excerpt files under a temporary run directory

### `scripts/guardrail-audit.py`

Responsibilities:

- inspect runtime traces or adapter manifests
- compare actual reads against the allowlist
- validate that any broad reads carry an escalation reason
- emit pass, warn, or fail status

## Minimal Data Schemas

### Preflight Output

```json
{
  "status": "ok",
  "command": "stories",
  "resolved_slug": "warehouse-rfp",
  "resolved_module": "auth-flow",
  "guardrail_mode": "index-first",
  "indexes": {
    "backbone_index": {
      "state": "current",
      "path": "plans/warehouse-rfp-260331-1015/02_backbone/backbone-index.md",
      "source_artifact": "plans/warehouse-rfp-260331-1015/02_backbone/backbone.md"
    }
  },
  "allow_reads": [
    "core/contract.yaml",
    "core/contract-behavior.md",
    "plans/warehouse-rfp-260331-1015/02_backbone/backbone-index.md"
  ],
  "deny_reads": [
    "plans/warehouse-rfp-260331-1015/02_backbone/backbone.md"
  ],
  "excerpt_plan": "backbone_by_module",
  "canonical_state_summary": "",
  "canonical_next_command": "",
  "message": "GUARDRAIL: cmd=stories idx=backbone current=1 allow=backbone_index,excerpt deny=backbone_full"
}
```

### Preflight Block Output

```json
{
  "status": "block",
  "command": "package",
  "guardrail_mode": "index-first",
  "indexes": {
    "stories_index": {
      "state": "stale",
      "path": "plans/warehouse-rfp-260331-1015/03_modules/auth-flow/user-stories-index.md"
    }
  },
  "reason": "stories_index_stale",
  "refresh_command": "ba-start stories --slug warehouse-rfp --module auth-flow",
  "message": "GUARDRAIL_BLOCK: cmd=package reason=stories_index_stale refresh=ba-start stories --slug warehouse-rfp --module auth-flow"
}
```

### Audit Output

```json
{
  "status": "fail",
  "command": "frd",
  "guardrail_mode": "index-first",
  "actual_reads": [
    "core/contract.yaml",
    "core/contract-behavior.md",
    "plans/warehouse-rfp-260331-1015/02_backbone/backbone-index.md",
    "plans/warehouse-rfp-260331-1015/02_backbone/backbone.md"
  ],
  "violations": [
    {
      "type": "disallowed_read",
      "path": "plans/warehouse-rfp-260331-1015/02_backbone/backbone.md",
      "reason": "full_source_read_while_index_current"
    }
  ],
  "message": "GUARDRAIL_AUDIT_FAIL: cmd=frd violation=disallowed_read path=plans/warehouse-rfp-260331-1015/02_backbone/backbone.md"
}
```

## Parity Harness Follow-Up

The current parity harness validates normalized behavior envelopes. It should be expanded later to validate actual read behavior for guardrail-covered commands.

Recommended new fixtures:

1. `f16` — `frd` requires `backbone_index` first and blocks full backbone discovery reads
2. `f17` — `stories` requires `backbone_index` first and blocks full backbone discovery reads
3. `f18` — `package` uses index-first discovery and allows full reads only for the artifact currently being compiled
4. `f19` — `status` ignores `PROJECT-HOME.md` when dashboard state conflicts with canonical artifacts
5. `f20` — `next` recommends the canonical next step even when `PROJECT-HOME.md` says otherwise

## Non-Goals

- replacing the existing contract with runtime-specific policy
- turning `index` files into new source-of-truth artifacts
- forcing Antigravity to mimic unsupported native hooks in v1
- duplicating the full BA lifecycle policy into adapter prompts

## Acceptance Criteria

- Codex, Claude Code, and Antigravity all consume the same preflight verdict format
- `frd`, `stories`, `package`, `status`, and `next` have deterministic guardrail outcomes
- the adapter prompt addition stays compact
- broad reads require explicit escalation when a current index should have been sufficient
- `PROJECT-HOME.md` cannot override canonical artifact state in `status` or `next`
