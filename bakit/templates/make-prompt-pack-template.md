# Gói prompt Figma Make theo module (Module Make Prompt Pack)

## Context

- Module: [module-slug]
- Screen set: [SCR-01, SCR-02]
- Lane: `figma-make`

## Hard negatives

- Do not add fields not listed
- Do not add screens not listed
- Do not change top-level navigation
- If a rule is missing, omit instead of inventing

## Per-UC prompts

Each use case has its own paste-ready prompt and change log under `tool-lanes/figma-make/usecases/`:

- `uc-{usecase_slug}-make-prompt.md` — paste-ready Figma Make prompt scoped to one UC
- `uc-{usecase_slug}-change-log.md` — versioned incremental change prompts

These files are referenced from this pack but live as separate artifacts to keep prompts scoped and paste-ready.

### UC-01 - [Use Case Name]

- Prompt: `tool-lanes/figma-make/usecases/uc-01-make-prompt.md`
- Change log: `tool-lanes/figma-make/usecases/uc-01-change-log.md`

<!-- Add additional UC rows as needed -->

## Screen bundle

### SCR-01 - [Screen Name]

- Portal lock: [PORTAL-ID] / [NAV-SCHEMA-ID] / [Active Menu]
- Allowed fields: [Field A, Field B]
- Required states: [loading, empty, error]
- Validation surfaces: [inline, toast, banner]
- Hidden navigation exceptions: [none / list]
- Source excerpt: [short excerpt]
