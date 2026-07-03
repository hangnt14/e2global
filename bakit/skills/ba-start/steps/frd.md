# BA Start Step - FRD

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md`

## Memory Read Scope

- **Must read:** `core/contract.yaml`, `core/contract-behavior.md`, `paths.backbone_index`, `paths.plan` (when exists)
- **May read:** targeted `paths.backbone` sections routed by the index, `paths.project_memory` or (`paths.memory_hot_vocabulary` + `paths.memory_hot_decisions`) when shard mode is active
- **Must NOT read:** `log.md`, `cold/`, `warm/` shards, unrelated module shards

## Governance Gate

Before mutating this artifact:
1. **Skip this gate for first-pass creation** (when `paths.frd` does not yet exist).
2. For reruns (artifact already exists): verify write authority and locate the active impact receipt at `paths.impact_receipt`. If no active receipt exists and `change_class` is not `wording-only`, emit `GOVERNANCE_BLOCK: impact_receipt missing or invalidated` and stop.
3. If either check fails on a rerun: emit `GOVERNANCE_BLOCK: {reason}` and stop.
4. After mutation completes: offer to file the change into canonical memory using `templates/project-memory-fileback-record-template.md`.

Receipt reference: `templates/impact-receipt-template.md`

## Scope

Run Step 6 only.

## Prerequisites

- Resolve slug, date, and module using `ba-kit resolve --slug <slug> [--module <module>]`.
  The CLI uses `find -type d` internally for correct directory discovery.
  Do not use `Glob` — it only matches files, not directories.
- **[CWD GATE]** After resolve, cd to the project root (`Project root:` line from `ba-kit resolve` output). All artifact paths in `contract.yaml` are relative to the project root. A stale CWD from a previous step will cause false prerequisite failures.
- Require `paths.backbone`.
- Prefer `paths.backbone_index` for routing. If it is missing and the backbone is large, stop and ask to refresh the index.
- If backbone is missing, print the exact missing path and stop.
- Trust accepted user intent. Do not reopen scope discovery after FRD execution is accepted.
- Run a narrow FRD preflight:
  - If `ba-kit guardrail --command frd --slug <slug> --date <date> --module <module>` returns `status=block`, surface the block message and stop
  - Otherwise use `ALLOW_READS` for file discovery
  - read `paths.backbone_index` first
  - read only targeted `paths.backbone` sections and `paths.plan` when it exists
  - do not scan unrelated module folders once slug, date, and module are resolved

## Output

- `paths.frd`

## Step 6 - Produce FRD

Produce the FRD from the backbone using `~/.claude/templates/frd-template.md` (fallback: [../../../templates/frd-template.md](../../../templates/frd-template.md)):

- Functional overview
- User personas
- Feature list with MoSCoW priorities
- Workflows (Mermaid)
- Data requirements
- Business rules
- Integration points
- Acceptance criteria

Execution rules:

- Start from `paths.backbone_index`, then the exact targeted backbone sections, plus the exact plan path when it exists.
- In `hybrid` mode, keep the FRD concise and focused on features, workflows, business rules, and integration-relevant context.
- In `lite` mode, emit the FRD only when the user explicitly asks for it.

Save to `paths.frd`.
