# BA Start Step - Stories

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md`

## Memory Read Scope

- **Must read:** `core/contract.yaml`, `core/contract-behavior.md`, `paths.backbone_index`
- **May read:** targeted `paths.backbone` sections, `paths.plan`, `paths.frd` (when exists), `paths.project_memory` or (`paths.memory_hot_vocabulary` + `paths.memory_hot_decisions`) when shard mode is active
- **Must NOT read:** `log.md`, `cold/`, `warm/` shards, unrelated module shards, `user-stories.md`, `user-stories-index.md`

## Backbone Authority Gate

Before writing any story file, validate backbone alignment:
- Story actor, goal, feature, and priority must trace to backbone module scope.
- If alignment fails: emit `BACKBONE_ALIGNMENT_FAIL: story_scope` and stop.
- Recovery: run `ba-start impact --slug <slug>` or refresh backbone, then rerun.

## Governance Gate

Before mutating this artifact:
1. **Skip this gate for first-pass creation** (when `paths.userstories_root` does not yet exist).
2. For reruns (artifacts already exist): verify write authority and locate the active impact receipt at `paths.impact_receipt`. If no active receipt exists and `change_class` is not `wording-only`, emit `GOVERNANCE_BLOCK: impact_receipt missing or invalidated` and stop.
3. If either check fails on a rerun: emit `GOVERNANCE_BLOCK: {reason}` and stop.
4. After mutation completes: offer to file the change into canonical memory using `templates/project-memory-fileback-record-template.md`.

## Scope

Run Step 7 only.

## Prerequisites

- Resolve slug, date, and module using `ba-kit resolve --slug <slug> [--module <module>]`.
  The CLI uses `find -type d` internally for correct directory discovery.
  Do not use `Glob` — it only matches files, not directories.
- Require `paths.backbone`.
- Prefer `paths.backbone_index` for routing. If it is missing and the backbone is large, stop and ask to refresh the index.
- If backbone is missing, print the exact missing path and stop.
- Run a narrow stories preflight:
  - If `ba-kit guardrail --command stories --slug <slug> --date <date> --module <module>` returns `status=block`, surface the block message and stop
  - Otherwise use `ALLOW_READS` for file discovery
  - read `paths.backbone_index` first
  - read only targeted `paths.backbone` sections
  - read `paths.plan` only when it adds needed scope context
  - read `paths.frd` only when it already exists and adds needed vocabulary or workflow structure
  - do not scan unrelated module folders once slug, date, and module are resolved

## Output

- `paths.userstories_index` — folder index navigator
- `paths.userstory_item` — one file per story (`userstories/us-{slug}.md`)

Do NOT create `user-stories.md` or `user-stories-index.md`.

## Step 7 - Produce user stories

Generate Agile user stories from the backbone feature map and FR draft.

Use templates:
- `templates/userstory-item-template.md` for each story file
- `templates/userstories-index-template.md` for the index

Generation rules:
- Derive one story per coherent user intent — not per acceptance criterion.
- One acceptance criteria set per story.
- Stable slug from normalized story title (kebab-case, ASCII, max 40 chars).
- No bundled behaviors — one intent per story statement.
- Story actor, goal, feature, and priority must trace to backbone module scope.

Story item fields:
- `story_id`: `US-{module}-{NNN}` (zero-padded, sequential within module)
- `slug`: stable kebab-case from story title
- `actor`: from backbone actor registry
- `priority`: P0 / P1 / P2 from backbone feature priority
- `source_backbone_ids`: backbone feature/scope IDs this story traces to
- `linked_usecases`: populated by SRS step
- `linked_screens`: populated by SRS step

Index row fields:
- `story_id`, `file`, `actor`, `feature_or_fr`, `acceptance_criteria_count`, `linked_usecases`, `linked_screens`, `source_backbone_ids`, `stale_status`

Execution rules:
- Start from `paths.backbone_index`, then the exact targeted backbone sections, plus the exact plan path when genuinely needed.
- Pull the FRD only when it already exists or the current mode requires it.
- If the user already confirmed that story generation should proceed, continue from the resolved backbone instead of reopening discovery.
- Treat generated index artifacts as `agent_facing`; keep them compact and do not duplicate source-of-truth requirement text.

After generating all story item files, create or refresh `paths.userstories_index` using `templates/userstories-index-template.md`. Keep it as a navigator over stories, acceptance-criteria counts, screen IDs, and source headings.

Generate `paths.userstories_index` with `stale_status: unknown`, leave `validated_at` and `validated_by` blank.

**[BẮT BUỘC — KHÔNG ĐƯỢC BỎ QUA]** Ngay sau khi write `userstories/index.md`, PHẢI chạy:

```bash
ba-kit validate-index --index-key userstories_index --slug <slug> --date <date> --module <module> --writeback
```

- Nếu validation PASS hoặc WARN: `stale_status` được promote lên `current`. Có thể tiếp tục sang SRS.
- Nếu validation FAIL: DỪNG. Không được chạy `srs` hay bất kỳ downstream command nào. Sửa index rồi chạy lại validator.
- PostToolUse hook (`guardrail-index-validation-hook.sh`) sẽ tự chạy lại validator như fallback, nhưng agent PHẢI gọi inline trước.

Không được bỏ qua bước này với lý do "để sau", "index nhỏ", hay "sẽ validate sau".

**[CWD RESTORE — MANDATORY]** After stories generation and validation complete, restore shell CWD to the project root. Run `ba-kit resolve --slug <slug> --date <date> [--module <module>]` and `cd` to the `Project root:` path it prints. Do NOT leave the shell stranded in `userstories/` or any module subdirectory — downstream steps (`srs`, `frd`, `package`) resolve `paths.design_doc` and `paths.shared_shell_contract` from the project root.
