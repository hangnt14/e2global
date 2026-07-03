# BA-kit Contract Behavior

Use this file as the shared runtime-neutral behavior layer for BA-kit.

- `core/contract.yaml` is canonical for paths, prerequisites, defaults, state enums, thresholds, and resolution sequences.
- This file is canonical for behavior that every command must follow.
- Command-specific policy lives in `core/behavior/` and is selected through `behavior_shards.<command>`.
- If this file and `core/contract.yaml` disagree on a literal path or threshold, trust `core/contract.yaml` for the value and this file for the policy intent.

## Required Read Order

1. Read `core/contract.yaml` for exact paths, prerequisites, defaults, states, command metadata, and `behavior_shards`.
2. Read `core/contract-behavior.md` for shared runtime-neutral policy.
3. Parse arguments and resolve the selected subcommand.
4. Read only the behavior shard(s) listed in `behavior_shards.<command>`.
5. Read only the matching step file.
6. Read templates and upstream artifacts only when the active step needs them.

## Shared Operating Rules

- Write BA deliverables in Vietnamese by default unless the user explicitly requests English.
- Use the defaults defined under `defaults.*`.
- Treat the backbone as the primary authoring source once it exists.
- Use exact artifact matching only. Never infer from closest-looking filenames or mtime.
- Keep module-scoped authoring inside `paths.module_root` and compiled output inside `paths.compiled_root`.
- Treat `paths.project_home` as the BA-facing dashboard. It is not a source of truth and must not override backbone, intake, or module artifacts.
- Runtime-local chat memory is not authoritative. Persist reusable project memory on disk.
- Before any file-system operation in a lifecycle step, ensure the shell CWD is the resolved project root (from `ba-kit resolve` output). CWD drift from a previous step (e.g., stranded inside a module subdirectory) must not carry into the current step. After `ba-kit resolve`, cd to the project root before evaluating prerequisites or reading/writing any artifact.

## Canonical Lifecycle Status Mapping

Use one lifecycle status vocabulary across shared behavior, command shards, templates, dashboards, and runtime adapters:

- `recommended`
- `in-progress`
- `completed`
- `skipped`
- `not-needed`

Do not introduce parallel labels such as `todo`, `doing`, or `done` in lifecycle state fields.

## Argument Parsing

Parse arguments before doing any work.

1. Read tokens left to right.
2. Extract `--slug <slug>`, `--date <date>`, `--module <module_slug>`, and `--mode <lite|hybrid|formal>` when present.
3. The first remaining lifecycle token is the subcommand: `intake`, `impact`, `options`, `backbone`, `frd`, `stories`, `srs`, `wireframes`, `package`, `status`, or `next`.
4. Friendly aliases may be translated before execution: continue/resume -> `next`, change assessment -> `impact`, option brainstorming/selection -> `options`, UI/ASCII wireframe refresh -> `srs`, handoff package -> `package`, status check -> `status`.
5. If no subcommand is present, run the full lifecycle from intake.
6. For `intake`, allow one free argument as the source path hint.
7. For `impact`, allow one free argument as the change file path hint.
8. For `options`, allow `--select <option-id>` and `--skip` as mutually exclusive controls.
9. For `frd`, `stories`, `srs`, and `wireframes`, enforce `commands.<name>.module_required`.
10. Reject unknown subcommands and unexpected free arguments instead of guessing.

For `options`, allow `--select <option-id>` and `--skip` as mutually exclusive control arguments.

## Natural-Language Routing

Infer `impact` when the user refers to an existing project set or downstream artifact and says a requirement, rule, actor, acceptance criterion, screen behavior, or scope item changed, was added, or was removed.

Also infer `impact` when exactly one project set can be resolved from disk and the user sends a bare correction statement without explicitly asking to update, overwrite, regenerate, or rerun a named artifact.

Do not mutate artifacts directly from a bare correction statement. Route to impact first. Collaboration intent routes to `ba-collab`; GitHub side effects require explicit approval after showing files and action plan.

## Resolution Rules

Use the resolution order from `resolution.*`.

### Slug

- Prefer explicit `--slug`.
- Otherwise inspect directories matching `patterns.project_dir` under `plans/`.
  Use `bash ls -d plans/*-*` or `find plans/ -type d` for directory discovery.
  The `Glob` tool only matches files — never use it for directory resolution.
- Ignore legacy report trees.
- If more than one slug exists, stop and ask.

### Date

- Prefer explicit `--date`.
- Otherwise derive the date from the resolved project directory name by applying `patterns.project_dir`.
  Same tool rule as Slug: use `bash ls -d` or `find -type d` for directory discovery, never `Glob`.
- If more than one dated set exists for the slug, stop and ask.

### Module

- For commands where `commands.<name>.module_required` is `true`, prefer explicit `--module`.
- If the project contains exactly one module directory, use it.
- If multiple module directories exist, stop and ask.
- Never infer a module from partial filename matches.

## Legacy Detection

- Treat anything under `legacy.roots` as out-of-contract for current lifecycle execution.
- If legacy artifacts exist but modular artifacts do not, stop and tell the user to migrate or rerun.
- Do not mix legacy and modular artifacts in one silent pass.

## Prerequisite Behavior

- Use `commands.<name>.requires` plus `paths.*` to resolve exact prerequisite files.
- If any required artifact is missing, print the exact missing path, the prior command to run, and stop.
- For `package`, require current canon sources and compile receipt. UI-backed modules must have ASCII coverage in `ascii-screen/` canon; external mockup state is not a package gate.

## Options Decision-Ledger Gate

Treat `paths.plan` as the execution decision ledger whenever intake seeds an `options status`, whether or not `paths.options_root` has been created yet.

- Intake may seed only `recommended` or `not-needed`.
- Recommendation strength may say `recommend` or `strongly recommend` in prose, but the execution ledger still stays on the canonical lifecycle statuses above.
- `options` must move the lifecycle to `in-progress`.
- `options` becomes `completed` once `selected option` is recorded.
- When the user explicitly bypasses optioning, `options` becomes `skipped`.
- `backbone` must not proceed while optioning remains `recommended` or `in-progress`.
- `backbone` may proceed only when the ledger records `not-needed`, `selected option` (`completed`), or `skipped`.
- `paths.options_root` is evidence that option artifacts exist; it must not be used as the condition that turns backbone gating on or off.
- `paths.plan` remains authoritative for the gate.

Stop when:

- the requested option file does not exist
- multiple options exist but no explicit selection/skip has been approved
- a selection request names an unknown option id

Shared read-scope reminder for the gate:

| command | must read | may read | must not read |
| --- | --- | --- | --- |
| backbone | contract.yaml, contract-behavior.md, paths.intake, paths.plan (when exists) | selected option file only when optioning is `completed`; paths.project_memory, paths.memory_index (nav only), paths.memory_hot_vocabulary, paths.memory_hot_decisions | log.md, cold/, warm/ |

## Overwrite Behavior

Before mutating `backbone`, `frd`, `stories`, `srs`, `package`, or any module artifact under `userstories/`, `usecases/`, `ascii-screen/`, or `srs/`:

1. Check whether the target output path already exists.
2. If it exists, print the exact path and ask whether to overwrite.
3. If overwrite is not explicitly approved, stop without mutating.

## Context-Loss Recovery

If exploration consumes context or the host truncates conversation history:

1. Reconstruct the active target from command, slug, date, optional module, and on-disk artifacts.
2. Continue from the next unresolved step when those values are still unambiguous.
3. Do not ask the user to restate the request merely because exploration consumed context.

## Routeable Backbone Re-entry

For any downstream action whose scope can be routed from the backbone, re-enter through `paths.backbone_index` first whenever that file exists.

- This applies on first execution, reruns, recovery after long sessions, and after host-side auto-compact or other context compression.
- Reconstruct module, feature, and trace scope from `paths.backbone_index` before opening targeted `paths.backbone` sections.
- Do not silently bypass `paths.backbone_index` by reopening the full backbone when an index-first route is available.
- If `paths.backbone_index` is missing or not trusted enough to route, stop and send the run back to backbone refresh/validation instead of guessing.

## Accepted-Scope Execution Lock

After the user explicitly approves a mutating rerun step:

- keep the current step locked for the rest of the run
- do not reopen generic discovery
- do not ask what to do next unless command, slug, date, module, or overwrite approval becomes genuinely ambiguous

## Token Discipline

- Read the selected step file, not the whole BA lifecycle.
- Read only the exact upstream artifacts needed by the active step.
- Use `templates/manifest.json` or CLI extraction helpers instead of loading full templates when only one group is needed.
- Reuse summaries and excerpts instead of rereading large raw sources when normalized artifacts already exist.
- For large source inputs, read `paths.source_summary` and `paths.source_chunk_index` before selecting chunk files.
- After `paths.backbone_index`, `paths.userstories_index`, or `paths.ascii_screen_index` exists, read the index first and open only targeted sections from the source artifact.
- Treat index files as navigators only; they do not replace source-of-truth artifacts.

### Internal Artifact Compactness

Artifact profile controls format and length:

- `user_facing`: deliverable or package output; write complete BA-readable content.
- `agent_facing`: navigator, packet, memory shard, or state summary; write compact tables/lists with IDs, paths, freshness, ownership, and route hints only.
- `machine_facing`: deterministic state or manifest; prefer JSON/YAML/NDJSON and avoid prose beyond stable labels.

### Wording-Layer Policy For User-Facing Artifacts

When generating `user_facing` artifacts, use reader-friendly Vietnamese labels for internal terms: source of truth -> tài liệu gốc, gate -> điều kiện tiến hành, canon -> tài liệu nguồn chuẩn, compile receipt -> biên bản tổng hợp, index -> chỉ mục điều hướng, backbone -> khung yêu cầu đã chốt, intake -> tiếp nhận yêu cầu, package snapshot -> gói bàn giao tại thời điểm, project memory -> bộ nhớ dự án, shared shell -> khung giao diện dùng chung, screen field contract -> đặc tả trường màn hình, qc-review -> kiểm tra chất lượng, scope lock -> chốt phạm vi. Keep raw state values, IDs, file paths, receipt filenames, option IDs, command names, and QC verdict fields literal. Do not apply to `agent_facing` or `machine_facing`.

## Index Validation Mandate [HARD — NON-NEGOTIABLE]

Every index artifact (`paths.backbone_index`, `paths.userstories_index`, `paths.usecases_index`, `paths.ascii_screen_index`) MUST pass producer-side validation before any downstream command treats it as `current`.

### Write-Time Rule

When a command writes or refreshes an index artifact:

1. **Generate** the index with `stale_status: unknown`, leave `validated_at` and `validated_by` blank.
2. **IMMEDIATELY run** `ba-kit validate-index --index-key <key> --slug <slug> --date <date> [--module <module>] --writeback` in the same execution step.
3. **If validation fails** (exit code != 0 or status != pass): stop execution. Do not proceed to downstream commands. Report the exact validation errors.
4. **If validation passes** (status: pass or warn): `stale_status` becomes `current`, `validated_at` and `validated_by` are set. Downstream commands may trust the index.
5. **SKIPPING validation is a contract violation.** No downstream command may route through an index with `stale_status: unknown` or `stale_status: stale`.

### PostToolUse Hook (Fallback)

A PostToolUse hook (`guardrail-index-validation-hook.sh`) runs automatically after every `Write|Edit` tool call inside a BA-kit plan directory. When it detects a write to an index file, it re-runs `validate-index-quality.py --writeback`. This ensures index freshness even if the agent's inline validation step is missed.

### Applicable Indexes

| Index Key | Written By | Module Required |
|-----------|-----------|-----------------|
| `backbone_index` | `ba-start backbone` | No |
| `userstories_index` | `ba-start stories` | Yes |
| `usecases_index` | `ba-start srs` | Yes |
| `ascii_screen_index` | `ba-start srs` | Yes |

### Enforcement Layers

| Layer | Mechanism | Triggers |
|-------|-----------|----------|
| Primary | Hard instruction in step file (`[BẮT BUỘC]`) | Agent executes inline during step |
| Fallback | PostToolUse hook (`guardrail-index-validation-hook.sh`) | Auto-fires after Write/Edit to index file |
| Consumer | Downstream guardrail (`guardrail-preflight.py`) | Blocks if `stale_status != current` |

If all three layers fail, the index stays `unknown`/`stale` and downstream commands stop with a stale-index block.

## Large Artifact Write Protocol

When generating artifacts that exceed about 150 lines, use incremental writes:

1. Write the skeleton first using the template structure.
2. Append group content sequentially into the correct section.
3. Confirm each append before moving on.
4. Never assemble and flush the full artifact in one large write.

## Runtime-Neutral HITL Contract

BA-kit is a playbook, not a UI product. Human-in-the-loop behavior is enforced through artifact routing and contract rules, not screen interactions.

- Core guarantees must stay identical across Claude Code, Codex, and Antigravity.
- A runtime adapter may translate command syntax or prompts, but it must preserve the same resolution, stop conditions, approval gates, and rerun rules.

## Backbone Authority Rule

Module artifacts are downstream from backbone. They must trace to backbone scope, actors, features, portals, rules, and terminology.

- If a module artifact conflicts with backbone, the module artifact is stale or wrong.
- New scope, actors, portals, or rules must route through `impact` and backbone refresh before module artifacts are updated.
- Every module-mutating command (`stories`, `srs`, impact approved writeback, `package`, `qc-review` remediation) must run backbone alignment validation before writing.
- Backbone alignment failure produces `BACKBONE_ALIGNMENT_FAIL: {scope}` and stops execution.
- Recovery: run `ba-start impact --slug <slug>` or refresh backbone, then rerun the blocked command.

Compiled deliverables never override source truth. Module source never overrides backbone. Backbone changes require impact/backbone route.

## Granular Artifact Intervention

Minimum intervention units include goal IDs, actor IDs, feature IDs, FR/NFR IDs, story IDs, acceptance criteria, use case IDs, screen IDs, rule/message codes, and glossary terms.

When a user change attaches to stable nodes, update only the narrowest source-of-truth artifact that owns those nodes. Do not rewrite the whole project set when a narrower rerun path is sufficient.

## Active Push-back And Fail-Closed Behavior

When uncertainty is material, stop and ask instead of filling the gap with plausible prose.

Material uncertainty includes ambiguous scope or module, conflicting terminology, unclear behavior or ownership, unclear navigation schema, and changes that could touch multiple source-of-truth layers.

Fail-closed rules:

- If a required fact is missing, mark it as an assumption or open question instead of presenting it as settled.
- If a downstream artifact would require guessing an upstream decision, stop and route back to the owning step.
- If a correction invalidates a persisted assumption, record the rejected assumption in project memory on the next approved mutating rerun.

Exception: skip the impact requirement for first-pass `backbone` creation when `paths.backbone` does not yet exist, and for explicitly approved `wording-only` reruns.

## Read Scope Contract

Every command has deterministic read scope. Load the selected command shard for its must-read, may-read, and must-not-read rules. Commands navigate summary -> index -> targeted shards.

### Index-First Navigation Rule

When shard memory exists:

1. Read `paths.memory_index` first to determine which shards are relevant.
2. Load only the shards the index routes to.
3. Never load the full shard tree when a targeted read is possible.

### Escalation Rule

A command may escalate its read scope only when the index routes to an additional shard, the user states an explicit audit/context need, or missing shard routing would otherwise require guessing.

Emit: `READ_ESCALATION: {command} read {path} due to {reason}.`

## Quality Gate Enforcement

After each mutable command completes, check `quality_gates` in `contract.yaml` for a gate with `trigger_after` matching the completed command.

If a matching gate exists:
1. Resolve platform from `--platform` flag or `defaults.platform`.
2. Load profile from `skills/qc-uc-review/profiles/{platform}.md`.
3. Invoke `qc-review` skill with the gate's `profile` and resolved `platform`.
4. Read verdict signal `{ verdict, score, platform, blockers, report_path }`.
5. Evaluate `block_on` condition from the gate config.
6. If `block_on` is true: enter remediation loop (defined in `core/behavior/qc-review.md`).
7. If `block_on` is false: log gate pass and proceed to next lifecycle step.

Gate enforcement is automatic — no user invocation needed. Gates fire AFTER the triggering command completes; they do not block the command itself.

### QC Review Argument Parsing

When `qc-review` is invoked directly or via gate:
- `--platform <mobile|web|api>` — override `defaults.platform` for this run
- `--profile <full-10ka>` — override the runtime gate profile for this run
- Legacy/manual-only profiles `completeness-clarity-only` and `cross-artifact-consistency` may still be used for ad hoc operator review, but they are not referenced by `quality_gates`
- `--skip-gate` — bypass QC gate enforcement; requires explicit user confirmation before proceeding

### Gate Profiles

| Profile | Scope |
|---|---|
| `full-10ka` | Runtime gate profile. All 10 KAs, full scoring rubric. |
| `completeness-clarity-only` | Legacy/manual-only narrow review of KA #1–#4. Not used by `quality_gates`. |
| `cross-artifact-consistency` | Legacy/manual-only blocker scan. Not used by `quality_gates`. |

## Reverse Mode Behavior

Reverse mode is a first-class lane for reconstructing as-built documentation from existing code and artifacts. It operates under stricter read and truth constraints than the forward lifecycle.

### Snapshot Truth

- All reverse claims are valid only against `documented_commit` recorded in `paths.reverse_baseline_lock`.
- `documented_commit` is the git commit hash captured at the time of the initial `reverse` scan.
- Any claim that cannot be traced to a file read during the baseline scan must be marked as an assumption, not a finding.
- After a `reverse_refresh`, all prior evidence entries must be re-validated against the new commit before being treated as current.

### As-Built vs Future-State Separation

- Never mix as-built findings and future-state requirements in the same artifact.
- `as_built_drift`: behavior that exists in code but is absent or contradicts the documented baseline.
- `future_state_request`: a desired behavior not yet implemented — routes to the forward lifecycle (backbone, FRD, stories).
- `mixed_change`: a change that contains both as-built and future-state elements — must be split before promotion.
- `reverse_impact` classifies each pending item into one of these three lanes before any promotion is allowed.

### No-Broad-Read Rule

- After the initial baseline scan (`reverse` command), only files listed in `paths.reverse_read_manifest` may be re-read without escalation.
- Reading any file not in the manifest requires emitting: `READ_ESCALATION: {command} read {path} due to {reason}.`
- The baseline scan itself may read broadly to build the manifest; subsequent commands must use the manifest as the allowlist.
- `paths.reverse_focus_excerpts` contains pre-extracted content for allowlisted focus areas — prefer excerpts over reopening full source files.

### Source-Only Constraint (v1)

- Reverse mode v1 operates on static source files only: code, config, docs, and schema files committed to the repository.
- No runtime probes, no application execution, no live endpoint verification, no database queries.
- If a claim requires runtime verification, mark it as `unverifiable_in_v1` in the evidence ledger.

### Reverse Artifact Classification

- `paths.reverse_baseline_lock` — `machine_facing`: JSON record of `documented_commit`, `scan_timestamp`, `focus_selection`, and `locked_files`. Not a source of truth.
- `paths.reverse_index` — `agent_facing`: navigator index of scanned artifacts and their evidence status. Not a source of truth.
- `paths.reverse_focus_excerpts` — `agent_facing`: focused excerpts per selected focus area. Not a source of truth.
- `paths.reverse_evidence_ledger` — `agent_facing`: trace records linking file evidence to promoted claims. Not a source of truth.
- `paths.reverse_drift_state` — `machine_facing`: current drift classification vs `documented_commit`. Not a source of truth.
- `paths.reverse_read_manifest` — `machine_facing`: audit log of all files read during reverse scan. Not a source of truth.
- None of the above are in `source_of_truth_order`. Canonical artifacts (backbone, SRS, FRD) remain the source of truth.

### Promotion Gate

- Evidence may only be promoted to canonical artifacts via `reverse_promote`.
- `reverse_promote` requires explicit user approval per promotion batch.
- Only `as_built_drift` items may be promoted directly to backbone or SRS.
- `future_state_request` items must be routed through the forward lifecycle (backbone → FRD → stories).
- `mixed_change` items must be split by `reverse_impact` before promotion is allowed.

### Argument Parsing for Reverse Commands

- `reverse` — optional `--focus <area>` to scope the baseline scan; optional `--commit <hash>` to pin `documented_commit`.
- `reverse status` — no additional arguments.
- `reverse refresh` — optional `--commit <hash>` to update `documented_commit`.
- `reverse promote` — requires `--evidence-ids <id,...>` to identify the ledger entries to promote.
- `reverse impact` — optional `--evidence-ids <id,...>` to classify a subset; defaults to all unclassified entries.
