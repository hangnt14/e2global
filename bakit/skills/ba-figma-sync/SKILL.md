---
name: ba-figma-sync
description: Sync approved BA-kit screen canon to Figma through Figma MCP. Downstream only: reads SRS canon/shared shell/design direction and writes sync or mismatch reports, never BA canon.
argument-hint: "--slug <slug> --module <module_slug> [--date <YYMMDD-HHmm>] [--dry-run]"
---

# BA Figma Sync

Use this skill when the user asks to create, update, or synchronize Figma wireframe frames from BA-kit SRS screen canon.

## Invocation

```text
/ba-figma-sync --slug warehouse-rfp --module auth-flow
/ba-figma-sync --slug warehouse-rfp --module auth-flow --dry-run
/ba-do Đồng bộ Figma cho module auth-flow của dự án warehouse-rfp
```

## Required Read Order

1. Read `~/.claude/core/contract.yaml`. If missing, fall back to `core/contract.yaml` from the BA-kit repo root.
2. Read `~/.claude/core/contract-behavior.md`. If missing, fall back.
3. Read `~/.claude/core/behavior/figma-sync.md`. If missing, fall back to `core/behavior/figma-sync.md` from the BA-kit repo root.
4. Resolve slug, date, and module exactly.
5. Run or follow the equivalent of:
   - `ba-kit check-prereq figma-sync --slug <slug> --module <module_slug>`
   - `python3 scripts/check-ascii-screen-index.py --repo . --slug <slug> --date <date> --module <module_slug> --require-ascii-current`
6. Read `ascii-screen/index.md` before individual screen files.

## Source Inputs

Required:

- `plans/{slug}-{date}/03_modules/{module_slug}/ascii-screen/index.md`
- `plans/{slug}-{date}/03_modules/{module_slug}/srs-compile-receipt.json`
- `plans/{slug}-{date}/03_modules/{module_slug}/ascii-screen/*.md`
- `designs/{slug}/DESIGN.md`
- `plans/{slug}-{date}/02_backbone/shared-shell-contract.md`

Optional:

- `plans/{slug}-{date}/02_backbone/shared-shell-index.md`
- `plans/{slug}-{date}/shared/definitions.md`
- `plans/{slug}-{date}/shared/traceability.md`
- `plans/{slug}-{date}/03_modules/{module_slug}/screen-field-contract.yaml`
- `plans/{slug}-{date}/03_modules/{module_slug}/figma-sync/figma-sync-report.md`
- `plans/{slug}-{date}/03_modules/{module_slug}/figma-sync/figma-mismatch-report.md`

## Write Scope

Allowed repo writes:

- `plans/{slug}-{date}/03_modules/{module_slug}/figma-sync/figma-sync-report.md`
- `plans/{slug}-{date}/03_modules/{module_slug}/figma-sync/figma-mismatch-report.md`

Forbidden repo writes:

- `srs.md`
- `ascii-screen/*.md`
- `usecases/*.md`
- `userstories/*.md`
- `srs/spec.md`
- `DESIGN.md`
- `shared-shell-contract.md`
- `shared-shell-index.md`

Before any repo write, validate scope with:

```bash
ba-kit check-write-scope --command figma-sync <target-path>
```

## MCP Behavior

- Use the configured Figma MCP server only after the user explicitly asked for Figma sync.
- If no Figma MCP tool is available in the runtime, stop and report: "Figma MCP is not configured; no Figma changes were made."
- Create or update Figma frames from screen canon, ASCII wireframes, visual state coverage, `DESIGN.md`, and shared shell rules.
- After updating Figma, read back enough frame metadata to verify names, screen IDs, key states, and shared shell/menu mapping.
- If Figma differs from canon, do not patch canon silently. Write a mismatch report and ask the BA to update canon first when requirement meaning changed.

## Output

After the run, report:

- resolved project/module
- screens attempted
- screens skipped and why
- frames created or updated
- mismatches found
- report paths written

## Stop Conditions

- Missing or stale `srs-compile-receipt.json`
- Missing `ascii-screen/index.md`
- Missing `DESIGN.md`
- Missing `shared-shell-contract.md`
- `doctor-srs` blocks the module
- Figma MCP unavailable
- User asks to change requirement meaning directly in Figma
