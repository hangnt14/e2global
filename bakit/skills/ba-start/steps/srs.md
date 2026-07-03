# BA Start Step - SRS Router

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md`
- `core/behavior/srs.md`

## Governance Gate

Before mutating any SRS artifact:
1. **Skip this gate for first-pass creation** (when `paths.srs_spec` and `paths.srs` do not yet exist).
2. For reruns (artifacts already exist): verify write authority and locate the active impact receipt at `paths.impact_receipt`. If no active receipt exists and `change_class` is not `wording-only`, emit `GOVERNANCE_BLOCK: impact_receipt missing or invalidated` and stop.
3. If either check fails on a rerun: emit `GOVERNANCE_BLOCK: {reason}` and stop.
4. After mutation completes: offer to file the change into canonical memory using `templates/project-memory-fileback-record-template.md`.

## Backbone Authority Gate

Before writing any SRS source artifact, run backbone alignment validation per `core/behavior/srs.md`. Misalignment produces `BACKBONE_ALIGNMENT_FAIL: {scope}` and stops execution.

## Scope

Run Steps 8-11 only. This path stays split so SRS execution can load only the instructions needed for the current pass.

## Read Order

1. Read this router for SRS preflight and orchestration.
2. Read [srs-core.md](./srs-core.md) for source set generation (spec, usecases, ascii-screen).
3. Read [srs-wireframes.md](./srs-wireframes.md) for ASCII wireframe gates and DESIGN.md gating.
4. Read [srs-assembly.md](./srs-assembly.md) for partial compile and receipt generation.

## Prerequisites

- Resolve slug, date, and module using `ba-kit resolve --slug <slug> [--module <module>]`.
  The CLI uses `find -type d` internally for correct directory discovery.
  Do not use `Glob` — it only matches files, not directories.
- **[CWD GATE]** After resolve, verify shell CWD is the project root. Run `cd "$(ba-kit resolve --slug <slug> --date <date> [--module <module>] 2>/dev/null | awk '/^Project root:/ {print $3}')"` if CWD is not already there. `paths.design_doc` (`designs/{slug}/DESIGN.md`) and `paths.shared_shell_contract` (`plans/{slug}-{date}/02_backbone/shared-shell-contract.md`) are relative to the project root — a stale CWD from a previous step (e.g., stranded in `userstories/`) will cause false `DESIGN_GAP` failures.
- Require `paths.backbone`, `paths.backbone_index`, and `paths.userstories_index`.
- For UI-backed modules: require `paths.design_doc` and `paths.shared_shell_contract` (created by Lead BA during backbone). If missing, emit `DESIGN_GAP` and stop — do NOT create them from SRS.
- If a required artifact is missing, print the exact missing path, tell the user which subcommand to run first, and stop.
- Run preflight from indexes first:
  - If `ba-kit guardrail --command srs --slug <slug> --date <date> --module <module>` returns `status=block`, surface the block message and stop
  - Otherwise use `ALLOW_READS` for file discovery
- read only targeted backbone/story sections, optional module FRD, and `paths.plan` when it exists.
- In reverse mode, gate on a valid reverse baseline, current drift state, and traceable reverse evidence; do not require `paths.design_doc`.

## Outputs

- `paths.srs_spec` — FR/NFR/business rules/API/data constraints
- `paths.srs_flows` — module/system flows (not UC-level diagrams)
- `paths.srs_states` — module state registry
- `paths.srs_erd` — business data model when justified
- `paths.usecases_index` + `paths.usecase_item` files — use case canon
- `paths.usecase_diagrams` — UC-specific diagrams
- `paths.ascii_screen_index` + `paths.ascii_screen_item` files — screen canon with mandatory ASCII wireframes
- `paths.srs` — compiled output only (requested-scope compile)
- `paths.srs_compile_receipt` — receipt with compile scope and source hashes
- `paths.screen_field_contract` — normalized machine-facing screen truth

Do NOT create `srs-index.md`, `screens/`, `data/`, `flows/`, or `srs-groups/`.
Do NOT create or modify `paths.design_doc` or `paths.shared_shell_contract` — these are system-level artifacts owned by Lead BA. Exception: Module BA may add nav items to an existing portal with user confirmation (see `srs-wireframes.md` Step 8.2 L2).

Treat generated index artifacts as `agent_facing`; keep them compact.
When `paths.usecases_index` or `paths.ascii_screen_index` is written or refreshed, keep `stale_status: unknown`, leave `validated_at` and `validated_by` blank.

**[BẮT BUỘC — KHÔNG ĐƯỢC BỎ QUA]** Ngay sau khi write index, PHẢI chạy cả hai:

```bash
ba-kit validate-index --index-key usecases_index --slug <slug> --date <date> --module <module> --writeback
ba-kit validate-index --index-key ascii_screen_index --slug <slug> --date <date> --module <module> --writeback
```

- Nếu cả hai PASS hoặc WARN: `stale_status` được promote lên `current`. Có thể tiếp tục compile SRS.
- Nếu bất kỳ validation nào FAIL: DỪNG. Không được compile `srs.md` hay chạy downstream command. Sửa index rồi chạy lại validator.
- PostToolUse hook (`guardrail-index-validation-hook.sh`) sẽ tự chạy lại validator như fallback, nhưng agent PHẢI gọi inline trước.

Không được bỏ qua bước này với lý do "để sau", "index nhỏ", hay "sẽ validate sau".

Treat `paths.srs` as the compiled, reader-facing deliverable. Direct edits to `paths.srs` are blocked by default; canonical edits belong in the module source files and must compile back into `paths.srs` via the partial compile routine.

## Partial Compile Semantics

Parse `--scope` flag or user request to determine compile scope:
- `full` — compile all source files
- `spec` — compile `srs/spec.md` only
- `usecases` — compile `usecases/index.md` + selected UC files + diagrams
- `screens` — compile `ascii-screen/index.md` + selected screen files
- `flows` — compile `srs/flows.md`
- `states` — compile `srs/states.md`
- `erd` — compile `srs/erd.md`
- `mixed` — compile user-requested combination

Receipt must define `compile_scope`, `requested_sections`, `included_sources`, `excluded_sources`, and `source_hashes`. Source changes outside requested scope do not mark receipt stale.

## Execution Order

```text
Backbone alignment gate
Step 8   -> srs-core.md  (generate source set)
Step 8.2 -> srs-wireframes.md  (DESIGN.md coverage verification gate)
Step 10  -> srs-wireframes.md  (screen field contract)
Step 10.1 + 11 -> srs-assembly.md  (partial compile, receipt)
```
