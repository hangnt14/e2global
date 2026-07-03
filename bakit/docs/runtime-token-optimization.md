# Runtime-Neutral Token Optimization

BA-kit uses a runtime-neutral read order to keep Codex, Claude Code, and Antigravity aligned while reducing default input surface:

1. `core/contract.yaml`
2. `core/contract-behavior.md`
3. the command behavior shard listed in `behavior_shards.<command>`
4. the selected step file
5. templates and upstream artifacts only when the active step needs them

For the hard-enforcement layer over this read order, see [runtime-hard-guardrails.md](./runtime-hard-guardrails.md) and [runtime-index-quality-hardening.md](./runtime-index-quality-hardening.md).

## Command Read Bundles

| Command | Required behavior shard | Must not load by default |
| --- | --- | --- |
| intake | `core/behavior/intake.md` | memory shards, `log.md`, full raw source when cached summary exists |
| backbone | `core/behavior/backbone.md` | downstream module artifacts |
| impact | `core/behavior/impact.md` | `cold/` unless escalated |
| frd/stories | `core/behavior/module-authoring.md` | unrelated module shards |
| srs | `core/behavior/srs.md` | full backbone/stories when indexes are current |
| wireframes | `core/behavior/wireframes.md` | unrelated module shards |
| package/status/next | `core/behavior/package-status-next.md` | full source-of-truth artifacts when indexes are current |

## Output Contract Strategy

Runtime adapters and wrappers must emit the smallest packet that satisfies the action. Three modes are defined in `CLAUDE.md` Runtime Guardrails and mirrored in `GEMINI.md`:

- **probe** — block verdict, no-op, or clarification. Fields: `output_mode`, `status`, `command`, `resolved_slug`, `message`.
- **delta** — index-first action when a current index exists. Adds: `indexes.<name>.state`, `action_guardrail` (if present), `allow_reads`, `excerpt_path` (if built).
- **full** — escalation, broad read, or first-run with no index. Adds: `deny_reads`, `canonical_state_summary`, `canonical_next_command`, `refresh_command` (if block).

Rules:
- Default to `probe` for `status=block` and no-op responses.
- Default to `delta` for `status=ok` or `status=warn` when an index is current.
- Use `full` only when `READ_ESCALATION` is emitted or no current index exists.
- Receipt artifacts (`impact_receipt`, `options_receipt`, `index_validation_receipt`) are separate files; never embed their content in the runtime packet.
- The adapter script (`scripts/runtime-parity-adapter.sh`) emits compact structured packets using these modes; see that file for the implementation.

## Maintainer Notes

- Keep `core/contract.yaml` as the canonical data layer for paths, enums, thresholds, and shard mapping.
- Keep `core/contract-behavior.md` limited to policy that every command must read.
- Put command-specific read scope, gates, and exceptions in the relevant shard.
- Prefer deterministic scripts and `templates/manifest.json` routing metadata over long prose in step files.
- Keep runtime guardrail enforcement in deterministic scripts with compact verdict injection instead of re-sending long policy prose to the model.
- Keep producer-side index validation outside the routine runtime packet; ship only the resulting state and the compact per-action `backbone_index` reminder when a command is routeable from backbone.
- Update `core/token-budget.md` whenever an intentional instruction-surface change changes baselines.

## Acceptance Criteria

- Codex, Claude Code, and Antigravity point to the same contract and shard mapping.
- Runtime adapter files do not duplicate lifecycle policy already present in `core/`.
- `python scripts/check-token-budget.py .` passes on Windows without Bash.
- `scripts/check-token-budget.sh` remains usable on Unix-like environments.
- SRS and wireframe bundles are below the new command-scoped caps.
- No command requires loading unrelated memory shards or full source-of-truth artifacts when a current index exists.
- Guardrail adapters add only compact verdict strings plus excerpt references, not duplicated lifecycle policy blocks.
- Repeating the action-level `backbone_index` packet per relevant action stays cheaper than reopening full backbone context.
