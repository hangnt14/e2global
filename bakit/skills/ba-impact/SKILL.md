---
name: ba-impact
description: Analyze requirement changes against the current BA artifact set and recommend the next exact commands without mutating artifacts.
argument-hint: "[--slug <slug>] [change statement|file]"
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
---

# BA Impact

Use this command when a requirement, rule, actor, scope item, or screen behavior changes in an existing BA project and you want impact analysis before editing anything.

## Invocation

```text
/ba-impact --slug warehouse-rfp Export CSV phai co audit log
/ba-impact --slug warehouse-rfp docs/changes/new-rule.md
/ba-impact Khong co nhom admin user
```

<execution_context>
Read `~/.claude/core/workflows/impact.md`, `~/.claude/core/contract.yaml`, `~/.claude/core/contract-behavior.md`.
If missing, fall back to reading from the BA-kit repo root at `core/workflows/impact.md`, etc.
</execution_context>

<context>
$ARGUMENTS
</context>

<process>
Execute the BA impact workflow from `core/workflows/impact.md` end-to-end.
Follow the `ba-start` impact contract exactly and return analysis only.
</process>
