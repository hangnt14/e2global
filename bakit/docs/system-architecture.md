# BA-kit System Architecture

## Overview

BA-kit uses a contract-first architecture where a single YAML contract (`core/contract.yaml`) defines all paths, commands, states, and quality gates. This contract is the source of truth for the entire system. All runtime behavior flows through behavior shards and step files that implement policy defined in the contract.

**Core Principle:** Contract-first design enables consistent behavior across three runtimes (Claude Code, Codex, Antigravity) without code duplication.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        BA-kit System                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  User Interface Layer                                            │
├─────────────────────────────────────────────────────────────────┤
│  • Natural Language Router (/ba-do)                              │
│  • Project Home Dashboard (PROJECT-HOME.md)                      │
│  • Collaboration Dashboards (COLLAB-HOME.md, MODULE-HOME.md)     │
│  • CLI Helpers (ba-kit doctor, ba-kit status)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Skill Layer (9 Skills)                                          │
├─────────────────────────────────────────────────────────────────┤
│  • ba-start (main lifecycle)                                     │
│  • ba-do (intent router)                                         │
│  • ba-next (resume + guidance)                                   │
│  • ba-impact (change analysis)                                   │
│  • ba-collab (module collaboration)                              │
│  • brainstorm (pre-intake interview)                             │
│  • qc-uc-review (UC/SRS audit)                                   │
│  • ba-notion (Notion publishing)                                 │
│  • ba-kit-update (self-update)                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Workflow Orchestration Layer                                    │
├─────────────────────────────────────────────────────────────────┤
│  • Lifecycle State Machine (intake → backbone → FRD → SRS → ...)│
│  • Change Impact Triage (impact.md)                              │
│  • Resume + Next-Step Logic (next.md)                            │
│  • Natural Language Routing (do.md)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Behavior Shard Layer (9 Shards)                                 │
├─────────────────────────────────────────────────────────────────┤
│  • intake.md (elicitation rules)                                 │
│  • backbone.md (authoring rules)                                 │
│  • module-authoring.md (module artifact rules)                   │
│  • srs.md (SRS/UC/screen spec rules)                             │
│  • wireframes.md (wireframe constraint rules)                    │
│  • package-status-next.md (packaging + status + next)            │
│  • impact.md (change triage rules)                               │
│  • qc-review.md (QC audit rules)                                 │
│  • reverse.md (as-built documentation rules)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Contract Layer (Single Source of Truth)                         │
├─────────────────────────────────────────────────────────────────┤
│  • contract.yaml (paths, commands, states, gates, thresholds)    │
│  • contract-behavior.md (shared runtime-neutral policy)          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Artifact Generation Layer                                       │
├─────────────────────────────────────────────────────────────────┤
│  • Templates (37 files)                                          │
│  • Scripts (39 files: validation, conversion, automation)        │
│  • Agents (4 specialized roles)                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Artifact Storage Layer                                          │
├─────────────────────────────────────────────────────────────────┤
│  • Project Root: plans/{slug}-{date}/                            │
│  • Intake: 01_intake/                                            │
│  • Backbone: 02_backbone/                                        │
│  • Modules: 03_modules/{module_slug}/                            │
│  • Compiled: 04_compiled/                                        │
│  • Design: designs/{slug}/DESIGN.md                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Runtime Adapters (3 Runtimes)                                   │
├─────────────────────────────────────────────────────────────────┤
│  • Claude Code (native ~/.claude/)                               │
│  • Codex (repo-native AGENTS.md)                                 │
│  • Antigravity (CLI + Knowledge Item)                            │
└─────────────────────────────────────────────────────────────────┘
```

## Lifecycle State Machine

```
START
  ↓
[Intake] ← User provides raw input
  ↓
  ├─→ Gap Analysis
  ├─→ Open Questions Tracking
  └─→ PROJECT-HOME.md (resume point)
  ↓
[Options] ← If intake shows multiple solution paths
  ↓
  ├─→ Generate option pack (1-3 options)
  ├─→ Comparison matrix
  └─→ User selects or skips
  ↓
[Backbone] ← Scope lock + source of truth
  ↓
  ├─→ Vocabulary (canonical terms)
  ├─→ Decisions (approved choices)
  ├─→ Assumptions (stated preconditions)
  ├─→ Project Memory (hot/warm/cold shards)
  └─→ COLLAB-HOME.md (if modular)
  ↓
[FRD] ← Functional requirements (per module)
  ↓
  ├─→ Business objectives
  ├─→ Capabilities (P0/P1/P2)
  └─→ Dependencies
  ↓
[Stories] ← User stories + acceptance criteria
  ↓
  ├─→ As a / I want / so that format
  ├─→ Acceptance criteria (SMART)
  └─→ Input to module SRS authoring
  ↓
[SRS] ← System requirements specification
  ↓
  ├─→ Functional requirements (FR-*)
  ├─→ Non-functional requirements (NFR-*)
  ├─→ Business rules (BR-*)
  ├─→ Use cases (UC-*)
  ├─→ Screen specifications (SCR-*)
  ├─→ Error codes (E-*)
  └─→ `srs.md` + `srs-compile-receipt.json`
  ↓
[Module QC] ← Automatic canon-first readiness audit
  ↓
  ├─→ Reads `srs-index.md`, `usecases/*.md`, `screens/*.md`
  ├─→ Reads `screen-field-contract.yaml`
  ├─→ Uses compiled `srs.md` as supporting evidence
  ├─→ Writes `03_modules/{module}/qc-review/*`
  └─→ May go directly to package when no UI handoff lane is needed
  ↓
[ASCII Wireframes] ← Required screen-canon visual coverage
  ↓
  ├─→ DESIGN.md (design system)
  ├─→ screens/*.md (ASCII by state)
  └─→ srs-compile-receipt.json
  ↓
[Package] ← Compiled HTML deliverables
  ↓
  ├─→ compiled-frd.html
  ├─→ compiled-srs.html
  ├─→ Traceability matrix
  └─→ Aggregate validation across emitted artifacts
  ↓
END (Ready for stakeholder handoff)
```

## Quality And Validation System

```
┌──────────────────────────────────────────────────────────────┐
│                 Module QC Gate: Post-SRS Module Audit         │
├──────────────────────────────────────────────────────────────┤
│ Trigger:     After module SRS completed                      │
│ Profile:     Full 10-point audit                             │
│ Evidence:    • srs-index.md                                  │
│              • usecases/*.md + screens/*.md                  │
│              • screen-field-contract.yaml                    │
│              • compiled srs.md as supporting reference       │
│ Block If:    Score < 70                                      │
│ Auto-Remedy: Max 2 retries, fix canon sources first          │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│               Downstream UI Lane: Wireframes / Figma          │
├──────────────────────────────────────────────────────────────┤
│ Trigger:     After SRS and module QC when UI support is needed│
│ Purpose:     Manual handoff / downstream visual sync only    │
│ QC Note:     No auto `qc-review` gate fires after wireframes │
│ Source:      Canon screen/use case files remain the truth    │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│                  Package Validation Boundary                  │
├──────────────────────────────────────────────────────────────┤
│ Trigger:     During `package` compile/validate run           │
│ Scope:       Whole-system aggregate HTML handoff             │
│ Criteria:    • UC steps match screen actions (same wording)  │
│              • Screen fields match UC data (same names)      │
│              • Error messages consistent (MSG-* codes)       │
│              • Business rules consistent (BR-* codes)        │
│              • Traceability complete (no orphaned items)     │
│              • Links valid (no broken references)            │
│              • Wireframes attached (if UI-backed)            │
│ Block If:    Package validation detects blockers             │
│ Auto-Remedy: None. Fix upstream canon artifacts first        │
└──────────────────────────────────────────────────────────────┘
```

## Memory Tier System

```
┌─────────────────────────────────────────────────────────────┐
│                    Project Memory Tiers                       │
└─────────────────────────────────────────────────────────────┘

HOT SHARD (Always in memory)
├── canonical-vocabulary.md
│   └── Approved terms + definitions (global, immutable)
├── approved-decisions.md
│   └── Locked decisions (scope, timeline, budget, tech stack)
└── pushback-triggers.md
    └── Known objections + responses

WARM SHARDS (Per-module, mutable)
├── modules/{module_slug}.md
│   ├── Module scope + ownership
│   ├── Module-specific decisions
│   ├── Module dependencies
│   └── Module review status

COLD SHARDS (Archived, reference only)
├── archived-options.md
│   └── Rejected solution paths + rationale
├── archived-decisions.md
│   └── Superseded decisions + history
└── archived-assumptions.md
    └── Invalidated assumptions + corrections
```

**Activation Levels:**

| Level | Trigger | Memory | Collaboration |
|-------|---------|--------|---------------|
| **Base** | Single project | Hot shard only | None |
| **Modular** | ≥2 modules OR ≥2 owners | Hot + warm shards | COLLAB-HOME.md, MODULE-HOME.md |
| **Program** | Cross-module deps OR ≥2 delegation slices | Hot + warm + cold | Full delegation tracking |

## Artifact Profiles

```
┌─────────────────────────────────────────────────────────────┐
│              Artifact Profile Classification                  │
└─────────────────────────────────────────────────────────────┘

MACHINE-FACING (JSON/NDJSON, structured for automation)
├── source-manifest.json
│   └── Source code inventory + metadata
├── reverse-baseline-lock.json
│   └── Commit hash + evidence snapshot
├── reverse-drift-state.json
│   └── Change tracking vs. baseline
└── reverse-read-manifest.ndjson
    └── Evidence ledger (one entry per line)

AGENT-FACING (Markdown, structured for LLM processing)
├── backbone-index.md
│   └── Backbone table of contents
├── user-stories-index.md
│   └── Story inventory + status
├── srs-index.md
│   └── SRS section inventory
├── review-packet.md
│   └── Module review handoff
└── reverse-index.md
    └── As-built documentation index

USER-FACING (Markdown, readable dashboards)
├── PROJECT-HOME.md
│   └── BA-facing resume + next-step guidance
├── COLLAB-HOME.md
│   └── Collaboration status + module ownership
├── MODULE-HOME.md
│   └── Module BA dashboard + checklist
├── intake.md
│   └── Intake normalization + gap analysis
├── backbone.md
│   └── Requirements backbone (source of truth)
├── frd.md
│   └── Functional requirements
├── user-stories.md
│   └── User stories + acceptance criteria
├── srs.md
│   └── System requirements specification
├── screens/
│   └── scr-*.md (mandatory ASCII wireframes)
└── compiled-*.html
    └── Stakeholder review packages
```

## Change Impact Analysis Flow

```
User reports change:
"Export CSV must have audit log"
        ↓
[Impact Skill]
        ↓
Classify change layer:
├─ Intake layer? (scope change)
├─ Backbone layer? (decision change)
├─ Module layer? (feature change)
└─ Artifact layer? (requirement change)
        ↓
Identify affected artifacts:
├─ If backbone: FRD, stories, SRS, wireframes
├─ If module: SRS, wireframes, compiled packages
├─ If artifact: downstream artifacts only
└─ If cross-module: flag for Lead BA review
        ↓
Generate impact receipt:
├─ Change summary
├─ Affected layers
├─ Rerun strategy
└─ Estimated effort
        ↓
Recommend rerun:
├─ Rerun FRD? (if backbone changed)
├─ Rerun stories? (if FRD changed)
├─ Rerun SRS? (if stories changed)
└─ Rerun wireframes? (if SRS changed)
        ↓
User approves rerun
        ↓
Execute rerun with change context
```

## Reverse Mode (As-Built Documentation)

```
START (Source code exists)
        ↓
[Reverse Preflight]
├─ Scan source code
├─ Create baseline lock (commit hash + evidence snapshot)
└─ Generate reverse-baseline-lock.json
        ↓
[Reverse Index]
├─ Extract evidence from code:
│  ├─ Database schema (tables, columns, constraints)
│  ├─ API endpoints (routes, methods, parameters)
│  ├─ Business logic (rules, validations, workflows)
│  ├─ Error handling (error codes, messages)
│  └─ Integrations (external services, webhooks)
├─ Generate reverse-index.md
└─ Generate reverse-evidence-ledger.md
        ↓
[Reverse Drift Check]
├─ Compare current code vs. baseline
├─ Detect changes:
│  ├─ Added features
│  ├─ Removed features
│  ├─ Modified behavior
│  └─ Bug fixes
└─ Generate reverse-drift-state.json
        ↓
[Reverse Promote]
├─ Only promote content with clear evidence
├─ No speculation about business intent
├─ No future-state requests
├─ Generate backbone.md (as-built)
└─ Generate reverse-focus-excerpts.md
        ↓
END (As-built SRS ready for review)
```

## Guardrail System (Index-First Reads)

```
┌─────────────────────────────────────────────────────────────┐
│              Index-First Read Enforcement                     │
└─────────────────────────────────────────────────────────────┘

User requests: "Read SRS and find all FR-payment-* requirements"
        ↓
[Guardrail Preflight]
├─ Check if srs-index.md exists
├─ If yes: use index to locate FR-payment-* entries
├─ If no: generate index first
        ↓
[Guardrail Build Excerpts]
├─ Extract only relevant sections from SRS
├─ Build excerpt file (srs-excerpts.md)
├─ Include context (section headers, related items)
        ↓
[Guardrail Audit]
├─ Validate excerpt quality
├─ Check for completeness
├─ Verify no orphaned references
        ↓
Return excerpts (not full SRS)
        ↓
Benefits:
├─ Reduced token usage (excerpts vs. full files)
├─ Faster processing (index lookup vs. full scan)
├─ Consistent discovery (index is canonical)
└─ Audit trail (what was read, when, why)
```

## Runtime Adapter Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Runtime Adapter Pattern                          │
└─────────────────────────────────────────────────────────────┘

Core BA-kit (Contract + Behavior + Skills)
        ↓
        ├─→ Claude Code Adapter
        │   ├─ ~/.claude/skills/ba-start/
        │   ├─ ~/.claude/skills/ba-do/
        │   └─ ~/.claude/CLAUDE.md
        │
        ├─→ Codex Adapter
        │   ├─ AGENTS.md (repo-native)
        │   ├─ codex/agents/
        │   └─ codex/skills/
        │
        └─→ Antigravity Adapter
            ├─ CLI (ba-kit command)
            ├─ Knowledge Item workflow
            └─ install-antigravity-ba-kit.sh

All adapters:
├─ Read same contract.yaml
├─ Execute same behavior shards
├─ Use same templates
├─ Generate same artifacts
└─ Produce identical output
```

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    User Input                                 │
│  (raw requirements, change request, resume request)           │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│              Natural Language Router (/ba-do)                 │
│  Maps intent to workflow (intake, impact, next, collab)       │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│            Resolve Project Context                            │
│  • Slug (from --slug or disk inspection)                      │
│  • Date (from --date or project directory)                    │
│  • Module (from --module or single module detection)          │
│  • Mode (from --mode or defaults.mode)                        │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│            Load Contract + Behavior                           │
│  • contract.yaml (paths, commands, states)                    │
│  • contract-behavior.md (shared policy)                       │
│  • behavior/{command}.md (command-specific policy)            │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│            Check Prerequisites                                │
│  • Verify required artifacts exist                            │
│  • Resolve exact file paths                                   │
│  • Load upstream artifacts if needed                          │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│            Execute Workflow Step                              │
│  • Load step file (skills/ba-start/steps/{step}.md)           │
│  • Execute step logic                                         │
│  • Apply quality gates if applicable                          │
│  • Generate or update artifacts                               │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│            Validate Output                                    │
│  • Run validation scripts                                     │
│  • Check cross-references                                     │
│  • Verify frontmatter                                         │
│  • Generate validation receipt                                │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│            Update Project State                               │
│  • Update PROJECT-HOME.md                                     │
│  • Update COLLAB-HOME.md (if modular)                         │
│  • Update MODULE-HOME.md (if module BA)                       │
│  • Update project memory (hot/warm/cold shards)               │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│            Return Results to User                             │
│  • Summary of changes                                         │
│  • Next-step recommendations                                  │
│  • Links to generated artifacts                               │
│  • Any blockers or warnings                                   │
└──────────────────────────────────────────────────────────────┘
```

## Module Collaboration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Module Collaboration Flow                        │
└─────────────────────────────────────────────────────────────┘

Lead BA divides work:
├─ Module 1: checkout (owner: @alice)
├─ Module 2: auth (owner: @bob)
└─ Module 3: reporting (owner: @charlie)
        ↓
COLLAB-HOME.md (Lead BA view)
├─ Module ownership matrix
├─ Review status per module
├─ Blockers and dependencies
└─ GitHub PR status
        ↓
Module BA claims module:
"I'll take module checkout"
        ↓
MODULE-HOME.md (Module BA view)
├─ Module scope + constraints
├─ Checklist (FRD → stories → SRS → wireframes)
├─ Review status
└─ Conflict warnings
        ↓
Module BA creates artifacts:
├─ frd.md (functional requirements)
├─ user-stories.md (user stories)
├─ srs.md (system requirements)
└─ screens/*.md (mandatory ASCII wireframes)
        ↓
Module BA requests review:
"Send module checkout for review"
        ↓
Review Packet Generated:
├─ Module summary
├─ Artifact diffs
├─ Quality gate results
├─ Cross-module dependencies
└─ Conflict warnings
        ↓
Lead BA reviews:
├─ Approve (merge into backbone)
├─ Request changes (send feedback)
└─ Block (flag conflict)
        ↓
If approved:
├─ Merge module artifacts into backbone
├─ Update COLLAB-HOME.md
├─ Optional: Create GitHub PR (approval-gated)
└─ Module marked "completed"
```

## Quality Gate Scoring (Post-SRS Module QC)

```
10-Point Audit Scoring:

1. Completeness (0-10)
   └─ All sections present? All requirements documented?

2. Clarity (0-10)
   └─ No ambiguous language? Clear acceptance criteria?

3. Consistency (0-10)
   └─ No contradictions? Terminology consistent?

4. Traceability (0-10)
   └─ Goals → FR → AC → test cases linked?

5. Acceptance (0-10)
   └─ Stakeholders signed off? No pending approvals?

6. Feasibility (0-10)
   └─ No impossible requirements? Tech stack supports?

7. Testability (0-10)
   └─ All AC testable? No subjective criteria?

8. Prioritization (0-10)
   └─ P0/P1/P2 assigned? Clear priority order?

9. Dependencies (0-10)
   └─ External deps documented? Risks identified?

10. Risks (0-10)
    └─ Known risks flagged? Mitigation planned?

Total Score = (Sum of 10 scores) / 10

Block if: Score < 70
Auto-remedy: Max 2 retries (address low-scoring sections)
```

## Integration Points

```
External Systems:
├─ GitHub (optional PR/merge workflow)
├─ Notion (optional artifact publishing)
├─ Jira (optional issue sync)
└─ Design tools (Figma, Pencil, etc.)

Integration Pattern:
├─ BA-kit generates artifacts (markdown)
├─ User optionally exports to external system
├─ External system is NOT source of truth
├─ Changes flow back through impact analysis
└─ Backbone remains canonical
```

## Error Handling & Recovery

```
Quality Gate Failure:
├─ Gate blocks artifact emission
├─ Generate detailed failure report
├─ Suggest remediation steps
├─ Allow max 2 auto-retries
├─ If still failing: escalate to user
└─ User can override (with warning)

Missing Prerequisite:
├─ Print exact missing path
├─ Suggest prior command to run
├─ Stop execution
└─ Do not guess or infer

Conflict Detection:
├─ Cross-module dependency detected
├─ Flag in review packet
├─ Require Lead BA approval
├─ Do not auto-merge
└─ Escalate to user

Ambiguous Resolution:
├─ Multiple projects with same slug
├─ Multiple modules in project
├─ Multiple dated sets for slug
├─ Stop and ask user to clarify
└─ Do not guess
```

## Performance Considerations

**Token Efficiency:**
- Index-first reads (guardrail system) reduce token usage
- Excerpt building extracts only relevant sections
- Lazy loading of upstream artifacts
- Caching of contract + behavior shards

**Scalability:**
- Modular architecture supports large projects (100+ modules)
- Warm shards per module (not monolithic memory)
- Delegation tracking for parallel work
- Artifact splitting (SRS groups A-F) for large specs

**Concurrency:**
- Module-based collaboration (no file conflicts)
- Git worktrees for parallel branches
- Review packets for async approval
- Conflict detection prevents silent overwrites
