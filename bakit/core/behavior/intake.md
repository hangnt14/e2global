# Intake Behavior

## Read Scope

- Must read: `core/contract.yaml`, `core/contract-behavior.md`, `skills/ba-start/steps/intake.md`
- May read: `paths.source_summary`, `paths.source_chunk_index`, selected source chunks, `paths.project_memory` compact summary
- Must not read: memory shards, `log.md`, `paths.memory_index`

## Source Handling

- For large PDF, DOCX, Markdown, TXT, or pasted input, stage source material and use `ba-kit source-extract` before normalization.
- Read `paths.source_summary` first.
- Read `paths.source_chunk_index` before selecting chunk files.
- Open only chunk files needed for the current normalization pass.
- Reuse `plans/_source-cache/{source_hash}` when present.
