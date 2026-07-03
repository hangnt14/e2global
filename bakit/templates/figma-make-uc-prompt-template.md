# Figma Make UC Prompt

## Context

- Module: {module_slug}
- Use case: UC-{usecase_slug}
- Lane: `figma-make`
- Generated from: `screen-field-contract.yaml` + `ascii-screen/*.md` + `DESIGN.md`

## Source references

- Design baseline: `DESIGN.md`
- Screen contract: `screen-field-contract.yaml`
- Shared rules: `05_tool-lanes/figma-make/shared-rules.md`
- Shared prompt skeleton: `05_tool-lanes/figma-make/shared-prompt-skeleton.md`
- Shared component contracts: `05_tool-lanes/figma-make/shared-component-contracts.md`
- Module prompt pack: `tool-lanes/figma-make/make-prompt-pack.md`

## Shared baseline instruction

Reuse the shared prompt skeleton for design system, color palette, typography, spacing, and component contracts. Do NOT redefine these in this prompt. UC-01 is NOT the style authority — `DESIGN.md` owns the visual baseline.

## UC-specific elements

### Screens involved

<!-- List SCR-IDs covered by this UC -->

### Allowed fields

<!-- Per-screen field allowlist from screen-field-contract.yaml -->

### Required states

<!-- Loading, empty, error, edge-case states required for this UC -->

### Validation surfaces

<!-- inline, toast, banner — per field -->

### Navigation constraints

- Portal lock: <!-- PORTAL-ID -->
- Nav schema: <!-- NAV-SCHEMA-ID -->
- Active menu: <!-- menu item -->
- Hidden navigation exceptions: <!-- none or list -->

### UC flow constraints

<!-- Step-by-step from UC main success scenario, alternate flows -->

## Hard negatives

- Do not add fields not listed in the allowlist
- Do not add screens not listed above
- Do not change top-level navigation
- Do not change Portal ID, Nav Schema ID, or Active Menu
- If a rule is missing, omit instead of inventing
- Do not treat UC-01 as the style authority
- Do not modify any other element outside this UC scope

## Paste-ready prompt

<!-- Self-contained paste-ready prompt block for Figma Make -->
