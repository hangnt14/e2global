# Change Log Convention (v2)

> v2 — changelog là YAML list trong frontmatter, KHÔNG còn body table.

## Required frontmatter field

Mọi doc per-feature có `changelog: []` field trong frontmatter. Hook `auto-changelog.sh` append entry khi:
- File có frontmatter `changelog:` field.
- Latest entry KHÔNG cùng date với hôm nay (dedupe by date).

```yaml
---
type: urd
feature: payment
status: in-review
lang: vi
owner: "@hoangphan"
created: 2026-05-12
updated: 2026-05-13
links: [docs/payment/brainstorms/checkout-flow.md]
tags: []
stale_reason: ""
changelog:
  - 2026-05-13 | /review | reviewed by @senior-ba, applied 1 blocking fix
  - 2026-05-12 | /urd | initial draft từ brainstorm checkout-flow
---
```

**Newest entries on top.** Skill ghi entry inline khi tạo/sửa doc; hook là fallback safety net cho manual edits.

## Entry format

Mỗi entry là 1 dòng YAML list item với 3 phần phân cách `|`:

```
- {date} | {skill-name} | {note}
```

- **date**: ISO `YYYY-MM-DD`.
- **skill-name**: tên skill đã ghi entry (vd `/urd`, `/review`, `/cr`, `manual` cho hook fallback).
- **note**: imperative hoặc past-tense, ≤80 chars, factual.

## Skill enum (skill-name)

| Skill | Phase | Khi nào ghi |
|-------|-------|-------------|
| `/srs`, `/srs-add-screen` | 1 | Tạo/sửa SRS spec |
| `/meet`, `/brainstorm`, `/legacy` | 1-2 | Capture |
| `/urd`, `/brd`, `/prd`, `/sequence`, `/erd`, `/wireframe` | 3 | Specification |
| `/review`, `/gap` | 4 | Validation |
| `/usecase`, `/userstory`, `/ac`, `/jira`, `/export` | 5 | Delivery |
| `/cr`, `/impact`, `/archive`, `/status` | 6 | Maintenance |
| `manual` | — | Hook fallback khi user edit không qua skill |

## Note style

- Imperative hoặc past-tense, factual.
- Good: `"initial draft từ brainstorm checkout-flow"`, `"reviewed by @senior-ba, applied 1 blocking fix"`, `"applied CR-20260512-001: added OTP requirement"`.
- Bad: `"updated stuff"`, `"fixed things"`, `"per Hoang's request"` (attribution qua skill-name).

## How skills set the changelog row

Skills ghi entry **inline** khi build content từ template — KHÔNG dùng env var primary mechanism:

```yaml
# Skill writes:
changelog:
  - 2026-05-12 | /urd | initial draft từ brainstorm checkout-flow
```

Hook là fallback. Khi user edit ngoài skill (vd via Edit tool trực tiếp trong chat), skill có thể set env vars trước:

```bash
export CLAUDE_SKILL_NAME="manual"   # hoặc skill name nếu có
export CLAUDE_CHANGELOG_NOTE="fixed typo in Mục 3"
# Then Edit
```

Nếu env vars miss → hook ghi `manual | manual edit`.

## Files excluded từ auto-changelog

Hook skip:
- `docs/feature-list.md` (auto-gen)
- `docs/README.md`
- `docs/_shared/*` (project-level, hook skip; maintain manually nếu cần)
- `docs/exports/*` (regenerated artifacts)
- `docs/inbox/*` (raw captures)
- `docs/_archive/*` (frozen)
- Files KHÔNG có frontmatter `changelog:` field

## Dedupe by date

Nếu latest entry trong `changelog:` đã cùng date với hôm nay, hook skip. Tránh spam trong multi-step edits cùng session.

> Đây là behavior khác v1 (so sánh full row equality). v2 chỉ check date — đủ cho audit trail mà không bị over-log.

## Migration từ v1

Docs cũ có body `## Change Log` table → chạy `_scripts/migrate-changelog-v2.sh` (xem `phase-1-2-PATCH-1.2.md` Mục A.v2.4) để chuyển sang frontmatter list.

Sau migration, body `## Change Log` section bị xoá.
