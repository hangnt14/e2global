# Backbone Behavior

## Read Scope

- Must read for `options`: `core/contract.yaml`, `core/contract-behavior.md`, `paths.intake`, and `paths.plan` when present.
- Must read for `backbone`: `core/contract.yaml`, `core/contract-behavior.md`, `paths.intake`, and `paths.plan` when present.
- May read: selected option file only when optioning is completed, `paths.project_memory`, `paths.memory_index` as navigator, hot vocabulary and decisions shards.
- Must not read: `log.md`, `cold/`, unrelated `warm/` shards, downstream module artifacts.

## Options Decision-Ledger Gate

Treat `paths.plan` as the execution decision ledger whenever intake seeds options status, whether or not `paths.options_root` exists.

- Intake may seed only `recommended` or `not-needed`.
- Recommendation strength stays in prose, not a parallel enum.
- `options` moves lifecycle to `in-progress`, then `completed` when `selected option` is recorded, or `skipped` when the user explicitly bypasses optioning.
- `backbone` must stop when ledger status is `recommended` or `in-progress`.
- `backbone` may proceed only when the ledger records `not-needed`, `selected option` (`completed`), or `skipped`.
- `paths.options_root` is evidence that option artifacts exist; it does not control whether backbone gating applies.
- For `options`, `--select <option-id>` and `--skip` are mutually exclusive.

Stop when the requested option file does not exist, multiple options exist without approved selection/skip, or a selection names an unknown option id.

## Backbone And Memory

- Backbone creation is the first source-of-truth consolidation after intake and accepted options.
- First-pass backbone creation may skip impact/governance pre-mutation checks because no accepted backbone exists yet.
- Refresh `paths.backbone_index` after backbone creation or approved rerun.
- **[BẮT BUỘC]** Immediately after writing `paths.backbone_index`, run `ba-kit validate-index --index-key backbone_index --slug <slug> --date <date> --writeback`. If validation fails, stop. Do not proceed to downstream commands. The PostToolUse hook serves as fallback, but this inline call is the primary enforcement.
- **Always create shared registries** `paths.common_rules`, `paths.message_list`, and `paths.shared_rule_message_index` during backbone. These are system-level artifacts that module screens and contracts reference by code (`CR-*`, `MSG-*`).
  - Populate `paths.common_rules` with initial CR-* codes derived from backbone scope.
  - Populate `paths.message_list` with initial MSG-* codes for common messages.
  - Generate `paths.shared_rule_message_index` by running the validator with `--write-index`.
- **When UI-backed scope exists:** create `paths.design_doc`, `paths.shared_shell_contract`, and `paths.shared_shell_index` during backbone. These are system-level artifacts owned by Lead BA.
  - `paths.design_doc` must cover ALL portals from the backbone Portal Matrix, not just one module.
  - `paths.shared_shell_contract` must declare every nav schema, shell variant, and layout variant used by any portal.
  - Module BAs are PROHIBITED from creating new portals, new nav schemas, new shell variants, or new shared components in these files.
  - Module BAs MAY add menu items to an existing nav schema with explicit user confirmation, then flag in review packet.
  - If a module needs a portal not yet in DESIGN.md or shared-shell-contract.md, escalate to Lead BA via `impact`.
- **UI Library Selection Gate:** After DESIGN.md is persisted and design direction approved, backbone MUST prompt user to select a concrete UI library (name + version) before creating `paths.control_type_library`. Supports two paths:
  - **Single-run (interactive):** User selects library via prompt → backbone writes selection into DESIGN.md and continues to create `paths.control_type_library` in the same run.
  - **Two-run (research):** User defers selection → backbone stops, user fills DESIGN.md manually, reruns backbone later.
  - If DESIGN.md has no library selection (TBD or empty) → prompt user via `AskUserQuestion` with library suggestions + `none` + "Tôi cần thời gian research".
  - If user picks a library → write it into DESIGN.md Section 10, gate passed, create control_type_library with that baseline.
  - If user picks "none" → write `none` into DESIGN.md, gate passed, create control_type_library with baseline = `none`.
  - If user defers → stop with instructions to fill DESIGN.md manually or rerun backbone.
  - If DESIGN.md already has library = `none` → gate passed, create control_type_library with baseline = `none`.
  - If DESIGN.md already has concrete library name + version → gate passed, create control_type_library with that baseline.
- Initialize or refresh project memory from accepted intake/backbone decisions.
- Compact memory (`paths.project_memory`) stores stable vocabulary, approved decisions, accepted assumptions, rejected assumptions, corrections, and push-back triggers.
- Shard memory is optional. If present, `paths.memory_index` is a bounded navigator and must not become a second monolith.
- `log.md` is optional chronology support and excluded from normal command reads.
- `cold/` is never loaded by default.
