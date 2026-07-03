# BA Start Step - Status

This step requires:

- `core/contract.yaml`
- `core/contract-behavior.md`

## Discovery Strategy: Canonical-Summary-First

Status must emit a compact, deterministic checklist without broad artifact reads.

Resolution order:
1. Package snapshot at `plans/{slug}-{date}/02_backbone/package-snapshot.md` when current — derive artifact presence from its `artifacts` list.
2. Otherwise filesystem stat only (no content reads).
3. `paths.project_memory` header and `paths.memory_index` for activation state only.

## Memory Read Scope

- **Must read:** `core/contract.yaml`, `core/contract-behavior.md`
- **May read:** package snapshot, `paths.project_memory` header, `paths.memory_index`
- **Must NOT read:** `log.md`, `warm/` shards, `cold/`, full backbone, stories, SRS

## Scope

Inspect the project set and print artifact status, dates, Project Home, and delegated slices.
Emit a compact canonical summary — no content reads beyond the snapshot or stat checks.
For UI-backed SRS modules, include canon source, compile, and Figma readiness signals from file presence only.

## Prerequisites

- Resolve slug and date using `ba-kit resolve --slug <slug>`.
  The CLI uses `find -type d` internally for correct directory discovery.
  Do not use `Glob` — it only matches files, not directories.
- If slug or date resolution is ambiguous, stop and ask.

## Output Format

Print a checklist like this:

```text
Project: {slug}
Date set: {date}
Gói bàn giao tại thời điểm: hiện tại | cũ | chưa có

[Tài liệu gốc]
- [x] PROJECT-HOME.md (trang điều phối dự án) — 2026-03-26
- [x] 01_intake/intake.md (phiếu tiếp nhận yêu cầu) — 2026-03-26
- [x] 02_backbone/backbone.md (khung yêu cầu đã chốt) — 2026-03-26

[Module: auth-flow]
- [x] 03_modules/auth-flow/userstories/index.md — 2026-03-26
- [x] 03_modules/auth-flow/usecases/index.md — 2026-03-26
- [x] 03_modules/auth-flow/ascii-screen/index.md — 2026-03-26
- [x] 03_modules/auth-flow/ascii-screen/*.md — 4 file(s)
- [x] 03_modules/auth-flow/srs/spec.md — 2026-03-26
- [ ] 03_modules/auth-flow/srs/flows.md — chưa có
- [ ] 03_modules/auth-flow/srs/states.md — chưa có
- [ ] 03_modules/auth-flow/srs/erd.md — chưa có
- [ ] 03_modules/auth-flow/srs.md — chưa có
- [!] srs-compile-receipt.json (biên bản tổng hợp) — chưa có; chạy lại ba-start srs

[Khung giao diện dùng chung]
- [x] designs/{slug}/DESIGN.md — 2026-03-26
- [x] 02_backbone/shared-shell-contract.md — 2026-03-26
- [x] 02_backbone/shared-shell-index.md — 2026-03-26

[Tài liệu đã tổng hợp]
- [x] 04_compiled/compiled-frd.html — 2026-03-26

[Thiết kế]
- [ ] designs/{slug}/DESIGN.md — chưa có
- [x|!| ] ASCII màn hình — hiện tại/chưa có/cũ

[Làn ngược (Reverse Lane)]  ← bỏ qua khi không có reverse_baseline_lock
- [x|!| ] reverse-baseline-lock.json — {scan_timestamp} | chưa có
- [x|!| ] reverse-index.md — stale_status: {unknown|current|stale} | chưa có
- [x| ] reverse-focus-excerpts.md — {entry_count} excerpts | chưa có
- [x| ] reverse-evidence-ledger.md — {total} entries | chưa có
- [x| ] reverse-drift-state.json — có | chưa có

```

Status rules:

- Prefer current snapshot; otherwise stat files only.
- Print exists/missing with mtime; count SRS canon markdown files without opening them.
- Mark receipt current/missing/stale from mtime against canon source directories.
- Report shared shell separately from module SRS files.
- Figma readiness = canon + receipt + shell + `DESIGN.md`; detailed sync state belongs to sync reports.
- Read only compact memory metadata and delegation tracker state.
- Do not read artifact content.

Reverse lane status rules:
- Omit `[Reverse Lane]` when `reverse_baseline_lock` absent (stat only).
- When present: stat checks only — do not open reverse lane files to count entries.
- Mark reverse-index `[!]` when stale_status `unknown` or `stale`; suggest `ba-start reverse --slug <slug>`.
- When evidence counts unknown from stat: print `unclassified: unknown — run ba-start reverse status`.
- When all promoted and none unclassified: `Reverse lane complete. Consider /ba-start backbone --slug <slug>.`
