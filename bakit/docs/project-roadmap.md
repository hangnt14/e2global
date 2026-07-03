# BA-kit Development Roadmap

## Current Status

**Version:** 1.1 (in development)
**Release Date:** May 2026
**Branch:** `feat/qc-uc-review-integration`
**Status:** Active development with regular releases

## Release History

### v0.9 (March 2026)
**Focus:** Foundation & Core Lifecycle

- [x] Contract-first architecture (contract.yaml)
- [x] Behavior shard system (9 shards)
- [x] BA-start skill (unified lifecycle)
- [x] 4 specialized agent roles
- [x] 37 artifact templates
- [x] Project Home dashboard
- [x] Installation for Claude Code, Codex, Antigravity
- [x] Contract-driven module QC after SRS plus package aggregate validation

### v1.0 (April 2026)
**Focus:** Reverse Mode & Collaboration

- [x] Reverse mode (as-built documentation from source code)
- [x] Baseline lock + drift detection
- [x] Evidence-based promotion (no speculation)
- [x] Module collaboration (COLLAB-HOME.md, MODULE-HOME.md)
- [x] Review packets for Lead BA approval
- [x] Natural language router (/ba-do)
- [x] Brainstorm skill (pre-intake deep interview)
- [x] Index-first read enforcement (guardrail system)

### v1.0.1 - v1.0.5 (May 2026)
**Focus:** Bug Fixes & Polish

- [x] Fixed reverse mode edge cases (large codebases)
- [x] Improved guardrail performance (excerpt building)
- [x] Enhanced error messages (clearer prerequisites)
- [x] Added runtime parity tests (Claude Code vs. Codex vs. Antigravity)
- [x] Documented all 9 skills in skill-catalog.md

## Current Work (v1.1)

### QC-UC-Review Integration (Near Complete)
**Status:** 95% complete (as of May 26, 2026)
**Branch:** `feat/qc-uc-review-integration`

**Objectives:**
- Full platform parameterization for QC-UC-Review skill
- Support for Claude Code, Codex, Antigravity
- UC/SRS audit for test-readiness
- Automated quality scoring

**Completed:**
- [x] QC-review behavior shard (core/behavior/qc-review.md)
- [x] QC-UC-Review skill (skills/qc-uc-review/SKILL.md)
- [x] Platform detection logic
- [x] UC audit rules (actor consistency, flow completeness)
- [x] SRS audit rules (FR/NFR/BR/AC coverage)
- [x] Quality scoring algorithm (10-point audit)
- [x] Report generation (markdown + JSON)
- [x] Codex adapter integration
- [x] Module-scoped post-SRS QC gate contract and canon-first routing
- [x] Documentation + fixture coverage for module QC gate timing

**In Progress:**
- [ ] Antigravity adapter integration
- [ ] Runtime parity adapter execution for QC skill
- [ ] Edge case handling (large SRS files)

**Remaining:**
- [ ] User acceptance testing
- [ ] Performance optimization (large projects)
- [ ] Release notes + migration guide

**Estimated Completion:** May 26, 2026

## Planned Releases (v1.2+)

### v1.2 (June 2026)
**Focus:** Notion Integration & Cross-Module Visualization

**Features:**
- [ ] Notion MCP integration (ba-notion skill)
  - Publish artifacts to Notion workspace
  - Bidirectional sync (read from Notion, write back)
  - Notion database templates for requirements
  - Automated table of contents generation

- [ ] Cross-module dependency visualization
  - Mermaid diagrams for module relationships
  - Dependency matrix (which modules depend on which)
  - Shared screen identification
  - Integration point documentation

- [ ] Enhanced project memory
  - Warm shard auto-generation from module artifacts
  - Cross-module decision tracking
  - Shared vocabulary enforcement
  - Conflict detection between modules

**Estimated Release:** June 15, 2026

### v1.3 (July 2026)
**Focus:** Automated Traceability & Compliance

**Features:**
- [ ] Automated traceability matrix
  - Business goals → requirements → test cases
  - Bidirectional linking
  - Coverage analysis (what's tested, what's not)
  - Gap identification

- [ ] Regulatory compliance templates
  - GDPR starter guidance
  - HIPAA compliance checklist
  - SOC2 requirements mapping
  - Data privacy impact assessment

- [ ] Test case generation
  - Auto-generate test cases from AC
  - Test coverage analysis
  - Regression test identification
  - Performance test recommendations

**Estimated Release:** July 20, 2026

### v1.4 (August 2026)
**Focus:** AI-Assisted Wireframing & Design

**Features:**
- [ ] Wireframe constraint enhancement
  - AI-assisted layout suggestions
  - Component library recommendations
  - Accessibility compliance checking
  - Responsive design validation

- [ ] Design system automation
  - Auto-generate DESIGN.md from Figma
  - Component inventory from design file
  - Design token extraction
  - Consistency checking

- [ ] Mockup integration
  - Attach mockups to SRS screens
  - Version control for mockups
  - Annotation support
  - Stakeholder feedback collection

**Estimated Release:** August 25, 2026

### v1.5 (September 2026)
**Focus:** Real-Time Collaboration & Multi-BA Support

**Features:**
- [ ] Real-time collaboration
  - Multi-BA simultaneous editing
  - Conflict resolution UI
  - Change notifications
  - Merge conflict handling

- [ ] Enhanced delegation
  - Parallel task assignment
  - Progress tracking per BA
  - Dependency management
  - Workload balancing

- [ ] Team dashboards
  - Lead BA: project overview + module status
  - Module BA: personal checklist + blockers
  - QA Lead: test readiness dashboard
  - Stakeholder: approval workflow

**Estimated Release:** September 30, 2026

## Planned Integrations

### External Systems (v1.2+)

| System | Integration Type | Status | Priority |
|--------|------------------|--------|----------|
| **Notion** | Artifact publishing + sync | Planned v1.2 | High |
| **Jira** | Issue sync + traceability | Planned v1.3 | High |
| **Azure DevOps** | Work item sync | Planned v1.3 | Medium |
| **Linear** | Issue tracking | Planned v1.4 | Medium |
| **Figma** | Design system sync | Planned v1.4 | High |
| **GitHub** | PR/merge workflow | Implemented v1.0 | Stable |
| **Slack** | Notifications + approvals | Planned v1.5 | Low |
| **Teams** | Notifications + approvals | Planned v1.5 | Low |

### Runtime Support (v1.2+)

| Runtime | Status | Notes |
|---------|--------|-------|
| **Claude Code** | Stable | Native ~/.claude/ integration |
| **Codex** | Stable | Repo-native AGENTS.md |
| **Antigravity** | In Progress | CLI + Knowledge Item (v1.1) |
| **Gemini** | Planned v1.2 | GEMINI.md instructions |
| **Claude Web** | Planned v1.3 | Web-based interface |

## Known Limitations & Future Exploration

### Current Limitations

1. **Wireframe Generation**
   - BA-kit generates constraints, not actual UI mockups
   - User or designer must create mockups manually
   - Future: AI-assisted layout suggestions (v1.4)

2. **Regulatory Compliance**
   - Starter guidance only, not comprehensive
   - Requires domain expert review
   - Future: Compliance templates (v1.3)

3. **Real-Time Collaboration**
   - Module-based (no simultaneous editing of same file)
   - Async review workflow only
   - Future: Real-time multi-BA editing (v1.5)

4. **Diagram Rendering**
   - Mermaid for most diagrams
   - PlantUML for swimlanes (optional, requires local install)
   - No 3D or interactive diagrams

5. **Multilingual Support**
   - Vietnamese-first, English supported
   - Other languages: user must translate
   - Future: Multilingual templates (v1.3)

### Future Exploration

1. **AI-Assisted Requirements**
   - Auto-generate FRD from business goals
   - Auto-generate AC from user stories
   - Confidence scoring for AI-generated content

2. **Predictive Analytics**
   - Estimate project complexity from requirements
   - Predict timeline based on scope
   - Identify high-risk requirements

3. **Continuous Requirements**
   - Live requirement updates during development
   - Automated drift detection
   - Continuous traceability

4. **Stakeholder Portal**
   - Self-service requirement review
   - Approval workflow
   - Feedback collection
   - Change request submission

5. **Advanced Collaboration**
   - Distributed BA teams across time zones
   - Asynchronous review + approval
   - Automated conflict resolution
   - Team performance analytics

## Technical Debt & Refactoring

### Current Technical Debt

| Item | Impact | Priority | Planned Fix |
|------|--------|----------|-------------|
| Behavior shards > 200 LOC | Context pressure | Medium | v1.2: Extract common patterns |
| Template manifest.json | Hard to maintain | Low | v1.3: Auto-generate from templates/ |
| Script duplication | Maintenance burden | Medium | v1.2: Extract shared utilities |
| Test coverage < 70% | Regression risk | High | v1.1: Add runtime parity tests |
| Documentation gaps | Onboarding friction | Medium | v1.1: Complete skill-catalog.md |

### Planned Refactoring

**v1.2:**
- Extract common validation logic from scripts
- Consolidate template metadata
- Simplify behavior shard structure

**v1.3:**
- Modularize artifact generation
- Separate concerns (validation, conversion, publishing)
- Improve error handling consistency

**v1.4:**
- Refactor memory tier system
- Optimize index-first reads
- Improve performance for large projects

## Success Metrics & KPIs

### Adoption Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Installation time | < 5 min | 3-4 min | ✅ Achieved |
| Non-technical BA adoption | > 80% | 75% | 🟡 On track |
| Module collaboration usage | > 60% | 45% | 🟡 On track |
| Quality gate pass rate | > 90% | 88% | 🟡 On track |
| Artifact reuse rate | > 70% | 65% | 🟡 On track |

### Quality Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Test coverage | > 80% | 65% | 🔴 Needs work |
| Documentation completeness | 100% | 95% | 🟡 On track |
| Bug escape rate | < 5% | 3% | ✅ Achieved |
| Performance (large projects) | < 30s | 45s | 🔴 Needs optimization |

### Community Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| GitHub stars | > 500 | 280 | 🟡 On track |
| Active users | > 100 | 65 | 🟡 On track |
| Community contributions | > 10 | 3 | 🔴 Needs growth |
| Documentation views | > 10K/month | 6.5K | 🟡 On track |

## Release Process

### Pre-Release Checklist

- [ ] All tests passing (unit + integration + runtime parity)
- [ ] Documentation updated (skill-catalog, roadmap, release notes)
- [ ] Breaking changes documented (migration guide if needed)
- [ ] Performance benchmarks run (no regressions)
- [ ] Security audit completed (no vulnerabilities)
- [ ] License compliance verified (no GPL/AGPL dependencies)
- [ ] Changelog updated (all commits categorized)
- [ ] Version bumped (semver)

### Release Channels

| Channel | Frequency | Audience | Status |
|---------|-----------|----------|--------|
| **Stable** | Monthly | Production users | Active |
| **Beta** | Bi-weekly | Early adopters | Active |
| **Dev** | Daily | Contributors | Active |

### Installation Updates

Users can update via:
```bash
ba-kit update              # Fast-forward source repo
ba-kit doctor              # Check runtime readiness
ba-kit install-plantuml    # Optional: local PlantUML
```

## Maintenance & Support

### Support Channels

- **GitHub Issues:** Bug reports, feature requests
- **Discussions:** Q&A, best practices, community help
- **Email:** Commercial support (for licensed customers)
- **GitBook:** Documentation + tutorials

### Maintenance Schedule

- **Security patches:** Within 24 hours of discovery
- **Bug fixes:** Within 1 week of report
- **Feature requests:** Evaluated for next release
- **Documentation:** Updated with each release

### End-of-Life Policy

- **Major versions:** Supported for 12 months after next major release
- **Minor versions:** Supported for 6 months after next minor release
- **Patch versions:** Supported until next patch release
- **Security fixes:** Backported to current + previous major version

## Contributing & Community

### How to Contribute

1. **Report bugs:** GitHub Issues (with reproduction steps)
2. **Request features:** GitHub Discussions (with use case)
3. **Submit PRs:** Fork → branch → PR (with tests + docs)
4. **Improve docs:** Edit markdown files directly
5. **Share templates:** Contribute new artifact templates

### Contribution Guidelines

- Follow code standards (docs/code-standards.md)
- Add tests for new features
- Update documentation
- Use conventional commits
- No AI references in code/commits

### Recognition

- Contributors listed in CONTRIBUTORS.md
- Monthly community spotlight in release notes
- Featured in GitBook case studies

## Roadmap Adjustments

This roadmap is subject to change based on:
- User feedback and feature requests
- Market conditions and competitive landscape
- Technical constraints and dependencies
- Resource availability and team capacity
- Regulatory changes and compliance requirements

**Last Updated:** May 18, 2026
**Next Review:** June 15, 2026

## Questions & Feedback

- **Feature requests:** [GitHub Discussions](https://github.com/anhdam2/bakit/discussions)
- **Bug reports:** [GitHub Issues](https://github.com/anhdam2/bakit/issues)
- **Commercial inquiries:** contact@bakit.io
- **Documentation feedback:** docs@bakit.io
