# BA-kit Codebase Summary

## Overview

BA-kit is a contract-first BA toolkit with ~32K LOC across 251 files. The codebase is organized around a single source of truth (`core/contract.yaml`) that defines paths, commands, states, and quality gates. All runtime behavior flows from this contract through behavior shards and step files.

**Key Principle:** Contract-first design means the YAML contract is authoritative for paths, thresholds, and command metadata. Behavior files implement policy. Skills and scripts execute workflows.

## Directory Structure

```
BA-kit/
├── core/                          # Contract + behavior system (786 LOC)
│   ├── contract.yaml              # Single source of truth (456 LOC)
│   ├── contract-behavior.md       # Shared runtime-neutral policy (330 LOC)
│   ├── behavior/                  # 9 command-specific shards
│   │   ├── intake.md              # Intake elicitation rules
│   │   ├── backbone.md            # Backbone authoring rules
│   │   ├── module-authoring.md    # Module artifact rules
│   │   ├── srs.md                 # SRS/UC/screen spec rules
│   │   ├── wireframes.md          # Wireframe constraint rules
│   │   ├── package-status-next.md # Packaging + status + next-step rules
│   │   ├── impact.md              # Change impact triage rules
│   │   ├── qc-review.md           # QC-UC-Review audit rules
│   │   └── README.md              # Behavior shard index
│   └── workflows/                 # Cross-command orchestration
│       ├── do.md                  # Natural language intent router
│       ├── impact.md              # Change triage state machine
│       └── next.md                # Resume + next-step state machine
│
├── skills/                        # 9 BA skills (1,200+ LOC total)
│   ├── ba-start/                  # Main BA lifecycle engine
│   │   ├── SKILL.md               # Skill definition (80 LOC)
│   │   └── steps/                 # Lifecycle step files
│   │       ├── intake.md
│   │       ├── options.md
│   │       ├── backbone.md
│   │       ├── frd.md
│   │       ├── stories.md
│   │       ├── srs.md
│   │       ├── wireframes.md
│   │       ├── package.md
│   │       ├── status.md
│   │       ├── next.md
│   │       └── reverse.md
│   ├── ba-do/                     # Natural language router (39 LOC)
│   ├── ba-next/                   # Resume + next-step guidance (33 LOC)
│   ├── ba-impact/                 # Change impact analysis (34 LOC)
│   ├── ba-collab/                 # Module collaboration (43 LOC)
│   ├── ba-notion/                 # Notion publishing (109 LOC)
│   ├── ba-kit-update/             # Self-update (46 LOC)
│   ├── brainstorm/                # Pre-intake deep interview (260 LOC)
│   └── qc-uc-review/              # UC/SRS audit (128 LOC)
│
├── agents/                        # 4 specialized roles
│   ├── requirements-engineer/     # Backbone, FRD, stories, SRS
│   ├── ui-ux-designer/            # Wireframe constraints, design decisions
│   ├── ba-documentation-manager/  # Validation, quality review, packaging
│   └── ba-researcher/             # Domain research, standards, context
│
├── scripts/                       # 39 automation scripts (Python + Bash)
│   ├── guardrail-*.py             # Index-first read enforcement (5 scripts)
│   ├── reverse-*.py               # As-built documentation (6 scripts)
│   ├── md-to-html.py              # Artifact packaging
│   ├── validate-*.py              # Quality validation (7 scripts)
│   ├── install.sh                 # Claude Code installer
│   ├── install-codex-ba-kit.sh    # Codex installer
│   ├── install-antigravity-ba-kit.sh # Antigravity installer
│   └── [other utilities]
│
├── templates/                     # 37 artifact templates
│   ├── intake-form-template.md
│   ├── backbone-index-template.md
│   ├── frd-template.md
│   ├── brainstorm-template.md
│   ├── project-home-template.md
│   ├── collab-home-template.md
│   ├── module-home-template.md
│   ├── design-md-template.md
│   ├── ascii-screen-template.md
│   ├── userstory-item-template.md
│   ├── impact-receipt-template.md
│   ├── options-receipt-template.md
│   ├── index-validation-receipt-template.md
│   ├── manifest.json              # Template routing manifest
│   └── [other templates]
│
├── rules/                         # 8 BA governance rules
│   ├── ba-quality-standards.md    # Requirement quality, traceability, consistency
│   ├── ba-workflow.md             # Lifecycle, delegation, documentation
│   ├── ba-conventions.md          # Owner resolution, no-re-ask, IT-BA framing
│   ├── ba-naming-conventions.md   # Slugs, file paths, ID formats
│   ├── brainstorm-*.md            # Brainstorm-specific rules (5 files)
│   └── [other governance]
│
├── designs/                       # Design system documents
│   ├── README.md
│   ├── ba-ide-platform/           # BA IDE platform design
│   └── {slug}/DESIGN.md           # Project runtime design (created per engagement)
│
├── docs/                          # Project documentation (12 files, ~2K LOC)
│   ├── project-overview-pdr.md    # This file (PDR + vision)
│   ├── codebase-summary.md        # Codebase navigation
│   ├── code-standards.md          # Coding standards + conventions
│   ├── system-architecture.md     # Architecture + state machines
│   ├── project-roadmap.md         # Development roadmap
│   ├── getting-started.md         # Installation + quick start
│   ├── codex-setup.md             # Codex runtime setup
│   ├── antigravity-setup.md       # Antigravity runtime setup
│   ├── skill-catalog.md           # Skill reference
│   ├── ba-methodology-guide.md    # BA methodology overview
│   ├── runtime-hard-guardrails.md # Guardrail system
│   └── [other docs]
│
├── plans/                         # Active project plans + reports
│   ├── {slug}-{date}/             # Per-engagement project root
│   │   ├── PROJECT-HOME.md        # BA-facing dashboard
│   │   ├── COLLAB-HOME.md         # Collaboration dashboard
│   │   ├── 01_intake/             # Intake + options
│   │   ├── 02_backbone/           # Backbone + memory
│   │   ├── 03_modules/            # Module artifacts
│   │   ├── 04_compiled/           # HTML packages
│   │   └── delegation/            # Review packets
│   └── reports/                   # Generated reports
│
├── tests/                         # Test fixtures + goldens
│   ├── fixtures/                  # 25 test input files
│   ├── goldens/                   # 25 expected output files
│   └── runtime-parity/            # Runtime adapter tests
│
├── codex/                         # Codex runtime integration
│   ├── agents/                    # Codex agent definitions
│   └── skills/                    # Codex skill wrappers
│
├── .github/                       # CI/CD
│   ├── CODEOWNERS                 # File ownership
│   ├── ISSUE_TEMPLATE/            # Bug report, feature request
│   └── workflows/                 # GitHub Actions
│
├── CLAUDE.md                      # Claude Code project instructions
├── AGENTS.md                      # Codex repository instructions
├── GEMINI.md                      # Gemini runtime instructions
├── ba-kit.config.json             # Root configuration
├── install.sh                     # Claude Code installer
├── LICENSE                        # Commercial proprietary
└── README.md                      # Project overview (Vietnamese)
```

## File Counts by Directory

| Directory | Files | LOC | Purpose |
|-----------|-------|-----|---------|
| `core/` | 12 | 786 | Contract + behavior system |
| `skills/` | 45 | 1,200+ | BA lifecycle skills |
| `agents/` | 8 | 400+ | Specialized agent roles |
| `scripts/` | 39 | 3,500+ | Automation (Python + Bash) |
| `templates/` | 37 | 2,000+ | Artifact templates |
| `rules/` | 8 | 1,500+ | BA governance |
| `designs/` | 5 | 500+ | Design system |
| `docs/` | 12 | 2,000+ | Project documentation |
| `tests/` | 50 | 1,000+ | Test fixtures + goldens |
| **Total** | **251** | **32,000+** | |

## Key Files & Their Roles

### Contract System (Core)

**`core/contract.yaml`** (456 LOC)
- Single source of truth for all paths, commands, states, thresholds
- Defines 18 commands (intake, backbone, frd, stories, srs, wireframes, package, status, next, impact, options, reverse, qc-review, etc.)
- Specifies post-`srs` module QC plus aggregate package validation
- Lists activation levels (base, modular, program)
- Maps behavior shards to commands
- Canonical for: paths, defaults, state enums, resolution sequences

**`core/contract-behavior.md`** (330 LOC)
- Shared runtime-neutral operating rules
- Argument parsing conventions
- Natural language routing logic
- Prerequisite behavior
- Legacy detection
- Canonical for: policy intent, not literal paths

**`core/behavior/*.md`** (9 shards, ~15K LOC total)
- Command-specific behavior (intake, backbone, module-authoring, srs, wireframes, package-status-next, impact, qc-review)
- Detailed step-by-step workflows
- Quality gate criteria
- Error handling
- Canonical for: command-specific policy

### Skills (Lifecycle)

**`skills/ba-start/`** (Main BA lifecycle engine)
- Unified skill covering all lifecycle steps
- Dispatches to step files based on subcommand
- Handles full lifecycle: intake → backbone → FRD/stories → SRS → module QC → wireframes/figma downstream → package
- Also handles: status, next, reverse, impact

**`skills/ba-do/`** (Natural language router)
- Maps user intent to safe workflows
- Infers subcommand from natural language
- Routes to ba-start or ba-collab

**`skills/ba-next/`** (Resume + next-step guidance)
- Resumes project from PROJECT-HOME.md
- Recommends next step based on current state
- Friendly for non-technical BAs

**`skills/ba-impact/`** (Change impact analysis)
- Triages requirement changes
- Identifies affected layers and artifacts
- Recommends rerun strategy

**`skills/ba-collab/`** (Module collaboration)
- Module ownership and scope management
- Review packet generation
- GitHub integration (approval-gated)

**`skills/brainstorm/`** (Pre-intake deep interview)
- 7-section structured interview
- Captures business context before formal intake
- Generates brainstorm artifact

**`skills/qc-uc-review/`** (UC/SRS audit)
- Platform-parameterized quality check
- Audits use cases and SRS for test-readiness
- Generates audit report with findings

### Scripts (Automation)

**Guardrail Scripts** (5 files)
- `guardrail-preflight.py`: Index-first read enforcement
- `guardrail-build-excerpts.py`: Extract relevant sections
- `guardrail-audit.py`: Validate index quality
- `guardrail_common.py`: Shared utilities

**Reverse Mode Scripts** (6 files)
- `reverse-preflight.py`: Baseline lock creation
- `reverse-drift-check.py`: Detect changes vs. baseline
- `reverse-build-excerpts.py`: Extract evidence
- `reverse-promote.py`: Promote to backbone

**Validation Scripts** (7 files)
- `validate-navigation-consistency.py`: Screen Contract Plus vs. DESIGN.md
- `validate-index-quality.py`: Producer-side validation
- `validate-cross-artifact-consistency.py`: Traceability checks

**Conversion Scripts**
- `md-to-html.py`: Compile markdown to HTML packages
- `source-extract.py`: Extract code snippets for reverse mode
- `design-snapshot.py`: Capture design decisions

**Installation Scripts**
- `install.sh`: Claude Code installer
- `install-codex-ba-kit.sh`: Codex installer
- `install-antigravity-ba-kit.sh`: Antigravity installer

### Templates (37 files)

**Lifecycle Artifacts**
- `intake-form-template.md`: Intake normalization
- `backbone-index-template.md`: Backbone index
- `frd-template.md`: Functional requirements
- `userstory-item-template.md`: User story item
- `userstories-index-template.md`: User stories folder index
- `usecase-item-template.md`: Use case item
- `usecases-index-template.md`: Use cases folder index
- `ascii-screen-template.md`: ASCII screen canon with mandatory wireframe
- `ascii-screen-index-template.md`: ASCII screen folder index
- `srs-spec-template.md`: SRS spec source
- `srs-flows-template.md`: SRS flows source
- `srs-states-template.md`: SRS states source
- `srs-erd-template.md`: SRS ERD source

**Dashboards**
- `project-home-template.md`: BA-facing resume dashboard
- `collab-home-template.md`: Collaboration dashboard
- `module-home-template.md`: Module BA dashboard

**Design & UI**
- `design-md-template.md`: Design system document
- `screen-canon-template.md`: Screen canon with mandatory ASCII wireframe coverage

**Receipts & Validation**
- `impact-receipt-template.md`: Change impact receipt
- `options-receipt-template.md`: Options selection receipt
- `index-validation-receipt-template.md`: Quality gate receipt

**Manifest**
- `manifest.json`: Template routing and metadata

## Component Relationships

```
contract.yaml (paths, commands, states)
    ↓
contract-behavior.md (shared policy)
    ↓
behavior/*.md (command-specific policy)
    ↓
skills/ba-start/steps/*.md (workflow execution)
    ↓
templates/*.md (artifact generation)
    ↓
scripts/*.py (validation, conversion, automation)
```

## Activation Levels

| Level | Trigger | Memory | Collaboration |
|-------|---------|--------|---------------|
| **Base** | Single project | Hot shard only | None |
| **Modular** | ≥2 modules OR ≥2 owners | Hot + warm shards | COLLAB-HOME.md, MODULE-HOME.md |
| **Program** | Cross-module deps OR ≥2 delegation slices | Hot + warm + cold | Full delegation tracking |

## Quality Gates

| Gate | Trigger | Profile | Block Criteria |
|------|---------|---------|----------------|
| **Post-SRS Module QC** | After module SRS | Full 10-point audit | Score < 70 |
| **Package Validation** | During package | Aggregate consistency compile check | Package blockers exist |

## Runtime Adapters

| Runtime | Integration | Status |
|---------|-------------|--------|
| **Claude Code** | Native via `install.sh` → `~/.claude/` | Production |
| **Codex** | Repo-native via `AGENTS.md` | Production |
| **Antigravity** | CLI + Knowledge Item via `install-antigravity-ba-kit.sh` | Production |

## How to Navigate the Codebase

1. **Start with contract:** Read `core/contract.yaml` for paths and command metadata
2. **Understand policy:** Read `core/contract-behavior.md` for shared rules
3. **Pick a command:** Read the relevant behavior shard in `core/behavior/`
4. **Execute workflow:** Read the step file in `skills/ba-start/steps/`
5. **Generate artifact:** Use template from `templates/`
6. **Validate output:** Run script from `scripts/`

## Key Patterns

### Path Resolution
All paths use token substitution: `{slug}`, `{date}`, `{module_slug}`. Resolved at runtime from CLI args or disk inspection.

### Artifact Profiles
- **Machine-facing:** JSON/NDJSON manifests, locks, state files
- **Agent-facing:** Indexes, memory shards, packets
- **User-facing:** Intake, backbone, FRD, SRS, compiled HTML

### State Enums
Canonical lifecycle status: `recommended`, `in-progress`, `completed`, `skipped`, `not-needed`

### Behavior Shards
Each command has a dedicated shard in `core/behavior/` that specifies:
- Prerequisites (what must exist first)
- Workflow steps (what to do)
- Quality gates (when to block)
- Error handling (what to do if blocked)

## Testing & Validation

- **25 test fixtures** in `tests/fixtures/` (sample inputs)
- **25 golden files** in `tests/goldens/` (expected outputs)
- **Runtime parity tests** in `tests/runtime-parity/` (Claude Code vs. Codex vs. Antigravity)
- **Contract sync tests** verify contract.yaml matches behavior shards
- **Validation scripts** run pre-commit checks

## Development Workflow

1. Modify `core/contract.yaml` for path/command changes
2. Update relevant `core/behavior/*.md` shard
3. Update `skills/ba-start/steps/*.md` step file
4. Update or create `templates/*.md` if artifact structure changed
5. Add/update `scripts/*.py` for validation or conversion
6. Run tests: `pytest tests/`
7. Commit with conventional message: `feat:`, `fix:`, `docs:`, `refactor:`

## Cross-References

- **Getting Started:** `docs/getting-started.md` (installation + quick start)
- **System Architecture:** `docs/system-architecture.md` (state machines + diagrams)
- **Code Standards:** `docs/code-standards.md` (naming, file organization, conventions)
- **Project Roadmap:** `docs/project-roadmap.md` (releases + planned work)
