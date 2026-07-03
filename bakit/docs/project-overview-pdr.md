# BA-kit Product Development Requirements

## Executive Summary

BA-kit is a commercial, production-grade Business Analysis toolkit for Claude Code, Codex, and Antigravity runtimes. It transforms AI agents into structured BA workstations with lifecycle management, standardized artifacts, module-based collaboration, and professional stakeholder handoff. Designed for solo IT BAs, consulting teams, and product managers doing BA work.

**Current Status:** Production (v1.0+), active development with regular releases
**License:** Commercial proprietary source-available
**Codebase:** ~32K LOC across 251 files (MD, YAML, JSON, Python, Bash)

## Problem Statement

Agent coding environments are optimized for software implementation. Business analysis work requires different defaults:

- Structured elicitation and intake normalization before requirements authoring
- Single persisted source of truth (backbone) before formal and Agile artifacts are emitted
- Traceability from business goals through requirements to test cases
- Reusable templates for recurring deliverables (FRD, SRS, user stories, screen canon ASCII)
- Module-based collaboration without forcing BAs to learn Git first
- Professional handoff packages for product, engineering, and operations teams

BA-kit closes this gap with a BA-first operating model and contract-first architecture.

## Vision & Value Proposition

**Vision:** Every AI agent can be a professional BA workstation.

**Value Proposition:**
- Reduce duplicated writing for solo analysts (templates + backbone-first authoring)
- Improve consistency of requirement quality and acceptance criteria (gated quality gates)
- Support Agile, Traditional, and Hybrid delivery styles (configurable mode)
- Enable non-technical BAs to collaborate without Git/CLI friction (natural language routing + dashboards)
- Accelerate handoff to engineering and operations (compiled HTML packages + traceability)

## Target Users

| User Type | Use Case |
|-----------|----------|
| Solo IT Business Analyst | Full lifecycle: intake → backbone → FRD/stories → SRS with mandatory ASCII → module QC → package |
| Product Manager (BA work) | Requirements definition, user story generation, acceptance criteria |
| Consulting Team | Discovery engagement, requirements capture, stakeholder handoff |
| Solution Analyst | Module-based collaboration, cross-team coordination, change impact analysis |
| QA/Test Lead | UC/SRS audit for test readiness (via qc-uc-review skill) |

## Core Capabilities

### 1. Lifecycle Management
- **Intake & Normalization:** Structured elicitation, gap analysis, open questions tracking
- **Requirements Backbone:** Single source of truth after scope lock (vocabulary, decisions, assumptions)
- **Gated Artifact Emission:** FRD, user stories, SRS, and screen canon ASCII emitted only when prerequisites met
- **Quality & Validation Boundaries:** Automatic module QC after `srs`, then aggregate validation during `package`
- **Packaging:** Compiled HTML deliverables for stakeholder review

### 2. Module Collaboration
- **Ownership & Scope:** Lead BA divides work, module BAs claim and author
- **Review Packets:** Structured handoff for Lead BA approval
- **Conflict Detection:** Automatic flagging of cross-module dependencies and shared decisions
- **GitHub Integration:** Optional PR/merge workflow (approval-gated, not automatic)

### 3. Reverse Mode (As-Built Documentation)
- **Baseline Lock:** Commit hash + evidence snapshot at start
- **Drift Detection:** Track changes to source code vs. documented behavior
- **Evidence-Based Promotion:** Only promote content with clear source evidence
- **No Speculation:** Reverse mode documents what exists, not future-state requests

### 4. Change Impact Analysis
- **Requirement Triage:** Classify changes by layer (intake, backbone, module, artifact)
- **Cascade Detection:** Identify downstream artifacts affected by change
- **Rerun Orchestration:** Automatically rerun affected layers with change context

### 5. Quality Assurance
- **QC-UC-Review Skill:** Platform-parameterized UC/SRS audit for test-readiness
- **Index-First Reads:** Guardrail enforcement for consistent artifact discovery
- **Validation Receipts:** Machine-readable proof of quality gate passage

## Key Features

| Feature | Description |
|---------|-------------|
| **Contract-First Design** | Single source of truth (contract.yaml) for paths, commands, states, quality gates |
| **Behavior Shards** | Command-specific operating rules (intake, backbone, SRS, wireframes, etc.) |
| **Memory Tiers** | Hot (vocabulary, decisions), warm (module-scoped), cold (archived) |
| **Activation Levels** | Base (single project), modular (≥2 modules), program (cross-module deps) |
| **Natural Language Routing** | `/ba-do` intent router maps user language to safe workflows |
| **Project Home Dashboard** | BA-facing resume point with next-step guidance and runtime prompts |
| **Collaboration Dashboards** | COLLAB-HOME.md (lead view), MODULE-HOME.md (module BA view) |
| **Design System** | DESIGN.md runtime constraints for UI handoff (colors, fonts, navigation schema) |
| **ASCII Wireframes** | Mandatory screen-canon ASCII under `screens/*.md`, compiled into SRS |
| **Compiled Packages** | HTML exports for stakeholder review (FRD, SRS, traceability matrix) |

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Installation time | < 5 minutes | Achieved |
| Non-technical BA resume | From PROJECT-HOME.md without CLI | Achieved |
| Module collaboration | No Git/PR learning required | Achieved |
| Requirement completeness | 100% have acceptance criteria | Achieved |
| Module QC automation | Post-`srs` module gate + package aggregate validation | Achieved |
| Codex integration | Repo-native via AGENTS.md | Achieved |
| Antigravity integration | CLI + Knowledge Item workflow | Achieved |

## Design Decisions

1. **Single unified skill** (`ba-start`) instead of many disconnected skills for cohesive lifecycle
2. **Requirements backbone** is default authoring source after intake (not freestyle FRD)
3. **Four focused agent roles** (requirements-engineer, ui-ux-designer, ba-documentation-manager, ba-researcher) without overlap
4. **Templates are first-class assets** because BA deliverables are repeatable across projects
5. **PlantUML for swimlanes**, Mermaid for other diagrams (portable, markdown-native)
6. **Hybrid methodology default** for solo IT BA work (formal where risk is high, lightweight where speed matters)
7. **Gated artifact emission** (SRS/wireframes only when needed) plus canon-first module QC after SRS instead of legacy pre-wireframe gating
8. **PROJECT-HOME.md is dashboard, not source of truth** (backbone → intake → module artifacts are canonical)
9. **GitHub is optional transport layer** (BA-facing state lives in Collab Home, Module Home, review packets)
10. **Contract-first architecture** (single contract.yaml for paths, commands, states, thresholds)

## Acceptance Criteria

- [x] Project structure exists and installs cleanly (< 5 min)
- [x] Skills, agents, rules, templates internally consistent
- [x] Cross-references between files valid and resolvable
- [x] Core BA outputs generated from templates without rework
- [x] Non-technical BAs can resume from PROJECT-HOME.md
- [x] Module collaboration works without Git/CLI friction
- [x] Quality gates enforce requirement completeness
- [x] Reverse mode produces evidence-based as-built documentation
- [x] Change impact analysis cascades across layers
- [x] Compiled packages ready for stakeholder handoff

## Roadmap & Release Strategy

### Recent Releases (v0.9+)
- Reverse mode: As-built documentation from source code with baseline lock and drift detection
- QC-UC-Review skill: Platform-parameterized UC/SRS audit for test-readiness
- Brainstorm skill: 7-section deep interview before lifecycle (pre-intake clarification)
- Index-first reads: Guardrail enforcement for consistent artifact discovery

### Current Work (v1.1)
- QC-UC-Review integration: Full platform parameterization for Codex/Antigravity
- Runtime parity: Unified behavior across Claude Code, Codex, Antigravity
- Token optimization: Context-efficient artifact handling for large projects

### Planned (v1.2+)
- Notion integration: Publish artifacts to Notion via MCP
- Cross-module dependency visualization: Mermaid diagrams for module relationships
- Automated traceability matrix: Business goals → requirements → test cases
- Regulatory compliance templates: GDPR, HIPAA, SOC2 starter guidance

## Technical Constraints & Dependencies

- **Python 3.8+** for scripts (guardrail, reverse mode, validation)
- **Bash 4+** for installation and CLI helpers
- **PlantUML** (optional, for swimlane diagrams in HTML packages)
- **Markdown rendering** (GitHub, Obsidian, or markdown-novel-viewer for full fidelity)
- **Git** (optional, for GitHub integration; not required for core BA workflows)

## Competitive Positioning

| Aspect | BA-kit | Traditional BA Tools | Generic AI Agents |
|--------|--------|---------------------|-------------------|
| **Lifecycle** | Gated, backbone-first | Waterfall-heavy | Freestyle, no structure |
| **Collaboration** | Module-based, no Git friction | Centralized, heavyweight | No collaboration model |
| **Artifact Quality** | Automated gates + validation | Manual review | No quality enforcement |
| **Handoff** | Compiled HTML + traceability | PDF export | Chat transcript |
| **Customization** | Contract-driven, extensible | Rigid templates | Unlimited, no standards |
| **Cost** | Commercial, source-available | Enterprise licensing | Free/subscription |

## Open Questions & Future Exploration

- Regulatory compliance automation (GDPR, HIPAA, SOC2 specific rules)
- AI-assisted wireframe generation (beyond constraints)
- Real-time collaboration (multi-BA simultaneous editing)
- Integration with Jira, Azure DevOps, Linear (bidirectional sync)
- Multilingual support beyond Vietnamese/English
