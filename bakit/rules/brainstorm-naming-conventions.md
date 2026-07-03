# Naming Conventions

## Slugs (folder & file names)

- All lowercase, kebab-case
- ASCII only (avoid Vietnamese diacritics — use English/transliteration)
- No spaces, no underscores, no special chars
- Strip leading/trailing dashes
- Max 50 chars

| Input | Slug |
|-------|------|
| "User Login" | `user-login` |
| "Forgot Password (v2)" | `forgot-password-v2` |
| "Thanh toán đơn hàng" | `payment-checkout` (preferred) |
| "2FA / OTP" | `two-factor-auth` |

## File path patterns

| Doc type | Path |
|----------|------|
| URD | `docs/{feature}/urd.md` |
| BRD | `docs/{feature}/brd.md` |
| PRD | `docs/{feature}/prd.md` |
| SRS spec | `docs/{feature}/srs/spec.md` |
| SRS flows (OPTIONAL — cross-function system-wide) | `docs/{feature}/srs/flows.md` (chỉ tạo khi user `--with-system-flow`. Per-function diagram đã embedded trong `usecases/uc-*.md` Mục e) |
| SRS ERD | `docs/{feature}/srs/erd.md` |
| Screen spec (ASCII fidelity) | `docs/{feature}/ascii-screen/{screen-slug}.md` (cùng level srs/, single source of truth: spec + states + logic + ASCII wireframe INLINE Mục "Wireframe (ASCII)") |
| HTML mockup | `docs/{feature}/html-design/{screen-slug}.html` (folder riêng) |
| Pencil design | `docs/{feature}/{feature}.pen` (1 file/feature, multi-screen inside; quản lý qua Pencil MCP — KHÔNG Read trực tiếp) |
| Figma link | inline trong screen MD frontmatter `designs.figma: <url>` (KHÔNG file local, KHÔNG `figma-links.md`) |
| Brainstorm | `docs/{feature}/brainstorms/{idea-slug}.md` |
| User story | `docs/{feature}/userstories/us-{NNN}.md` |
| Function / Use case (function-centric, 8 sections) | `docs/{feature}/usecases/uc-{slug}.md` — self-contained 1 file: intro + actors + preconds + expected result + logic diagram inline (Mục e) + screens involved + FR map + OQs |
| Project ERD | `docs/_shared/erd.md` (singleton exception) |
| Traceability | `docs/_shared/traceability.md` (auto from /gap) |
| Jira map | `docs/_shared/jira-map.md` (auto from /jira) |
| Meeting | `docs/meetings/YYYY-MM-DD-{type}-{slug}.md` (project-level) |
| Decision | `docs/decisions/YYYY-MM-DD-{slug}.md` (project-level) |
| Blocker | `docs/blockers/YYYY-MM-DD-{slug}.md` (project-level) |
| Inbox capture | `docs/inbox/YYYY-MM-DD-{slug}.md` (project-level) |
| Change Request | `docs/changes/CR-{YYYYMMDD}-{NNN}.md` (project-level) |
| Impact Report | `docs/impacts/CR-{cr_id}-impact.md` (project-level) |
| Export package | `docs/exports/{date}-{scope}{-feature}-package.{md|html|pdf|docx}` |

## Wikilinks

Format: `[[docs/payment/srs/spec|Payment SRS]]`

- Use full path from project root (Obsidian + GitHub render correctly)
- Optional display text after `|`
- Don't use `[[Login Feature]]` (Obsidian-only style) — breaks on GitHub

## Frontmatter requirements

Every doc-type file MUST have YAML frontmatter at the top:

```yaml
---
type: srs-feature           # see types below
status: draft               # see status-lifecycle.md
created: 2026-05-09         # ISO date
updated: 2026-05-09         # ISO date
---
```

Recommended optional fields:
- `owner`: handle (e.g. `@hoang`)
- `priority`: P0 / P1 / P2
- `version`: semver (e.g. `0.1.0`)
- `tags`: list of strings
- `links`: dict of related-doc paths

## Doc type values

| Type | Use for |
|------|---------|
| `srs` | `docs/{feature}/srs/spec.md` |
| `srs-flows` | `docs/{feature}/srs/flows.md` |
| `screen` | `docs/{feature}/ascii-screen/*.md` (per-feature, cùng level srs/; spec + ASCII wireframe INLINE Mục 5) |
| `urd` / `brd` / `prd` | per-feature requirements docs (`docs/{feature}/{urd,brd,prd}.md`) |
| `brainstorm` | `docs/{feature}/brainstorms/*.md` |
| `user-story` | `docs/{feature}/userstories/*.md` |
| `use-case` | `docs/{feature}/usecases/*.md` |
| `diagram-sequence` | DEFAULT: `docs/{feature}/usecases/uc-*.md` Mục e (function-centric). Fallback `docs/{feature}/srs/flows.md` (`--system-flow`) hoặc standalone |
| `diagram-erd` | `docs/{feature}/srs/erd.md` hoặc `docs/_shared/erd.md` |
| `pencil-design` | `docs/{feature}/{feature}.pen` (flat, multi-screen, Pencil MCP-managed, encrypted) |
| `change-request` | `docs/changes/CR-*.md` |
| `impact-report` | `docs/impacts/CR-*-impact.md` |
| `archive-stub` | original path sau khi file moved to `_archive/` |
| `traceability` | `docs/_shared/traceability.md` |
| `jira-map` | `docs/_shared/jira-map.md` |
| `export-package` | `docs/exports/*.md` |
| `meeting` | `docs/meetings/*.md` |
| `decision` | `docs/decisions/*.md` |
| `blocker` | `docs/blockers/*.md` |
| `inbox` | `docs/inbox/*.md` |

## ID conventions (cross-doc references)

Mọi ID trong frontmatter `links:` hoặc body phải tuân format dưới. Format này đảm bảo `/gap` traceability matrix không collision khi cross-aggregate cross-feature.

### Format chung

| Loại | Format | Ví dụ | Scope |
|------|--------|-------|-------|
| Business Objective | `BO-{feature}-{NNN}` | `BO-payment-01` | Per-feature, trong `brd.md` Mục 4 |
| PRD Capability | `CAP-{feature}-{NNN}` | `CAP-payment-01` | Per-feature, trong `prd.md` Mục 4 |
| Functional Requirement | `FR-{feature}-{NNN}` | `FR-payment-001` | Per-feature, trong `srs/spec.md` Mục 2 |
| Non-Functional Requirement | `NFR-{feature}-{NNN}` | `NFR-payment-001` | Per-feature, trong `srs/spec.md` Mục 3 |
| Business Rule | `BR-{feature}-{NNN}` | `BR-payment-001` | Per-feature, trong `srs/spec.md` Mục 4 |
| Error Code | `E-{feature}-{NNN}` | `E-payment-001` | Per-feature, trong `srs/spec.md` Mục 5 |
| User Story | `US-{module}-{NNN}` | `US-auth-001` | Per-module (`03_modules/{module}/userstories/us-{module}-{nnn}.md`) |
| Use Case | `UC-{module}-{slug}` | `UC-auth-login` | Per-module folder, slug human-readable |
| Acceptance Criterion | `AC-{module}-{NNN}` | `AC-auth-001` | Per-module, scope trong file user story |
| Change Request | `CR-{YYYYMMDD}-{NNN}` | `CR-20260512-001` | Project-wide (`docs/changes/`) |
| Decision | `D-{YYYY-MM-DD}-{slug}` | `D-2026-05-12-stripe-vs-momo` | Project-wide |
| Blocker | `B-{YYYY-MM-DD}-{slug}` | `B-2026-05-12-vendor-delay` | Project-wide |

### Rules

- **Feature prefix bắt buộc** cho BO/CAP/FR/NFR/BR/E. Mục đích: tránh collision khi `/gap` cross-feature aggregate (vd `FR-001` ambiguous khi 2 features).
- **US/AC có module prefix** (`US-{module}-{NNN}`, `AC-{module}-{NNN}`) để tránh collision khi compile cross-module. Module ngầm hiểu qua folder cha, nhưng ID vẫn cần prefix vì traceability matrix và QC review là cross-module.
- **NNN = 3 digit zero-pad** cho BO/CAP/FR/NFR/BR/E (vd `001`, `042`). NN cũng OK cho BO/CAP (`01`, `02`) vì thường ít hơn.
- **CR/D/B prefix date** vì là sự kiện theo thời gian, ordering theo date.
- ID không reuse khi delete — luôn increment max + 1.
- Slug trong ID kebab-case, max 30 chars.

### Cross-references

Khi 1 doc reference ID của doc khác:
- Frontmatter `links:` flat list với full path: `links: [docs/payment/srs/spec.md, docs/payment/userstories/us-payment-001.md]`
- Body inline reference: `[[docs/payment/srs/spec.md#FR-payment-001|FR-payment-001]]` (Obsidian-compatible anchor).
- `/gap` parse cả 2 dạng để build relationship graph.
