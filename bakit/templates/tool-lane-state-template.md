# Trạng thái tool lane (Tool Lane State)

- Slug: [initiative-slug]
- Date: [YYMMDD-HHmm]
- Module: [module-slug]
- Selected lane: `manual`
- Lane state: `ready`
- Approval source: [explicit user choice / lifecycle default / reverse carveout]
- Source screen field contract: `plans/{slug}-{date}/03_modules/{module_slug}/screen-field-contract.yaml`
- Source screen canon ASCII: `plans/{slug}-{date}/03_modules/{module_slug}/ascii-screen/*.md`
- Source design doc: `designs/{slug}/DESIGN.md`
- Stale triggers: [impact on screens, field rules, states, navigation, lane switch]

## Expected downstream artifacts

- `plans/{slug}-{date}/03_modules/{module_slug}/tool-lanes/figma-make/make-guidelines.md` when lane = `figma-make`
- `plans/{slug}-{date}/03_modules/{module_slug}/tool-lanes/figma-make/make-prompt-pack.md` when lane = `figma-make`
- `plans/{slug}-{date}/03_modules/{module_slug}/tool-lanes/figma-make/prototype-conformance-checklist.md` when lane = `figma-make`
- `plans/{slug}-{date}/03_modules/{module_slug}/tool-lanes/figma-make/prototype-conformance-report.md` when lane = `figma-make`
