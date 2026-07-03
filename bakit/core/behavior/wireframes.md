# Wireframes Behavior

## Read Scope

- Must read: `core/contract.yaml`, `core/contract-behavior.md`, `paths.ascii_screen_index`, `paths.ascii_screen_root`, and `skills/ba-start/steps/wireframes.md`.
- May read: `paths.design_doc`, `paths.shared_shell_contract`, `paths.shared_shell_index`, `paths.screen_field_contract`, and targeted ascii-screen canon files.
- Must not read: `log.md`, `cold/`, other module shards, unrelated module artifacts.

## Deprecated Command Scope

- `wireframes` is a compatibility validation command only.
- Do not create legacy wireframe pack artifacts.
- Canonical ASCII wireframes live in module-local `paths.ascii_screen_item` files and are compiled by `ba-start srs`.

## Design Document Handling

- `paths.design_doc` is the runtime design constraint source for UI-backed modules.
- Treat `paths.design_doc` as the visual-direction document and `paths.shared_shell_contract` as the machine-usable ownership contract for portals, nav schemas, shell variants, and active-menu rules.
- If it exists, ask whether to reuse, refresh, or stop before changing it.
- If absent or refresh is approved, synthesize it from approved decisions using `templates/design-md-template.md`.
- Keep `defaults.ui_baseline` as fallback only when the approved design document does not specify another direction.
- Do not proceed when design direction, portal navigation schema, or active-menu rules remain unresolved.

## ASCII Validation Behavior

- Require each UI-backed screen canon file in `ascii-screen/` to contain `## ASCII Wireframe`.
- Require `ascii_status: current`.
- Require ASCII subsections for every required visual state.
- If validation fails, route to `ba-start srs --slug <slug> --module <module_slug>`.

No outputs are allowed from this command. Screen and behavior changes discovered during visual review route through `impact`, then `srs`.
