---
name: ba-next
description: Detect the next logical BA-kit step from the current artifact set.
argument-hint: "[--slug <slug>]"
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
---

# BA Next

Use this command when you want BA-kit to inspect the current project set and tell you the next exact BA command to run.

## Invocation

```text
/ba-next
/ba-next --slug warehouse-rfp
```

<execution_context>
Read `~/.claude/core/workflows/next.md`, `~/.claude/core/contract.yaml`, `~/.claude/core/contract-behavior.md`.
If missing, fall back to reading from the BA-kit repo root at `core/workflows/next.md`, etc.
</execution_context>

<context>
$ARGUMENTS
</context>

<process>
Execute the BA next-step workflow from `core/workflows/next.md` end-to-end.
Recommend the next exact command without mutating artifacts.
</process>
