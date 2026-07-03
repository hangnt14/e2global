# Audit Rules — Per-Artifact-Type Format & Cross-Reference Checks

Core lifecycle artifacts checked by `/ba-content-audit`. For each artifact type, mandatory sections are resolved at audit time by reading the referenced template, not hardcoded here.

## Severity Classification

| Severity | Meaning | Examples |
|----------|---------|----------|
| **Blocking** | Breaks artifact integrity, traceability, or compilation | Missing `type` frontmatter, missing mandatory section, broken cross-ref to required file |
| **Warning** | Deviation from conventions, stale references, naming drift | Missing optional frontmatter, naming convention deviation, stale index entry |
| **Info** | Low-risk observations, deferred checks | Optional section absent, anchor not validated, empty module directory |

## Finding ID Scheme

Stable content-hash IDs: `{SeverityPrefix}-{6-char-hex}` where hash = first 6 chars of SHA-256( `{file_path}:{check_type}:{location_key}` ). Same issue always gets same ID across re-audits.

Severity prefixes: `B-` (Blocking), `W-` (Warning), `I-` (Info).

## Core Lifecycle Artifact Rules (P0)

### 01_intake

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `intake` | `{project_root}/01_intake/intake.md` | `intake-form-template.md` | user_facing |
| `plan` | `{project_root}/01_intake/plan.md` | none | agent_facing |

**intake.md rules:**
- Frontmatter required: `type`, `status`, `created`
- Frontmatter optional: `owner`, `priority`, `tags`, `version`, `updated`, `links`
- Template: `templates/intake-form-template.md`
- Mandatory sections: resolved from template `##` headings at audit time
- `type` must be `intake` (Blocking if wrong)
- Naming: must be `intake.md` in `01_intake/` folder

**plan.md rules (agent_facing):**
- Frontmatter required: `type`, `status`, `created`
- No mandatory sections (agent-facing; structure varies)
- Naming: must be `plan.md` in `01_intake/` folder

### 02_backbone

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `backbone` | `{project_root}/02_backbone/backbone.md` | `requirements-backbone-template.md` | user_facing |
| `backbone_index` | `{project_root}/02_backbone/backbone-index.md` | `backbone-index-template.md` | agent_facing |
| `common_rules` | `{project_root}/02_backbone/common-rules.md` | `common-rules-template.md` | agent_facing |
| `message_list` | `{project_root}/02_backbone/message-list.md` | `message-list-template.md` | agent_facing |
| `shared_rule_message_index` | `{project_root}/02_backbone/shared-rule-message-index.md` | `shared-rule-message-index-template.md` | agent_facing |
| `shared_shell_contract` | `{project_root}/02_backbone/shared-shell-contract.md` | `shared-shell-contract-template.md` | agent_facing |
| `shared_shell_index` | `{project_root}/02_backbone/shared-shell-index.md` | `shared-shell-index-template.md` | agent_facing |
| `project_memory` | `{project_root}/02_backbone/project-memory.md` | `project-memory-template.md` | agent_facing |

**backbone.md rules:**
- Frontmatter required: `type`, `status`, `created`
- Frontmatter optional: `owner`, `priority`, `tags`, `version`, `updated`
- Template: `templates/requirements-backbone-template.md`
- Mandatory sections: resolved at audit time from template
- `type` must be `backbone` (Blocking if wrong)
- Module list in backbone → verify each listed module has `03_modules/{module_slug}/` folder (Blocking if missing folder)

**Index files (backbone-index, shared-shell-index, etc.):**
- Frontmatter required: `type`, `status`, `created`
- `type` validated per-file: `backbone-index`, `shared-shell-index` (Info — agent_facing, type not enforced)
- Index entries referencing files → verify files exist on disk (Warning if broken link)
- Index entries referencing modules → verify `03_modules/{module_slug}/` exists (Warning if missing)

### 03_modules — Module Artifacts

#### FRD
| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `frd` | `{module_root}/frd.md` | `frd-template.md` | user_facing |

- Frontmatter required: `type`, `status`, `created`, `module`
- Template: `templates/frd-template.md`
- Mandatory sections: resolved at audit time from template
- `type` must be `frd` (Blocking if wrong)
- All `BO-{feature}-{NN}` IDs in body → verify defined in same file or backbone (Warning if not found)

#### SRS Sources

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `srs_spec` | `{module_root}/srs/spec.md` | `srs-spec-template.md` | user_facing |
| `srs_flows` | `{module_root}/srs/flows.md` | `srs-flows-template.md` | user_facing |
| `srs_states` | `{module_root}/srs/states.md` | `srs-states-template.md` | user_facing |
| `srs_erd` | `{module_root}/srs/erd.md` | `srs-erd-template.md` | user_facing |
| `srs` (compiled) | `{module_root}/srs.md` | `srs-template.md` | user_facing |

**srs/spec.md rules:**
- Frontmatter required: `type`, `status`, `created`, `module`
- `type` must be `srs` (Blocking if wrong)
- Template: `templates/srs-spec-template.md`

**srs/flows.md rules:**
- Frontmatter required: `type`, `status`, `created`, `module`
- `type` must be `srs-flows` (Blocking if wrong)
- Template: `templates/srs-flows-template.md`

**srs/states.md rules:**
- Frontmatter required: `type`, `status`, `created`, `module`
- `type` must be `srs-states` (Blocking if wrong)
- Template: `templates/srs-states-template.md`

**srs/erd.md rules:**
- Frontmatter required: `type`, `status`, `created`, `module`
- `type` must be `srs-erd` (Blocking if wrong)
- Template: `templates/srs-erd-template.md`

**srs.md (compiled) rules:**
- Frontmatter required: `type`, `status`, `created`, `module`
- Template: `templates/srs-template.md`
- This is compiled output from canon sources — audit for consistency with source files, not structural completeness

#### User Stories

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `userstories_index` | `{module_root}/userstories/index.md` | `userstories-index-template.md` | agent_facing |
| `userstory_item` | `{module_root}/userstories/us-*.md` | `userstory-item-template.md` | user_facing |

**userstories/index.md rules:**
- Frontmatter required: `type`, `status`, `created`, `module`
- Template: `templates/userstories-index-template.md`
- Each story entry → verify `us-{slug}.md` exists (Warning if broken link)
- Each story ID (`US-{module}-{NNN}`) → verify story file exists with matching ID (Warning if not found)

**us-*.md rules:**
- Frontmatter required: `type`, `status`, `created`, `module`
- Template: `templates/userstory-item-template.md`
- Mandatory sections: resolved at audit time from template
- `type` must be `user-story` (Blocking if wrong)
- Story ID format: `US-{module}-{NNN}` in frontmatter or heading (Info if non-standard)
- Acceptance criteria present in expected format (Warning if missing)

#### Use Cases

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `usecases_index` | `{module_root}/usecases/index.md` | `usecases-index-template.md` | agent_facing |
| `usecase_item` | `{module_root}/usecases/uc-*.md` | `usecase-item-template.md` | user_facing |
| `usecase_diagrams` | `{module_root}/usecases/diagrams.md` | `usecase-diagrams-template.md` | user_facing |

**usecases/index.md rules:**
- Frontmatter required: `type`, `status`, `created`, `module`
- Template: `templates/usecases-index-template.md`
- Each UC entry → verify `uc-{slug}.md` exists (Warning if broken link)
- Each UC ID (`UC-{module}-{slug}`) → verify file exists (Warning if not found)

**uc-*.md rules:**
- Frontmatter required: `type`, `status`, `created`, `module`
- Template: `templates/usecase-item-template.md`
- Mandatory sections: resolved at audit time from template (Blocking if required section missing)
- `type` must be `use-case` (Blocking if wrong)
- Screen references → verify screen files exist (Warning if broken)
- PlantUML or Mermaid diagram present if template requires (Warning if missing)

#### ASCII Screens

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `ascii_screen_index` | `{module_root}/ascii-screen/index.md` | `ascii-screen-index-template.md` | agent_facing |
| `ascii_screen_item` | `{module_root}/ascii-screen/*.md` | `ascii-screen-template.md` | user_facing |

**ascii-screen/index.md rules:**
- Frontmatter required: `type`, `status`, `created`, `module`
- Template: `templates/ascii-screen-index-template.md`
- Each screen entry → verify `{screen_slug}.md` exists (Warning if broken link)

**{screen_slug}.md rules:**
- Frontmatter required: `type` (must be `screen`), `status`, `created`, `module`
- Template: `templates/ascii-screen-template.md`
- Mandatory sections: resolved at audit time from template
- ASCII wireframe section present if template requires (Info if missing)
- State visual coverage declared if template requires (Info if missing)

#### Screen Field Contract

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `screen_field_contract` | `{module_root}/screen-field-contract.yaml` | `screen-field-contract-template.yaml` | machine_facing |

- Valid YAML syntax (Blocking if malformed)
- Template: `templates/screen-field-contract-template.yaml`
- Required top-level keys: resolved from template at audit time (Blocking if missing)

### 04_compiled

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `compiled_frd` | `{project_root}/04_compiled/compiled-frd.html` | none (HTML) | user_facing |
| `compiled_srs` | `{project_root}/04_compiled/compiled-srs.html` | none (HTML) | user_facing |
| `compiled_srs_module` | `{project_root}/04_compiled/{module_slug}/compiled-srs.html` | none (HTML) | user_facing |

- HTML files: verify well-formed (basic HTML structure check) (Warning if malformed)
- No frontmatter check (HTML artifacts)
- Verify referenced source modules exist (Info if compiled for non-existent module)

### Shared

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `shared_traceability` | `{project_root}/shared/traceability.md` | `shared-traceability-template.md` | agent_facing |
| `shared_staleness` | `{project_root}/shared/staleness.md` | `shared-staleness-template.md` | agent_facing |
| `shared_definitions` | `{project_root}/shared/definitions.md` | `shared-definitions-template.md` | agent_facing |

- Frontmatter required: `type`, `status`, `created`
- `type` must match key name: `shared-traceability`, `shared-staleness`, `shared-definitions` (Info — agent_facing, type not enforced)
- Template checks: respective templates per table above

### Project-Level Files

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `project_home` | `{project_root}/PROJECT-HOME.md` | `project-home-template.md` | user_facing |
| `collab_home` | `{project_root}/COLLAB-HOME.md` | `collab-home-template.md` | user_facing |
| `module_home` | `{module_root}/MODULE-HOME.md` | `module-home-template.md` | user_facing |
| `design_doc` | `designs/{slug}/DESIGN.md` | `design-md-template.md` | agent_facing |

Note: `design_doc` lives at repo-level (`designs/{slug}/DESIGN.md`), not under `plans/{slug}-{date}/`.

- Frontmatter required: `type`, `status`, `created`
- `type` must be `design-doc` for `design_doc`, `project-home` for project_home, etc. (Blocking if wrong for user_facing; Info for agent_facing)
- Template checks: respective templates

### Brainstorms

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `brainstorm_index` | `{module_root}/brainstorms/index.md` | `brainstorms-index-template.md` | agent_facing |
| `brainstorm_item` | `{module_root}/brainstorms/*.md` | `brainstorm-module-item-template.md` | user_facing |

- Frontmatter required: `type` (must be `brainstorm`), `status`, `created`
- Template checks: respective templates

### Changes & Impacts

| Artifact Key | Path Pattern | Template | Profile |
|---|---|---|---|
| `change_request` | `{project_root}/changes/CR-*.md` | `change-request-template.md` | user_facing |
| `impact_report` | `{project_root}/impacts/CR-*-impact.md` | `impact-report-template.md` | user_facing |

- Frontmatter required: `type`, `status`, `created`
- `type` must be `change-request` for CR files, `impact-report` for impact files (Blocking if wrong)
- Template checks: respective templates

These artifact types exist in contract.yaml but are NOT audited in v1. Listed for reference:

| Group | Artifact Keys |
|---|---|
| Tool-lanes (Figma Make) | `tool_lane_state`, `make_guidelines`, `make_prompt_pack`, `make_uc_prompt`, `make_uc_change_log`, `prototype_conformance_checklist`, `prototype_conformance_report`, `figma_make_shared_rules`, `figma_make_shared_prompt_skeleton`, `figma_make_shared_component_contracts` |
| Tool-lanes (Stitch) | `stitch_design_system_id`, `stitch_screen_map`, `stitch_sync_report`, `stitch_mismatch_report` |
| Reverse | `reverse_index`, `reverse_baseline_lock`, `reverse_focus_excerpts`, `reverse_evidence_ledger`, `reverse_drift_state`, `reverse_read_manifest` |
| QC | `qc_report`, `qc_backlog`, `qc_export_*` |
| Memory (deep) | `memory_index`, `memory_log`, `memory_hot_vocabulary`, `memory_hot_decisions`, `memory_hot_pushback`, `memory_module_warm` |
| Figma sync | `figma_sync_report`, `figma_mismatch_report` |
| Source cache | All `source_*` artifacts |
| Receipts | `impact_receipt`, `options_receipt`, `index_validation_receipt`, `srs_compile_receipt`, `package_snapshot` |
| Control type library | `control_type_library` |
| Options | All `option_*` artifacts |

## Cross-Reference Resolution

### Reference Types Detected

| Type | Pattern | Resolution | Severity if Broken |
|------|---------|------------|-------------------|
| Frontmatter `links:` | YAML list `links: [path, ...]` | Path relative to project root; check file exists | Blocking |
| Wikilink with path | `[[docs/path/to/file.md]]` | Path relative to project root; check file exists | Blocking |
| Wikilink with display | `[[path\|Display Text]]` | Extract path before `\|`; check file exists | Blocking |
| Wikilink with anchor | `[[path#section-id]]` | Extract path before `#`; check file exists (anchor validation is P2) | Blocking for file; Info for anchor |
| ID reference inline | `FR-payment-001`, `UC-auth-login`, etc. | Find ID definition in expected source file | Warning |
| Index file entry | `- [label](./relative-path.md)` | Resolve relative to index location; check file exists | Warning |
| Markdown link | `[text](relative/path.md)` | Skip external URLs (`https://`); resolve relative paths | Warning |

### ID Definition Resolution Table

| ID Pattern | Expected Definition Location | Scan Strategy |
|------------|------------------------------|---------------|
| `FR-{feature}-{NNN}` | Any module `srs/spec.md` or `srs.md` | Global scan (first pass: collect all defined IDs → second pass: check refs) |
| `NFR-{feature}-{NNN}` | Same as FR | Global scan |
| `BR-{feature}-{NNN}` | Any module `srs/spec.md` or `common-rules.md` | Global scan |
| `E-{feature}-{NNN}` | Any module `srs/spec.md` | Global scan |
| `UC-{module}-{slug}` | `03_modules/{module}/usecases/uc-{slug}.md` | Direct path check |
| `US-{module}-{NNN}` | `03_modules/{module}/userstories/us-{module}-{nnn}.md` | Glob match |
| `CAP-{feature}-{NN}` | Any module `frd.md` or backbone | Global scan |
| `BO-{feature}-{NN}` | Any module `frd.md` or backbone | Global scan |
| `CR-{YYYYMMDD}-{NNN}` | `changes/CR-{change_id}.md` | Direct path check |
| `MSG-{TYPE}-{NN}` | `message-list.md` in backbone | Backbone check |
| `CR-{TYPE}-{NN}` (rule code) | `common-rules.md` in backbone or any module | Backbone + global scan |

### Path Resolution Rules

1. **Absolute from project root**: paths starting without `./` or `../` → resolve relative to `plans/{slug}-{date}/`
2. **Relative to source file**: paths starting with `./` or `../` → resolve relative to directory of source file
3. **Cross-module**: `../other-module/file.md` in a module file → resolves to `03_modules/other-module/file.md`
4. **External URLs**: `https://` or `http://` → skip (not checkable)
5. **Template placeholders**: path patterns containing `{slug}`, `{date}`, `{module_slug}` → resolve per project

### ID Pattern Regex

```
FR-\w+-\d{2,3}           # FR-{feature}-{NNN}
NFR-\w+-\d{2,3}          # NFR-{feature}-{NNN}
BR-\w+-\d{2,3}           # BR-{feature}-{NNN}
E-\w+-\d{2,3}            # E-{feature}-{NNN}
UC-\w+-[\w-]+            # UC-{module}-{slug}
US-\w+-\d{2,3}           # US-{module}-{NNN}
CAP-\w+-\d{2}            # CAP-{feature}-{NN}
BO-\w+-\d{2}             # BO-{feature}-{NN}
CR-\d{8}-\d{3}           # CR-{YYYYMMDD}-{NNN}
MSG-(?:ERR|WRN|SUC|INF)-\d{2}  # MSG-{TYPE}-{NN}
CR-(?:DIS|BEH|VAL|MIX)-\d{2}   # CR-{TYPE}-{NN} (rule code)
```

### Two-Pass ID Resolution

First pass: scan all files, collect `{id: (file, line)}` defined IDs into a map.
Second pass: scan all files for ID references, check against map.
Unmatched refs → Warning. IDs defined but never referenced → Info.

## Finding-to-Fix-Command Mapping

After audit, each Blocking and Warning finding is classified into a fix command group for the `## Fix Commands` section of the report.

### Classification Rules

**Direct Edit** — finding can be fixed by editing the source file:

| check_type | description_pattern | command_template |
|---|---|---|
| `frontmatter` | Missing required field `{field}` | `Edit {file_path}` |
| `frontmatter` | Expected type `{expected}`, got `{actual}` | `Edit {file_path}` |
| `frontmatter` | Missing YAML frontmatter | `Edit {file_path}` |
| `frontmatter` | Cannot parse frontmatter: `{error}` | `Edit {file_path}` |
| `frontmatter` | Missing optional field `{field}` | `Edit {file_path}` |
| `section` | Missing mandatory section `{section}` | `Edit {file_path}` |
| `section` | Extra section `{section}` not in template | `Edit {file_path}` |
| `crossref` | Broken wikilink: `{path}` | `Edit {file_path}` |
| `crossref` | Broken frontmatter link: `{path}` | `Edit {file_path}` |
| `crossref` | Broken ID reference: `{id}` | `Edit {file_path}` |
| `crossref` | Broken markdown link: `{path}` | `Edit {file_path}` |
| `crossref` | Index entry references missing file: `{path}` | `Edit {file_path}` |
| `id_orphan` | ID `{id}` defined but never referenced | `Edit {file_path}` |
| `naming` | Naming deviation: expected `{expected}` | `Edit {file_path}` |

The `Description` from the finding becomes the "What to change" / "Change" column content verbatim.

**Skill-Based** — finding needs a BA-kit skill to fix:

| check_type | description_pattern | command_template |
|---|---|---|
| `crossref` | Module `{module}` listed but no folder found | `/ba-next --slug {slug}` — review missing module |
| `crossref` | Compiled SRS inconsistent with source canon | `/srs {module} --update` |
| `section` | Missing mandatory section `{section}` in `srs.md` (compiled) | `/srs {module} --compile` |
| `crossref` | Broken UC screen reference: `{screen}` | `/srs {module} --update` or `Edit` to fix screen reference |
| `crossref` | Missing use case file referenced in index | `/usecase {module} --create {slug}` |
| `crossref` | Missing user story file referenced in index | `/userstory {module} --create {nnn}` |
| `section` | Missing diagram in use case `{file}` | `Edit {file_path}` — add PlantUML/Mermaid diagram |
| `section` | Missing acceptance criteria in `{file}` | `Edit {file_path}` — add acceptance criteria section |

The "Why" column contains the finding description verbatim.

**Manual Actions** — finding needs a manual file/directory operation:

| check_type | description_pattern | action_template |
|---|---|---|
| `naming` | Naming deviation: expected `{expected}` | `Rename {file_path} → {expected_dir}/{expected_name}` |
| `crossref` | Module `{module}` listed but no folder found | `Create 03_modules/{module}/ directory` |

The "Reason" column contains the finding description verbatim.

### Fallback Rule

If no pattern matches, classify as **Direct Edit** with command `Edit {file_path}` and use the finding's "Suggested Fix" as the change description.

| Case | Handling |
|------|----------|
| `.pen` files | Skip entirely (Pencil MCP-managed, encrypted) |
| Empty module directory | Info: "Module {slug} has no artifacts yet" |
| Missing project folder | Blocking: "No project found for slug {slug}" |
| Project with intake + backbone only (no modules) | Audit what exists; Info: "No modules found — partial audit" |
| Malformed YAML frontmatter | Blocking: "Cannot parse frontmatter" |
| File < 3kB | Read fully — small enough, Grep overhead higher than read cost |
| File 3–10kB | Read with `offset`+`limit` (<5kB per read). Frontmatter: first 40 lines. Sections: TOC-first (80 lines), then target sections. Cross-refs: Grep |
| File > 10kB | Never read fully. Frontmatter: `offset=0, limit=40`. Sections: Grep `^## ` for headings list, then read only missing/present sections. Cross-refs: Grep for wikilinks/IDs/links, resolve against manifest. Content verification: `offset`+`limit` on specific line ranges |
| ID-dense project (>50 ID definitions across all files) | Use on-disk indexing. Write all IDs to `shared/.audit-id-index.txt` via Bash `grep -rE`. Use `files_with_matches` for discovery. Cross-reference via `grep -c "ID"` against index file. Orphan detection via `sort \| uniq -c \| awk`. Zero context for ID collection. |
| Project with >60 files or >2 modules | Multi-agent batched audit. Orchestrator builds manifest + global index (Steps 1-2), audits system files, then spawns one sub-agent per module. Each sub-agent gets fresh context (~200K), audits its module files, writes findings to `shared/.audit-module-{slug}.md`. Orchestrator merges module files into final report. Context per sub-agent: ~45% of budget. |
| File with no frontmatter at all | Blocking: "Missing YAML frontmatter" |
| File with unknown `type` value | Warning: "Unknown artifact type '{value}'" |
| Compiled HTML with malformed structure | Warning: "HTML appears malformed" |
| External URL in markdown link | Skip (not reported) |
| Wikilink with empty path `[[ ]]` | Warning: "Empty wikilink" |
| Broken anchor link `[[path#anchor]]` | Info: "Anchor '{anchor}' not validated (P2)" |
