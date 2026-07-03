# BA-kit Instructions For Claude Code

## Canonical Sources

- `core/contract.yaml`
- `core/contract-behavior.md` plus the command shard in `core/behavior/` listed by `core/contract.yaml.behavior_shards`
- `skills/ba-start/SKILL.md` - lifecycle stub that dispatches into the active step file

For lifecycle work, read `contract.yaml`, then shared behavior, then only the selected command behavior shard and step file.

For non-trivial BA work, start from `skills/ba-start/SKILL.md` instead of improvising from the prompt alone.

## Core Defaults

- Write BA deliverables in Vietnamese unless the user explicitly requests English.
- Default to `hybrid` mode for solo IT BA work.
- Persist project memory on disk; do not rely on Claude chat memory as the system of record.
- Apply runtime-neutral HITL behavior from `core/contract-behavior.md` and the selected shard.

## Runtime Guardrails

If a wrapper or operator supplies a guardrail preflight packet for `frd`, `stories`, `package`, `status`, or `next`, treat that packet as the authoritative runtime constraint.

- Honor `status`, `message`, `guardrail_mode`, `allow_reads`, `deny_reads`, `indexes`, and `refresh_command` exactly as supplied.
- If `status=block`, stop before lifecycle work and surface `refresh_command` instead of proceeding.
- Treat an index as truly current only when the packet already reflects producer-side validation; do not assume a freshly generated index is trusted before `validated_at` and `validated_by` exist.
- When the packet says an index is current, use only the allowlisted files for discovery and prefer any generated excerpt files over reopening the full source artifact.
- Do not discovery-read a full artifact that appears in `deny_reads` unless you first emit `READ_ESCALATION: {command} read {path} due to {reason}.`
- If an `action_guardrail` or `ACTION_GUARDRAIL` reminder is present, obey it on that action even if earlier turns already mentioned the same backbone route.
- For `status` and `next`, `PROJECT-HOME.md` may help explain state to the user but must not override canonical artifact resolution.
- Keep the runtime payload compact; do not ask for the full guardrail policy again when the packet already supplies the verdict and exact path hints.

### Output Modes

Adapters and wrappers emit one of three output modes. Use the smallest mode that satisfies the action:

| Mode | When to use | Required fields |
| --- | --- | --- |
| `probe` | no-op, clarification, or block verdict | `output_mode`, `status`, `command`, `resolved_slug`, `message` |
| `delta` | index-first action with changed state | probe fields + `indexes.<name>.state`, `action_guardrail` (if present), `allow_reads`, `excerpt_path` (if built) |
| `full` | escalation, broad read, or first-run with no index | delta fields + `deny_reads`, `canonical_state_summary`, `canonical_next_command`, `refresh_command` (if block) |

Rules:
- `probe` is the default for `status=block` and no-op responses; do not add delta or full fields.
- `delta` is the default for `status=ok` or `status=warn` when an index is current.
- `full` is required only when `READ_ESCALATION` is emitted or no current index exists.
- Receipt contracts (`impact_receipt`, `options_receipt`, `index_validation_receipt`) are separate artifacts; do not embed their content in the runtime packet.

## Artifact Model

- Project root: `plans/{slug}-{date}/`
- Project Home: `PROJECT-HOME.md`
- Intake and plan: `01_intake/`
- Backbone and memory: `02_backbone/`
- Module artifacts: `03_modules/{module_slug}/`
- Compiled HTML: `04_compiled/`
- Delegation and collaboration: `delegation/`, `COLLAB-HOME.md`, `MODULE-HOME.md`

## Context Budget Enforcement [NON-NEGOTIABLE]

Every oversized tool output is cached in prompt context and re-loaded on EVERY subsequent turn. The guardrail hooks enforce these rules at two layers:

- **PreToolUse (Read)**: Blocks Read calls on files >10kB without `offset`+`limit`. Warns on files >5kB. Detects re-reads of same file within session.
- **PostToolUse (Bash|Read|Grep)**: Warns on outputs >5kB. Strong warning >8kB.
- **Stop**: End-of-session audit reports total context waste from oversized outputs.

### Tool Selection Rules

| Instead of | Use | Reason |
|---|---|---|
| `find ... -type f` (Bash) | `Glob` with specific patterns | Glob returns file paths only, no noise |
| `cat <file>` (Bash) | `Read <file>` | Read supports offset/limit for large files |
| `grep -r <pattern>` (Bash) | `Grep` with `head_limit` | Grep tool is optimized, supports filtering |
| `ls -R` or `tree` (Bash) | `Glob **/*` | Glob gives structured results |

### Output Limiting Rules [HARD]

1. **Read**: Always use `offset` + `limit` on files >200 lines. Read TOC/frontmatter first (~50 lines), then target specific line ranges. Files >10kB without limit will be BLOCKED by PreToolUse hook.
2. **Grep**: Always use `head_limit` when `output_mode=content`. Default to `files_with_matches` first, then narrow to content.
3. **Bash**: Pipe through `head -N` or `tail -N` when output size is uncertain. Never return raw `find`, `ls -R`, or `cat` output without limiting.
4. **Prefer dedicated tools**: Use Glob over `find`/`ls`. Use Read over `cat`. Use Grep over `grep`/`rg`.
5. **Full-file reads**: Only Read an entire file when it's <200 lines AND you need the full content. If any doubt, read in sections.

### Re-Read Prevention [HARD]

- Do NOT re-read a file you already read in this session. Reference prior read by line numbers instead.
- If you need a different section, use `offset`+`limit` to target it specifically.
- The PreToolUse hook tracks all reads and warns on re-reads.

### Thresholds

- **PreToolUse WARN**: >5kB file with no offset/limit — warning injected, read proceeds
- **PreToolUse BLOCK**: >10kB file with no offset/limit — Read is BLOCKED, must retry with offset+limit
- **PostToolUse WARN**: >5kB tool output (~1.2k tokens) — context warning injected
- **PostToolUse CRITICAL**: >8kB tool output (~2k tokens) — strong warning with repeat counter

### Bypass

If full-file read is genuinely required and blocked by PreToolUse:
```
Read file_path with limit=0 to bypass the preflight guard.
```

### Escalation

If a legitimately large read outside BA-kit context is necessary, emit:
```
READ_ESCALATION: {command} read {path} due to {reason}.
```

## Delegation

Use agent roles under `agents/` when delegation improves quality or throughput.

- `requirements-engineer` for backbone, FRD, stories, and selective SRS content
- `ui-ux-designer` for wireframe constraint packs and manual handoff checklists
- `ba-documentation-manager` for validation, quality review, and packaging
- `ba-researcher` for domain research

Pass narrow packets: exact path, write scope, trace IDs, and targeted excerpts.

## BA-Friendly UX

Use `PROJECT-HOME.md` to resume. Lead with friendly labels, then show commands: tao du an moi -> intake; tiep tuc -> next; thay doi -> impact; handoff UI -> wireframes; ban giao -> package.

Route module collaboration NLP to `ba-collab`. Commit/push/PR/merge require explicit approval.

## Source Repo Fix Rule [CRITICAL]

When fixing bugs or implementing features in THIS repository (BA-kit source), apply changes ONLY to files under this repo root. Do NOT apply fixes to installed locations:
- `~/.claude/ba-kit/` — installed by `install.sh`
- `~/.local/bin/ba-kit` — installed by `install.sh`
- `~/.codex/ba-kit/` — installed by `scripts/install-codex-ba-kit.sh`
- `~/.gemini/antigravity-cli/ba-kit/` — installed by `scripts/install-antigravity-ba-kit.sh`

Installation pipeline:
- `install.sh` → copies `scripts/ba-kit` → `~/.local/bin/ba-kit`
- `install.sh` → calls `scripts/install-claude-code-ba-kit.sh` → copies `scripts/*.py` → `~/.claude/ba-kit/scripts/`, writes hooks to `~/.claude/ba-kit/hooks/`
- Templates: `install.sh:164` → copies `templates/*` → `~/.claude/templates/`

User runs `bash install.sh` to apply source fixes to their installation.
