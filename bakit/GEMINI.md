# BA-kit Instructions For Antigravity

## Canonical Sources

- `core/contract.yaml`
- `core/contract-behavior.md` plus the command shard in `core/behavior/` listed by `core/contract.yaml.behavior_shards`
- `skills/ba-start/SKILL.md`

For lifecycle work, read `contract.yaml`, then shared behavior, then only the selected command behavior shard and step file.

For non-trivial BA work, start from `skills/ba-start/SKILL.md` instead of improvising from the prompt alone.

## Automatic BA Routing

| User intent | Read this file | Then do |
| --- | --- | --- |
| Publishing to Notion | `skills/ba-notion/SKILL.md` | publish |
| Module claim/review/conflict/approve/integrate or GitHub handoff | `skills/ba-collab/SKILL.md` | collab |
| Checking status, completion, or missing artifacts | `skills/ba-start/SKILL.md` | run `status` |
| Continuing/resuming a project | `skills/ba-next/SKILL.md` | inspect and recommend |
| Asking what the next BA step should be | `skills/ba-next/SKILL.md` | inspect and recommend |
| Adding, changing, removing, or correcting a requirement or rule | `skills/ba-start/SKILL.md` | run `impact` |
| Naming a lifecycle step | `skills/ba-start/SKILL.md` | run that step |
| Providing raw requirements for a new engagement | `skills/ba-start/SKILL.md` | run lifecycle from intake |
| Other freeform BA requests | `skills/ba-do/SKILL.md` | route |

Prefer `impact` for ambiguous requirement corrections unless the user explicitly asks to update, overwrite, regenerate, or rerun a named artifact.

## Runtime Defaults

- Write BA deliverables in Vietnamese unless the user explicitly requests English.
- Default to `hybrid` mode for solo IT BA work.
- Persist memory in BA-kit artifacts, not runtime chat memory.
- Preserve HITL guarantees from the shared behavior contract and selected command shard.

## Conservative Guardrail Adapter

For `frd`, `stories`, `package`, `status`, and `next`, assume Antigravity is running behind
an external conservative adapter, not a native path-enforcement hook.

- If an injected guardrail packet is present, obey it as the runtime decision.
- Treat `GUARDRAIL_BLOCK` as a hard stop. Do not continue by discovery-reading broader source files.
- Treat `GUARDRAIL_WARN` as escalation mode only. Broad reads require an explicit
  `READ_ESCALATION: {command} read {path} due to {reason}.`
- Do not assume a newly generated index is trusted. `current` requires producer-side validation, including `validated_at` and `validated_by`, before the adapter should keep the run on the index-first lane.
- Prefer excerpt-only context generated outside the runtime over asking Antigravity to open
  full source-of-truth artifacts for discovery.
- Never claim that native path allowlists, denylists, or mid-run approval pauses exist unless
  the operator explicitly confirms richer hook support.
- If the adapter repeats an `ACTION_GUARDRAIL` packet for the current step, treat it as mandatory per-action re-entry through `backbone_index`.

### Portable-Core Packet Fields

When a packet includes preflight fields, treat these as the portable-core minimum:

- `status`
- `command`
- `resolved_slug`
- `resolved_module` when applicable
- `guardrail_mode`
- `indexes.<name>.state`
- `reason` for `block` or `warn`
- `refresh_command` for `block`
- `message`

Runtime-hint fields such as `allow_reads`, `deny_reads`, `excerpt_plan`, and excerpt-manifest
paths are guidance for the external adapter. They are not proof of native Antigravity
enforcement.
The adapter should prefer repeating that tiny packet on each relevant action instead of pasting broader backbone context again.

### Output Modes

Adapters emit one of three output modes. Use the smallest mode that satisfies the action:

| Mode | When to use | Required fields |
| --- | --- | --- |
| `probe` | block verdict, no-op, or clarification | `output_mode`, `status`, `command`, `resolved_slug`, `message` |
| `delta` | index-first action with current index | probe fields + `indexes.<name>.state`, `action_guardrail` (if present), `allow_reads`, `excerpt_path` (if built) |
| `full` | escalation, broad read, or no current index | delta fields + `deny_reads`, `canonical_state_summary`, `canonical_next_command`, `refresh_command` (if block) |

- `probe` is the default for `status=block`; do not add delta or full fields.
- `delta` is the default for `status=ok` or `status=warn` when an index is current.
- `full` is required only when `READ_ESCALATION` is emitted or no current index exists.
- See `CLAUDE.md` Runtime Guardrails for the canonical output-mode definition.

## Delivery Expectations

- Use `templates/` when a matching template exists.
- Keep final compiled HTML under `plans/{slug}-{date}/04_compiled/`.
- Keep active delegation trackers under `plans/{slug}-{date}/delegation/`.
- Prefer narrow handoff context to sub-agents instead of dumping full upstream documents.

## BA-Friendly Language

Accept Vietnamese first, then show internal step: tao du an -> intake; tiep tuc -> next; thay doi -> impact; handoff UI -> wireframes; ban giao -> package; trang thai -> status.

Collab NLP -> `ba-collab`; GitHub commit/push/PR/merge requires explicit approval.

For `status` and `next`, `PROJECT-HOME.md` may be consulted as a dashboard but must never
override canonical artifact state.
