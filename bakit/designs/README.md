# Design Artifacts

Use this directory for project runtime `DESIGN.md` files.

`DESIGN.md` is the visual direction and design-system document for a project. It is not the final mockup itself. BA-kit uses it to lock:
- visual tone
- colors and typography
- layout principles
- shared components such as menu, header, footer, cards, forms, and tables
- responsive behavior and anti-patterns

Machine-readable portal, navigation, shell variant, layout variant, and active-menu ownership belongs in `plans/{slug}-{date}/02_backbone/shared-shell-contract.md`.

## Current flow

BA-kit is migrating from manual wireframe handoff toward canon-first screen specs, ASCII rendering, and optional downstream Figma sync.

Current transitional model:
- `designs/{slug}/DESIGN.md` defines visual direction
- `02_backbone/shared-shell-contract.md` defines machine-readable shell/navigation ownership
- `03_modules/{module}/screens/*.md` defines screen canon, state visual coverage, ASCII, and Figma frame mapping
- `wireframe-input.md` and `wireframe-map.md` remain legacy transitional handoff artifacts
- future Figma sync is a downstream consumer and must not mutate BA canon

## Rules

- Keep one `DESIGN.md` per project slug.
- Treat `DESIGN.md` as the source of truth for visual direction.
- Treat the backbone `Portal Matrix` plus `shared-shell-contract.md` as the canonical IA pair for module-level screen and Figma work.
- Do not let module-level artifacts redefine shared components or the overall visual direction.
- If a user-supplied mockup conflicts with `DESIGN.md`, update the BA artifacts deliberately instead of silently accepting visual drift.
