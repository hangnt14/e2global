# Module Authoring Behavior

FRD and stories must start from `paths.backbone_index`. Re-entry still starts there after long sessions, reruns, or host auto-compact. If the index is current, read targeted `paths.backbone` sections only.

## Backbone Authority

Module artifacts are downstream from backbone. Before writing any module artifact, validate backbone alignment:
- Story actor, goal, feature, and priority must trace to backbone module scope.
- If alignment fails, stop with `BACKBONE_ALIGNMENT_FAIL: story_scope` and route through `ba-start impact` or backbone refresh.

## Read Scope

- FRD must read: `core/contract.yaml`, `core/contract-behavior.md`, `paths.backbone_index`, and `paths.plan`.
- Stories must read: `core/contract.yaml`, `core/contract-behavior.md`, and `paths.backbone_index`.
- May read: targeted `paths.backbone` sections, `paths.frd` for stories when it exists, `paths.project_memory` or hot vocabulary and decisions shards.
- Must not read: `log.md`, `cold/`, unrelated `warm/` shards, unrelated module artifacts, or full `paths.backbone` when the index is current.

## Authoring Rules

- Keep module-scoped outputs inside `paths.module_root`.
- Use exact module resolution and stop on ambiguity.
- Preserve accepted backbone scope, terminology, gates, and risks.
- Route material scope or requirement corrections through `impact` before mutating accepted downstream artifacts.
- Stories output is `userstories/index.md` plus one `userstories/us-{slug}.md` per story. Do not create `user-stories.md` or `user-stories-index.md`.
- When stories writes or refreshes `paths.userstories_index`, generate it with `stale_status: unknown`, leave `validated_at` and `validated_by` blank. **[BẮT BUỘC]** Immediately run `ba-kit validate-index --index-key userstories_index --slug <slug> --date <date> --module <module> --writeback`. If validation fails, stop execution. Do not proceed to SRS or other downstream work. The PostToolUse hook serves as fallback, but this inline call is the primary enforcement.
- For any routeable downstream rerun from module authoring, re-enter through `paths.backbone_index` first and reopen only the targeted backbone slices it routes to.
- Generated module indexes are navigators only. They must include IDs, source headings, trace hints, counts, freshness, and route hints, not duplicated requirement prose.
- If a required upstream decision is absent or contradictory, stop and route back to the owning step instead of inventing prose.
