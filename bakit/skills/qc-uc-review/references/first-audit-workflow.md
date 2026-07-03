## First Audit Workflow

1. **Ingest & Understand** — read the full module canon set, understand the feature
2. **Audit** — score completeness across all required knowledge areas
3. **Report** — deliver a structured readiness report with verdict, score, gaps, and suggestions

## Phase 1 — Ingest & Understand

### Step 1: Read all artefacts

**Reading order:**
1. `backbone-index.md` / targeted `backbone.md` sections — backbone alignment gate first
2. `shared/definitions.md` — canonical terminology
3. `shared/traceability.md` — coverage map
4. `userstories/index.md` + targeted `userstories/us-*.md` — story intent and AC
5. `usecases/index.md` + `usecases/uc-*.md` — primary functional flows
6. `usecases/diagrams.md` — UC-level diagrams
7. `ascii-screen/index.md` + `ascii-screen/*.md` — primary screen behavior and ASCII evidence
8. `srs/spec.md` — FR/NFR/business rules
9. `srs/flows.md` — module/system flows
10. `srs/states.md` — state registry
11. `srs/erd.md` — data model (if present)
12. `screen-field-contract.yaml` — shared rules, states, validations, navigation
13. Current compiled `srs.md` + `srs-compile-receipt.json` — supporting cross-check only
14. `DESIGN.md`, shared shell contract, or API spec (if available) — supporting evidence only

**Backbone Alignment Gate (before scoring):**
- If module not in backbone → `NOT_READY`
- If actor/portal/feature/rule/term unknown in backbone → `NOT_READY` or critical gap
- If module contradicts backbone → `BACKBONE_ALIGNMENT_FAIL`

**Source-of-truth drift rule:**
- Facts present only in compiled `srs.md` and not in source files score as **Partial** at best, not Clear.
- Compiled-only facts represent source-of-truth drift and must be flagged.

Input-type routing:
| Input Type | Action |
| :--- | :--- |
| Module root | Read canon artifacts in the order above |
| Compiled `srs.md` only | Use as supporting reference; do not treat as sole source if canon artifacts exist |
| Image / mockup | Describe UI elements, labels, and states as supporting evidence only |
| API spec | Use only to understand client-side context inside the active platform boundary |

DO NOT score any knowledge area before finishing all primary canon artifacts.

### Step 2: Synthesise a Feature Understanding

After reading all primary canon artifacts (plus supporting evidence when present), synthesize into 5 sections with **fixed headings**:

---

## 1. UI Object Inventory & Mapping

Build table of all UI components from screen canon and compiled evidence, mapped to use cases:

| # | Component Name | Type | In UC? | In Wireframe? | Notes |
|---|---|---|---|---|---|
| 1 | Example Button | Button | ✅ | ✅ | |

Per component check: display state? action rule? label consistent across use case, screen canon, and compiled SRS?

**Shared Rule Cross-Check:**
- Canon sources do not reference applicable shared rules / contract rules → ⚠️ Partial + question
- Conflict use case vs screen canon / shared rule → 🔴 Conflict + High-priority question

Sub-categories: Data Display (grid/list/table), Controls (filters/search), Navigation (buttons), Others.

---

## 2. Object Attributes & Behavior Definition

- System States: default state per object (Enabled/Disabled/Hidden/Read-only) based on permissions, data conditions
- Interaction Matrix: actions + system responses
- Object Behavior: reactive rules when data/state changes

**Edge Case Checklist** — see platform profile for platform-specific groups. If UC does not mention an item → record gap + question.

> Edge cases only check behavior within the platform boundary. Do NOT deduct points for gaps found here (bonus coverage).

---

## 3. Functional Logic & Workflow Decomposition

Per function (view list, filter, search, create, edit, delete, etc.):

```
[Function Name]
MAIN FLOW: Step 1 → Step 2 → ... → Expected Result
ALTERNATIVE FLOWS: [Alt-1] Condition → Flow → Result
EXCEPTION FLOWS: [Err-1] Error → Displayed message → Behavior
BUSINESS RULES: BR-xxx: [Rule]
UI/UX FEEDBACK: Loading / Toast / Error message
```

Per input/display field:
| Field | Data Type | Required? | Min | Max | Format |
|---|---|---|---|---|---|
Missing info → record as gap. If compiled `srs.md` contains detail absent from canon, record it as a source-of-truth drift warning rather than treating it as Clear evidence.

---

## 4. Functional Integration Analysis

- Impact Analysis: state/data change in one function → affects others?
- Data Consistency: data sync across related UI components after execution

---

## 5. Acceptance Criteria Synthesis

Categorize AC into: Interface (UI), Function, Integration.

---

## Preliminary Gaps Found

Record preliminary missing/conflicting points found in Phase 1 — do not score yet.

---

## Phase 2 — Audit & Phase 3 — Report

→ **Apply the full scoring process, verdict, breakdown, conflict check, blocked protocol, and report format from [`scoring-rubric.md`](scoring-rubric.md).**
