# Figma Make UC Change Log

## Context

- Module: {module_slug}
- Use case: UC-{usecase_slug}
- Lane: `figma-make`
- Parent prompt: `uc-{usecase_slug}-make-prompt.md`

## Version history

| Version | Date | Author | Summary |
| --- | --- | --- | --- |
<!-- Add rows as versions are requested -->

## Change rules

1. Each version entry describes ONLY the approved prototype change for that version.
2. Material product/requirement drift must route through `ba-start impact` — do NOT smuggle requirement changes into change-log versions.
3. Each version includes its own paste-ready Figma Make prompt.
4. Older version prompts are kept for audit trail only; the latest version is the active Make prompt.

```
Example version entry:

## v{N} — {YYYY-MM-DD}

### Requested changes

- [Bullet list of approved prototype changes]

### Paste-ready Figma Make prompt

[Self-contained prompt. Reference shared skeleton for baseline.]

### Hard negatives

- Do not modify any other element
- Do not add fields not listed in the original UC prompt
- Do not add screens not listed in the original UC prompt
- Do not change navigation
- If uncertain, stop and ask instead of inventing
```
