# Hợp đồng component dùng chung cho Figma Make (Figma Make Shared Component Contracts)

## Component rules

| Component Type | Allowed Uses | Forbidden Drift |
| --- | --- | --- |
| Input | Field listed in `screen-field-contract.yaml` | New field, relabel, required-state drift |
| Select / Combo box | Only when contract says option-based input | Extra choices not supported by source |
| Modal / Drawer | Only for primary overlay screens or explicit exceptions | Turning hidden-nav overlay into normal screen |
| Table / List | Only when source states columns, filters, or actions | Inventing actions, filters, bulk ops |

## Validation handling

- Inline errors stay inline when source says inline
- Toast or banner feedback must match source message surface
- Success-only polishing must not remove error and empty states
