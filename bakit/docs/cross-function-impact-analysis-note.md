# Cross-Function Impact Analysis — Future Design Note

**Origin:** QC-kit gap analysis, 2026-05-29
**Updated:** 2026-05-29 — added cross-module design + resolution rules

## Problem

BA-kit UCs capture trace links (UC → screens → stories) but don't model cross-function relationships:

- Function A output is Function B's input
- Cross-UC workflow ordering (UC-01 must complete before UC-02)
- Impact propagation when Function A changes
- Shared data entities with conflicting read/write access across UCs

QC-kit's KA #8 (Functional Integration Analysis) evaluates this. (Note: QC-kit scores KA #8 at 20pts in its own rubric; BA-kit's `qc-uc-review` scores the equivalent area at 9pts — the point scales are independent.) BA-kit has `srs/spec.md` `## API / Integration Constraints` but that's for external integrations, not internal cross-function analysis.

## Additional Complexity: Cross-Module Dependencies

In multi-BA projects, different BAs own different modules. Module A may finish before Module B. Cross-module dependencies can't be fully resolved at authoring time.

## Design: Produce-First, Resolve-Later

Module A declares what it **produces** for external consumers. Module B (when it eventually exists) declares what it **consumes**. Neither needs the other to exist at authoring time.

### UC Template Addition

```markdown
## Cross-Function Impact

### Within Module
| Direction | UC | Data / State | Type |
|-----------|-----|--------------|------|
| Depends on | UC-cart | cart_id, cart_items | Input |
| Produces for | UC-tracking | order_id, order_status | Output |

### Across Modules
| Direction | Target Module | Expected UC / Backbone Ref | Data / State | Type |
|-----------|---------------|---------------------------|--------------|------|
| Produces for | shipping | FEAT-SHP-01 | order_id, order_status | Output |
| Consumes from | auth | FEAT-AUTH-03 | user_id, token | Input |
```

Three dependency types: Input, Output/Trigger, Shared State.

### Resolution Rules

1. **Intra-module**: BA resolves directly during UC authoring. Full knowledge.

2. **Inter-module "produces for"**: Module A BA writes it. References backbone feature ID. The consuming UC doesn't need to exist yet.

3. **Inter-module "consumes from"**: Module B BA writes it when their module starts. Backbone defines the contract. Module A's existing declarations are hints, not requirements.

4. **Compile time**: Assembler cross-references all modules. If Module A says "produces for shipping: order_id" and Module B's UC-shipment says "consumes from payment: order_id" → resolved. If mismatch → flagged. If one side missing → noted as pending.

5. **Export time** (to QC-kit): Only resolved dependencies appear. Pending ones become "Expected consumer/producer: TBD" — QC-kit treats as known limitation, not a gap.

### Backbone is the Anchor

Backbone (`02_backbone/backbone.md`) already defines cross-module boundaries, shared entities, and feature map. Cross-function declarations just reference backbone IDs. No new coordination protocol needed — backbone IS the protocol.

Module B not finished yet → Module A's external table has TBD entries. That's fine. The analysis is partial by design, not broken.

## Decisions (formerly Open Questions — resolved by implementation)

- **SRS aggregation**: Per-UC inline (not standalone matrix section). Implemented in `skills/ba-start/steps/srs-assembly.md` Step 10.5.
- **ba-impact consumption**: Full propagation with downstream/upstream tracing + reverse inbound scan. Implemented in `core/behavior/impact.md`.
- **QC scoring adjustment**: KA #8 now references `## Cross-Function Impact` section; UCs without it score Partial. Updated in `skills/qc-uc-review/references/scoring-rubric.md`.
- **Module-level dependency graph**: Not produced as standalone artifact — per-UC inline is sufficient.

## Related

- QC-kit repo: https://github.com/Sotatek-PhuongTran/qc-kit
- BA-kit qc-uc-review skill: `skills/qc-uc-review/`
- UC template: `templates/usecase-item-template.md`
- Bridge skill note: `docs/ba-qc-export-bridge-note.md`
