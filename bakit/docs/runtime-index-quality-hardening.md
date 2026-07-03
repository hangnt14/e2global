# Runtime Index Quality Hardening

This document defines the producer-side contract for BA index artifacts and the action-level runtime rule that keeps backbone-backed work on the index-first lane across Codex, Claude Code, and Antigravity.

## Goal

BA-kit already has consumer-side guardrails that fail closed when indexes are stale, contradictory, or not extractable enough for downstream work.

This document closes the remaining gap:

- index generation must not mark an index as trusted by default
- only deterministic validation may promote an index to `current`
- when a downstream action can route from `backbone_index`, that action must re-enter through `backbone_index` first even after long sessions or host auto-compact

## Affected Indexes

- `paths.backbone_index`
- `paths.stories_index`
- `paths.srs_index`

## Producer Contract

### Issuance Rule

When an index is first generated or refreshed:

- write `stale_status: unknown`
- leave `validated_at` blank
- leave `validated_by` blank
- do not treat the index as trusted for downstream routing yet

Only `scripts/validate-index-quality.py` may promote the index to `stale_status: current`.

### Minimum Validation Outcome

The validator must prove:

1. metadata is structurally valid
2. source path and source hash match the real source artifact
3. required table columns exist
4. required row fields are present
5. route targets resolve to real headings or group files
6. indexed IDs cover the source IDs required for that index type

If those checks fail, the suggested status must stay non-current.

## Validation States

| State | Meaning | Runtime Consequence |
| --- | --- | --- |
| `unknown` | index exists but has not yet passed producer-side validation | downstream guardrails must not trust it as current |
| `stale` | index failed validation or no longer matches source coverage/hash | downstream guardrails must block or require explicit escalation |
| `current` | index passed producer-side validation and consumer-side freshness rules | downstream commands may stay on the index-first lane |

## Action-Level Backbone Re-entry

Producer-side validation is not enough on its own. A second rule applies at runtime:

- if a downstream action can route from `backbone_index`, it must consult `backbone_index` first
- this applies on first execution, reruns, recovery after long sessions, and after host-side auto-compact or other context compression
- wrappers and operator packets must re-send the compact index-first reminder per relevant action instead of assuming prior conversation context is still reliable

Portable compact packet shape:

```json
{
  "required": true,
  "navigation_source": "backbone_index",
  "packet_scope": "per-action",
  "reason": "consult backbone_index before broader backbone reads"
}
```

## Runtime Support

### Codex

- stage `validate-index-quality.py` into `~/.codex/ba-kit/scripts/`
- run validator after backbone/stories/SRS index generation
- run `guardrail-preflight.py` again for each downstream action covered by hard guardrails

### Claude Code

- consume the same compact packet fields
- treat each relevant action as a fresh index-first decision point
- do not rely on prior session memory to skip `backbone_index`

### Antigravity

- run validator and preflight outside the runtime
- inject only compact verdicts plus excerpts
- restate the per-action `backbone_index` packet whenever the next action is routeable from backbone

## Token Discipline

The action-level reminder must stay compact enough that repeating it per action is still cheaper than reopening full backbone context.

Target strategy:

- ship one short packet with `navigation_source`, `packet_scope`, and `reason`
- prefer excerpt paths or compact summaries over full backbone prose
- keep the validator report machine-readable and out of normal runtime prompts unless a failure must be surfaced

## Recommended Commands

Validate a backbone index after generation:

```bash
python3 scripts/validate-index-quality.py \
  --repo . \
  --index-key backbone_index \
  --slug <slug> \
  --date <date> \
  --writeback
```

Validate a stories index after generation:

```bash
python3 scripts/validate-index-quality.py \
  --repo . \
  --index-key stories_index \
  --slug <slug> \
  --date <date> \
  --module <module> \
  --writeback
```

Validate an SRS index after generation:

```bash
python3 scripts/validate-index-quality.py \
  --repo . \
  --index-key srs_index \
  --slug <slug> \
  --date <date> \
  --module <module> \
  --writeback
```
