# BA-kit Behavior Shards

`core/contract-behavior.md` contains shared behavior every runtime must read.

Command-specific behavior lives in this folder. Runtime adapters must load:

1. `core/contract.yaml`
2. `core/contract-behavior.md`
3. the shard(s) listed in `behavior_shards.<command>`
4. the selected step file
5. templates and upstream artifacts only when the active step needs them

Shard files are policy overlays. They must not redefine literal paths or thresholds from `core/contract.yaml`.

## Wireframe Tool Lanes

- `manual` remains the default Step 9 lane.
- AI lanes are opt-in and consume `paths.screen_field_contract` as the hard-control artifact.
- `wireframes` may emit lane-specific artifacts, but it must not rewrite upstream SRS truth.
- For v1, `figma-make` is the first supported AI lane and uses a shared-rule layer under `05_tool-lanes/figma-make/`.
- `stitch` is a downstream visual consumer lane. It reads screen canon + DESIGN.md,
  bootstraps a Stitch design system via MCP, and generates consistent UI screens.
  It writes only under `paths.stitch_lane_root`. See `behavior_stitch_sync`.
