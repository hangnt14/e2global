# Scoring Rubric & Report Rules (Shared)

> Shared file for both First Audit and Re-Audit. Each workflow keeps its own steps and references this file for scoring + report format.
> Platform-specific subject framing rules (e.g., "App/Client as subject") are defined in the platform profile, not here.

---

## Bảng 10 Knowledge Area

| # | Knowledge Area | Max Pts | Critical? |
|---|---|:---:|:---:|
| 1 | Feature Identity | 4 | Yes |
| 2 | Objective & Scope | 4 | Yes |
| 3 | Actors & User Roles | 9 | Yes |
| 4 | Preconditions & Postconditions | 9 | Yes |
| 5 | UI Object Inventory & Mapping | 14 | Yes |
| 6 | Object Attributes & Behavior Definition | 18 | Yes |
| 7 | Functional Logic & Workflow Decomposition | 18 | Yes |
| 8 | Functional Integration Analysis | 9 | Yes |
| 9 | Acceptance Criteria | 10 | Yes |
| 10 | Non-functional Requirements | 5 | No |

**Total = 100 points. Raw score = Final score. No normalization.**

---

## Nguyên tắc chấm điểm

1. Score each sub-item then sum — do NOT estimate the whole KA.
2. Only use the exact Clear/Partial/Missing values from the sub-item table below. Scores are always integers.
3. Criterion: Does the tester have enough info to write a test case?
4. Do NOT deduct points for gaps found at Edge Case Checklist (bonus coverage).
5. Uncertain Clear↔Partial → choose **Partial**. Uncertain Partial↔Missing → choose **Missing**.
6. Each sub-item MUST record evidence (`UC §X.Y` / `ascii-screen/SCR-NN §X.Y` / `userstories/US-NNN` / `srs/spec.md §X.Y` / `Rule-ID`) + 1-sentence reason. Evidence from compiled `srs.md` only scores as Partial, not Clear.

---

## Định nghĩa mức Clear / Partial / Missing

### ✅ Clear — full sub-item points

- Information is explicit, **no inference required**.
- Do NOT use vague words: "appropriate", "reasonable", "should", "can", "may".
- Content is specific and verifiable (has numbers, enums, specific names, clear conditions).
- Tester can design test cases immediately WITHOUT asking the BA.

### ⚡ Partial — partial points (see "Partial" column in KA table)

- Has description but is vague, uses unmeasurable language.
- Only inferable from supporting artefacts / mockups / context — NOT written explicitly in canon sources.
- Contradicts another artefact on the same point.
- Has correct content but missing necessary boundary cases.

### ❌ Missing — 0 points

- Completely absent from all artefacts.
- Has content but is entirely wrong relative to actual behavior or shared rules.
- Required artefact is BLOCKED making the sub-item unassessable.

### Quy tắc phân vân

- Clear ↔ Partial → choose **Partial**.
- Partial ↔ Missing → choose **Missing**.

---

## Sub-item Breakdown từng KA

### KA #1 — Feature Identity (4đ, Critical)

| Sub-item | Clear | Partial | Tiêu chí Clear |
|---|:---:|:---:|---|
| 1.1 UC-ID + Feature name | 1 | 0 | ID and name consistent between header and content |
| 1.2 UC version + Date created | 1 | 0 | Has version + date; consistent |
| 1.3 Module + Function type | 1 | 0 | e.g., Mobile App / Navigation & Overview |
| 1.4 BA owner + Context | 1 | 0 | Has BA name and UC position in system |

### KA #2 — Objective & Scope (4đ, Critical)

| Sub-item | Clear | Partial | Tiêu chí Clear |
|---|:---:|:---:|---|
| 2.1 Objective (WHY) | 2 | 1 | Clearly describes business problem + beneficiary |
| 2.2 In-Scope list | 1 | 0 | Lists all functions/sub-functions completely |
| 2.3 Out-of-Scope list | 1 | 0 | Explicitly states what is NOT in scope |

### KA #3 — Actors & User Roles (9đ, Critical)

| Sub-item | Clear | Partial | Tiêu chí Clear |
|---|:---:|:---:|---|
| 3.1 Primary Actors list | 3 | 1 | Complete list, classified Primary/System/External |
| 3.2 Permissions / Role | 3 | 1 | Role defined; behavioral differences between roles stated |
| 3.3 Permission rules | 2 | 1 | Each actor: what they can interact with / see |
| 3.4 Fallback when role outside enum | 1 | 0 | Role not in enum → how does UI handle it? |

### KA #4 — Preconditions & Postconditions (9đ, Critical)

| Sub-item | Clear | Partial | Tiêu chí Clear |
|---|:---:|:---:|---|
| 4.1 Preconditions — Entry point | 3 | 1 | UC activation conditions are clear |
| 4.2 Preconditions — System state | 2 | 1 | Required system/data state before start |
| 4.3 Postconditions — Success state | 3 | 1 | State after happy path completes |
| 4.4 Postconditions — Data changes | 1 | 0 | All data/session changes after completion |

### KA #5 — UI Object Inventory & Mapping (14đ, Critical)

| Sub-item | Clear | Partial | Tiêu chí Clear |
|---|:---:|:---:|---|
| 5.1 Complete component list | 5 | 2 | Every relevant component / endpoint in canon sources is inventoried |
| 5.2 Use case ↔ canon consistency | 3 | 1 | Label names, positions, component types, or endpoint contracts match between use cases and canon sources |
| 5.3 State / Action / Label per component | 3 | 1 | Each component has: default state, interaction rule, and label in canon evidence |
| 5.4 Shared rule cross-check | 3 | 1 | All applicable shared rules / rule IDs are referenced in canon sources |

**Rule 5.4:** ≥85% shared-rule coverage → Clear (3pts). 50–<85% → Partial (1pt). <50% → Missing (0pts).

### KA #6 — Object Attributes & Behavior Definition (18đ, Critical)

| Sub-item | Clear | Partial | Tiêu chí Clear |
|---|:---:|:---:|---|
| 6.1 System States | 5 | 2 | Each component has default state + change conditions |
| 6.2 Interaction Matrix | 5 | 2 | Each component has interaction matrix + responses |
| 6.3 Object Behavior (reactive rules) | 4 | 2 | Reactive rules when data/state changes |
| 6.4 Edge Case Coverage | 4 | 2 | Platform edge case groups covered by UC |

**Rule 6.4:** ≥70% items covered → Clear (4pts). 40–<70% → Partial (2pts). <40% → Missing (0pts).
Edge case groups are defined in the platform profile.

### KA #7 — Functional Logic & Workflow Decomposition (18đ, Critical)

| Sub-item | Clear | Partial | Tiêu chí Clear |
|---|:---:|:---:|---|
| 7.1 Main Flow (Happy Path) | 5 | 2 | Each sub-function has complete main flow steps |
| 7.2 Alternative Flows | 4 | 2 | Alternative flows covered |
| 7.3 Exception & Error Flows | 3 | 1 | Error handling for all interactions (platform-side) |
| 7.4 Business Rules & Validation | 3 | 1 | Enum values, constraints, validation |
| 7.5 UI/UX Feedback | 3 | 1 | Loading states, toast messages, error wording |

### KA #8 — Functional Integration Analysis (9đ, Critical)

| Sub-item | Clear | Partial | Tiêu chí Clear |
|---|:---:|:---:|---|
| 8.1 Impact Analysis | 3 | 1 | UC declares within-module dependencies in `## Cross-Function Impact` → Within Module table with specific data/state items; dependency type matches direction |
| 8.2 Data Consistency | 3 | 1 | UC declares across-module dependencies in `## Cross-Function Impact` → Across Modules table with backbone feature IDs; data source→consumer chain traceable |
| 8.3 Section-level error isolation | 3 | 1 | UC declares Shared State entities where applicable; conflicting read/write access identifiable from declarations |

**Cross-function evidence rules:**
- UC has `## Cross-Function Impact` section with at least one table → evidence source is the section
- Within Module table has ≥1 entry OR explicit "None" marker → 8.1 eligible for Clear
- Across Modules table has ≥1 non-None entry with backbone refs OR explicit "None" marker → 8.2 eligible for Clear
- Shared State entries declare which entity and which UCs share access → 8.3 eligible for Clear
- UC missing `## Cross-Function Impact` entirely → all KA #8 sub-items score **Partial** (reviewer infers from UC text)

### KA #9 — Acceptance Criteria (10đ, Critical)

| Sub-item | Clear | Partial | Tiêu chí Clear |
|---|:---:|:---:|---|
| 9.1 Explicit AC in UC | 4 | 2 | UC has AC section written by BA; NOT inferred by skill |
| 9.2 Measurable AC (pass/fail) | 3 | 1 | Each AC is verifiable (no "should", "may") |
| 9.3 AC covers UI/Functional/Integration | 3 | 1 | AC clearly categorized into 3 groups, covers main + error flows |

**Note:** If original UC has no AC section but skill infers → 9.1 scored as **Partial (2pts)**.

### KA #10 — Non-functional Requirements (5đ, Non-critical)

| Sub-item | Clear | Partial | Tiêu chí Clear |
|---|:---:|:---:|---|
| 10.1 Performance | 1 | 0 | Has time target (timeout, response SLA) |
| 10.2 Security | 1 | 0 | Session management, HTTPS, authentication |
| 10.3 Accessibility | 1 | 0 | Specific target (WCAG, touch target size, contrast) |
| 10.4 Compatibility | 1 | 0 | OS versions, screen orientations, device types |
| 10.5 Reliability | 1 | 0 | Error isolation, retry behavior, fallback |

> KA #10 is Pass/Fail only (1pt/0pt), no Partial.

---

## Auto-fail Rule

If any Critical KA (#1–#9) scores **0 for the entire KA** → verdict = ❌ NOT READY regardless of total score.

- Only triggers when the ENTIRE KA = 0, NOT when a single sub-item = 0.
- KA #10 (non-critical) does not trigger auto-fail.

---

## Verdict

| Score | Verdict |
|:---:|---|
| `[85, 100]` | ✅ **READY** — QA can start test design immediately |
| `[70, 85)` | ⚡ **CONDITIONALLY READY** — start on clear areas, resolve gaps in parallel |
| `[0, 70)` | ❌ **NOT READY** — too many gaps, do not start |

> `[a, b]` includes both a and b. `[a, b)` includes a, does NOT include b.

---

## Breakdown chi tiết (BẮT BUỘC)

For each KA, MUST output breakdown table:

```markdown
### KA #N — [KA Name] ([total]pts)
| Sub-item | Max | Score | Status | Evidence / Reason |
|---|:---:|:---:|:---:|---|
| N.1 [name] | X | x | ✅/⚡/❌ | UC §X.Y / SCR §X.Y / Rule-ID / Missing |

**Subtotal KA #N: Y/Total — ✅/⚡/❌**
**Evaluation:** [1 line — main reason]
```

---

## Cross-Artefact Conflict Check

Only flag conflicts that **affect the platform boundary** (defined in platform profile):
- Use case flow contradicts screen canon or compiled SRS?
- API spec has a field / endpoint behavior not reflected in module canon?
- Screen / endpoint element in canon has no business rule or shared-rule reference?
- Label/field name inconsistent across use cases, screens, contracts, or supporting design?

Conflicts → automatic Warnings.

---

## Blocked Artefact Protocol

Artefact not accessible:
- Mark dependent KA = `[BLOCKED]`, score = 0
- Surface as 🔴 Blocker in report
- Do NOT infer content from unavailable artefact

---

## Report Format

**Status markers:** ✅ Complete · ⚡ Partial · ⚠️ Missing · *(inferred)*

### 📊 Audit Summary

| # | Knowledge Area | Max | Score | Status |
|---|---|:---:|---|---|
| 1 | Feature Identity | 4 | X/4 | ✅/⚡/⚠️ |
| 2 | Objective & Scope | 4 | X/4 | ✅/⚡/⚠️ |
| 3 | Actors & User Roles | 9 | X/9 | ✅/⚡/⚠️ |
| 4 | Preconditions & Postconditions | 9 | X/9 | ✅/⚡/⚠️ |
| 5 | UI Object Inventory & Mapping | 14 | X/14 | ✅/⚡/⚠️ |
| 6 | Object Attributes & Behavior Definition | 18 | X/18 | ✅/⚡/⚠️ |
| 7 | Functional Logic & Workflow Decomposition | 18 | X/18 | ✅/⚡/⚠️ |
| 8 | Functional Integration Analysis | 9 | X/9 | ✅/⚡/⚠️ |
| 9 | Acceptance Criteria | 10 | X/10 | ✅/⚡/⚠️ |
| 10 | Non-functional Requirements | 5 | X/5 | ✅/⚡/⚠️ |
| **Total** | | **100** | | **XX/100** |

### Section-Level Scoring (BẮT BUỘC cuối mỗi Mục 0-9)

```markdown
---
**Đánh giá KA #N ([KA Name]):** Y/Total — ✅ Clear | ⚡ Partial | ❌ Missing
[1 sentence main reason]
---
```

### 📋 Unified Gap & Question Report

| ID | Priority | Ref | Question | Why It Matters | Status |
|---|---|---|---|---|---|
| Q1 | High/Medium/Low | Excerpt or "N/A (Missing)" | What needs clarification | Impact on testability | Open |

Priority: 🔴 High = blocker (critical KA = 0). ⚠️ Medium = conflict/partial. 🟡 Low = suggestion/non-critical.
Sort descending by priority.

### 🟢 What's Good

Bullet 1 line / 1 point. Credit all ✅ Complete items.

### 🧪 Testability Outlook

- **CAN test now:** [areas with enough info]
- **CANNOT test yet:** [areas blocked by gaps + gap ID reference]
- **Focus areas once resolved:** Happy path, alternative scenarios, boundary/validation, error/exception, UI checks, shared-rule compliance, edge cases

### 📌 Summary & Recommendation

4-6 sentences: (a) overall status, (b) 2-3 main actions, (c) clear recommendation (pause / fix then continue / proceed now).

---

## Common Gap Patterns

| Gap Pattern | Sign | Example Question |
|---|---|---|
| No preconditions | UC starts from step 1 | "What conditions must be true before [X]?" |
| Vague actor | Only "user" | "Specific role? Different behavior between roles?" |
| Missing validation | Input fields, no constraints | "What does [X] accept? Min/Max? Error message?" |
| Generic error message | "show error" | "Exact message for [X]?" |
| AC not measurable | "should"/"can" | "Rewrite [X] as pass/fail?" |
| Screen/supporting-design element not in canon | Shared-rule cross-check | "Which canon rule or screen behavior does element [X] correspond to?" |
| Canon source does not ref shared rule | No linked rule/message ID | "Does this flow apply a shared rule or message code?" |
| Partial API failure | Only full-screen error | "When [A] fails + [B] OK, how does UI handle it?" |
| No debounce | Nav without interaction guard | "Trigger twice quickly, navigate twice?" |
| i18n no persistence | Language switch, no storage rule | "Where is language stored? Persists after logout?" |
| No cross-function declarations | UC missing `## Cross-Function Impact` section | "Which UCs does this depend on? What does this UC produce for others?" |
| Vague cross-function data | "order data" instead of specific items | "Exactly which data/state items flow between these UCs?" |
