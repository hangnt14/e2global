# Figma Make Sample Bundle

Sample này minh họa artifact split cho một module representative. Dùng synthetic names, không nằm trong runtime `plans/`.

## Example module

- Slug: `ops-suite`
- Date: `260522-1030`
- Module: `complaint-intake`

## Expected generated artifacts

- `plans/ops-suite-260522-1030/03_modules/complaint-intake/screen-field-contract.yaml`
- `plans/ops-suite-260522-1030/03_modules/complaint-intake/tool-lanes/tool-lane-state.md`
- `plans/ops-suite-260522-1030/05_tool-lanes/figma-make/shared-rules.md`
- `plans/ops-suite-260522-1030/03_modules/complaint-intake/tool-lanes/figma-make/make-guidelines.md`
- `plans/ops-suite-260522-1030/03_modules/complaint-intake/tool-lanes/figma-make/make-prompt-pack.md`
- `plans/ops-suite-260522-1030/03_modules/complaint-intake/tool-lanes/figma-make/prototype-conformance-checklist.md`
- `plans/ops-suite-260522-1030/03_modules/complaint-intake/tool-lanes/figma-make/prototype-conformance-report.md`

## Example control lines

`screen-field-contract.yaml`

```yaml
shared_constraints:
  no_extra_fields: true
  no_nav_changes: true
```

`make-prompt-pack.md`

```text
Do not add fields not listed
Do not add screens not listed
Do not change top-level navigation
If a rule is missing, omit instead of inventing
```

## Review expectation

- Reviewer phải check extra field, missing field, state drift, validation surface drift, và active-menu drift.
- Nếu prototype cần đổi requirement, route về `ba-start impact` thay vì sửa prompt lặng lẽ.
