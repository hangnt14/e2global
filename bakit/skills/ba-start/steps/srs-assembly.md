# BA Start Step - SRS Assembly

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md`

## Step 10.1 - Produce Shared Traceability And Definitions

Produce the shared traceability and definitions artifacts from the completed source set. Prefer `ba-documentation-manager` ownership when delegated.

Outputs:
- `paths.shared_traceability` — backbone → userstories → usecases → screens/SRS source map
- `paths.shared_definitions` — canonical term definitions used across module artifacts

## Step 10.5 - Cross-Function Impact Inlining

During UC compilation (Step 11, substep 4 — usecases), for each UC that declares `## Cross-Function Impact`:

1. Read `### Within Module` table → inline as-is into the UC's compiled entry.
2. Read `### Across Modules` table → cross-reference with other modules' declarations:
   - "produces for" entries → check if target module UC declares matching "consumes from"
   - "consumes from" entries → check if source module UC declares matching "produces for"
3. Mark each inter-module edge:
   - Match found on backbone feature ID + matching data/state → **Resolved**
   - No matching declaration in target/source module → **Pending** (other module may not be authored yet)
   - Declarations exist but data/type conflicts → **Mismatch**
4. Add `Status` column to Across Modules table in compiled output.
5. Inline the cross-function subsection into the UC's compiled entry (after UC flow content, before next UC).
6. UCs without `## Cross-Function Impact` → no subsection added (no noise).

Pending edges are NOT errors — partial data is valid when other modules haven't been authored yet.

## Step 10.9 - Pre-Compile Cleanup: Resolve Placeholders [BẮT BUỘC]

Before running the deterministic compile script, scan all canon source files for unfilled template placeholders, fix column name alignment, and verify index-disk consistency.

1. **Fix index column names.** Ensure index table columns exactly match the templates (see `templates/usecases-index-template.md`, `templates/ascii-screen-index-template.md`, `templates/userstories-index-template.md`). Common errors: `Stories` instead of `Linked Stories`, `Source Backbone` instead of `Source Backbone IDs`, missing `Trigger` column.

2. **Compute source_hash.** Fill `source_hash` in every index metadata table using actual SHA-256 hashes of the source directory/files (see `guardrail_common.compute_source_hash`). Never leave empty or placeholder values.

3. **[BẮT BUỘC] Index-disk consistency audit.** After writing all canon files, verify EVERY file referenced in `usecases/index.md` and `ascii-screen/index.md` exists on disk:
   ```bash
   # Verify UC files exist
   ls 03_modules/{module}/usecases/uc-*.md | wc -l
   # Compare with rows in usecases/index.md
   grep "| UC-" 03_modules/{module}/usecases/index.md | wc -l
   # Same for screens
   ls 03_modules/{module}/ascii-screen/scr-*.md | wc -l
   grep "| SCR-" 03_modules/{module}/ascii-screen/index.md | wc -l
   ```
   If counts don't match: **STOP. Do not compile. Write missing files or fix index FIRST.** `compile-srs.py` will also block with `index_disk_errors`.

4. **Fix placeholders.** Auto-resolve `[Tên dự án]`, `[Tên module]` etc. from backbone context. Ask user for any that cannot be auto-resolved.

5. **Run validator.** Ensure `ba-kit validate-index --writeback` passes for all indexes before compile.

6. **Run guardrails on screen canon.** After writing or updating screen canon files, run ALL mandatory guardrails:
   ```bash
   ba-kit check-screen-behaviour plans/{slug}-{date}/03_modules/{module}/ascii-screen/
   ba-kit check-control-type-compliance plans/{slug}-{date}/03_modules/{module}/ascii-screen/
   ba-kit check-message-placement plans/{slug}-{date}/03_modules/{module}/ascii-screen/
   ```
   Fix violations before compile. The `Message Zones:` legend and `▼ MSG-*` markers are mandatory per `srs-wireframes.md` Step 9.
   Also run terminology check (WARN only):
   ```bash
   ba-kit check-terminology plans/{slug}-{date}/03_modules/{module}/
   ```

## Step 11 - Compile SRS

Run the deterministic compile script to assemble `paths.srs` from canon sources:

```bash
python3 scripts/compile-srs.py --module-root plans/{slug}-{date}/03_modules/{module}
```

Or with direct path:
```bash
python3 scripts/compile-srs.py --module-root plans/{slug}-{date}/03_modules/{module}
```

To skip HTML generation (markdown-only):
```bash
python3 scripts/compile-srs.py ... --no-html
```

The script handles:
- Reading `srs-template.md` for heading structure
- Stripping YAML frontmatter from UC and screen canon files before merging
- Auto-filling known placeholders from project context (`[Tên dự án]`, `[Tên module]`, `[Project]`, `[Module]`)
- Detecting remaining unfilled placeholders and reporting as warnings
- Merging all canon sources into correct template sections: `srs/spec.md` → FR/NFR, `usecases/uc-*.md` → UC section, `ascii-screen/*.md` → Screen Descriptions, `srs/flows.md` → Flows, `srs/erd.md` → ERD
- Inlining cross-function impact per UC (Step 10.5)
- Running `validate-navigation-consistency.py` when UI-backed screens and `DESIGN.md` exist; treats `MENU_SCHEMA_MISMATCH`, `NAV_SCHEMA_MISMATCH`, and `MENU_ACTIVE_MISSING` as blocking
- Validating template compliance (all required headings present)
- Writing `paths.srs` (compiled `srs.md`) + `paths.srs_compile_receipt`
- Generating per-module HTML at `04_compiled/{module_slug}/compiled-srs.html` (unless `--no-html`)

Do not manually assemble `srs.md`. The script is the single source of truth for compile. Do not delete canonical source files.
