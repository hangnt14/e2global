# BA Start Step - Package

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md`

## Discovery Strategy: Snapshot-First

Before any artifact reads, check for a current package snapshot manifest at
`plans/{slug}-{date}/02_backbone/package-snapshot.md`.

- If the snapshot exists and `snapshot_state: current`, use it as the authoritative
  artifact inventory.  Do not re-run broad index discovery.
- If the snapshot is absent or `snapshot_state: degraded`, run the guardrail preflight
  to classify indexes, then proceed with index-first discovery:
  ```bash
  ba-kit guardrail --command package --slug {slug} --date {date}
  ```
- Regenerate the snapshot after any compile step by running:
  ```bash
  python3 scripts/package-snapshot.py --repo . --slug {slug} --date {date} --output plans/{slug}-{date}/02_backbone/package-snapshot.md
  ```

## Memory Read Scope

- **Must read:** `core/contract.yaml`, `core/contract-behavior.md`
- **Snapshot path (preferred):** `plans/{slug}-{date}/02_backbone/package-snapshot.md` when current
- **Index fallback:** `paths.backbone_index`, `paths.userstories_index`, `paths.usecases_index`, `paths.ascii_screen_index` when snapshot absent or degraded
- **May read:** `paths.project_memory` (compact only, consistency check), `paths.memory_index` (health overview and activation state)
- **Must NOT read:** raw source, full intake, `log.md`, `cold/`, `warm/` shards, or full source-of-truth artifacts for cross-reference discovery when snapshot or indexes are current

## Scope

Run Step 12 only.

## Prerequisites

- Resolve slug and date using `ba-kit resolve --slug <slug>`.
  The CLI uses `find -type d` internally for correct directory discovery.
  Do not use `Glob` — it only matches files, not directories.
- Require at least one emitted downstream artifact for the selected mode.
- If the engagement emitted any module SRS, require at least one module `paths.srs`.
- If a module SRS exists in canon-first form, require `paths.srs_compile_receipt` and treat missing/stale receipt as a package blocker.
- If a module has UI-backed screen canon, require current ASCII coverage in `ascii-screen/*.md`.

## Outputs

- packaged HTML under `paths.compiled_root`
- delivery summary
- refreshed `plans/{slug}-{date}/02_backbone/package-snapshot.md`

## Step 12 - Package deliverables

Run a final packaging and quality pass:

- Keep the default package scope narrow: validate the existing artifact set from the snapshot
  manifest or indexes, then regenerate `paths.compiled_frd` when FRD exists and
  `paths.compiled_srs` when SRS exists.
- Do not treat `package` as a full rebuild of intake, backbone, stories, and SRS drafts.
- When snapshot is current, use its `artifacts` list for existence checks and its `indexes`
  list for cross-reference routing — no additional index reads required.
- When snapshot is absent or degraded, fall back to `paths.backbone_index`,
  `paths.userstories_index`, `paths.usecases_index`, and `paths.ascii_screen_index` for cross-reference discovery.
- Read full markdown only for the artifact currently being converted to HTML, or emit
  `READ_ESCALATION` when an index is missing, stale, or contradictory.
- Verify all deliverables follow their templates.
- Check cross-references between the backbone and every emitted downstream artifact.
- When FRD and SRS exist, check their cross-references against stories.
- Verify user-story traceability across FR, UC, and SCR.
- Verify compiled SRS freshness against `paths.srs_compile_receipt` before converting to HTML.
- Validate naming conventions and file structure.
- Flag broken links or missing sections.
- Produce a delivery summary.
- After compile, refresh the snapshot manifest.
- Before final output, validate token budgets:
  ```bash
  ba-kit check-token-budget
  ```

## Step 12.1 - Generate packaged HTML

> Per-module HTML from `compile-srs.py` at `paths.compiled_srs_module`.
> Aggregate step: single stakeholder HTML.

When the engagement includes multiple modules with FRD or SRS, aggregate and convert them to HTML:

```bash
python scripts/md-to-html.py plans/{slug}-{date}/03_modules --aggregate
```

Output:

- `paths.compiled_frd`
- `paths.compiled_srs`

When the engagement does not include SRS, package only the artifacts that were actually emitted and requested for stakeholder handoff.

If the user later manually inserts wireframe images or links into the markdown source, preserve those references in the packaged HTML instead of trying to regenerate design assets.
