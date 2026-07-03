# Impact Behavior

## Read Scope

- Must read: `core/contract.yaml`, `core/contract-behavior.md`, `paths.intake`, `paths.backbone_index` when present, and `paths.backbone`.
- May read: `paths.project_memory`, `paths.memory_index`, hot shards, selected warm module shard, relevant downstream indexes and artifacts.
- Must not read: `cold/` unless escalated.
- `log.md` may be read only for explicit audit or recent-history requests.

## Routing And Scope

- `impact` is analysis-only until the user approves a mutating rerun path.
- Map each change to the narrowest owning source-of-truth layer: intake/scope lock, backbone, stories, SRS, or wireframes.
- Prefer stable IDs and sections over whole-file rewrites.
- When the change affects UI information architecture or active-menu behavior, include a wireframes follow-up route.
- Emit exact stale artifact paths and the command needed to refresh them.

## Broad-Read Exception

`impact` is the only command that may read across warm module shards by default when Modular or Program activation is detected. Use `paths.memory_index` first and read only routed shards.

## Cross-Function Propagation

When a changed artifact is a UC, extend the impact report with dependency propagation.
Reverse inbound scanning runs for **any changed UC** (even without its own `## Cross-Function Impact` section).
Outbound tracing runs only when the changed UC declares dependencies.

### Reverse Inbound Scan (always runs for changed UC)

1. Scan **other UC files** for reverse inbound edges — UCs that declare "Depends on" or "Consumes from" this UC:
   - **Intra-module**: Read `## Cross-Function Impact` from each sibling UC in the same module
   - **Cross-module**: When Modular/Program activation detected, scan other module UC files for `Consumes from` entries targeting this module
   - Collect entries where Direction = "Depends on" and UC = this UC's ID
   - For `Consumes from` cross-module matches, require at least one of:
     - Backbone ref matches a feature ID this UC's module is known to satisfy
     - Data/State overlaps with this UC's known outputs (from SRS or backbone)
   - Module-only match (Target Module matches but no backbone/data overlap confirmed) → classify as **possible**, not confirmed downstream impact
2. Add confirmed matches to **downstream impact** list. Module-only matches go to **cross-module warnings**.

### Outbound Tracing (only when changed UC has ## Cross-Function Impact)

3. Read `## Cross-Function Impact` from the affected UC.
4. Build **downstream impact** from "Produces for" entries (Within Module + Across Modules):
   - Intra-module: list specific UCs that consume this UC's output, with data/state items
   - Inter-module: flag target modules and backbone feature IDs — consumer may not exist yet
5. Build **upstream impact** from "Depends on" / "Consumes from" entries:
   - Intra-module: list specific UCs this UC depends on, with data/state items
   - Inter-module: flag source modules — upstream change may break this UC's assumptions
6. Classify each impact edge:
   - **Intra-module**: full traceability — affected UCs listed with specific data/state items
   - **Inter-module "produces for"**: warning-level — consumer may not exist yet
   - **Inter-module "consumes from"**: warning if producer UC changes
7. Add to impact report output:

```markdown
### Cross-Function Propagation

**Downstream impact** (UCs that consume this UC's output):
| UC | Module | Data / State | Impact |
|----|--------|--------------|--------|

**Upstream impact** (UCs this UC depends on):
| UC | Module | Data / State | Impact |
|----|--------|--------------|--------|

**Cross-module warnings:**
- {uc_id} produces {data} for module {module} ({backbone_ref}) — module not yet authored
- {module} UC may consume {data} from this UC ({backbone_ref}) — module-only match, not confirmed
```

8. Impact remains read-only — cross-function data is read, never mutated.

## Governance And File-Back

- Verify write authority before recommending mutation.
- Lead BA approves global hot shards, cross-module file-back, and index changes.
- Module owner approves module-local warm shard file-back.
- End-user approval is required when filed-back content changes accepted business scope or policy.
- Ambiguous classification forces explicit end-user approval before file-back.
- Command-level approval alone is not sufficient for file-back.

Filed-back memory items must carry source artifact, source IDs, promotion target, approver, role, approval time, approval basis, approval trigger, impact reference, and supersession fields.

Before mutating `backbone`, `frd`, `stories`, `srs`, or `wireframes`, confirm an approved impact run unless this is first-pass backbone creation or an explicitly approved wording-only rerun. If validation fails, emit `GOVERNANCE_BLOCK: {reason}` and stop.
