---
name: ba-do
description: Route freeform BA text to the right BA-kit command automatically.
argument-hint: "<description of the BA task or requirement change>"
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
---

# BA Do

Use this command when you know what you want to do in a BA workflow but do not know which BA-kit command should handle it.

## Invocation

```text
/ba-do xem next step cho project nay
/ba-do dang lam do SRS thi them yeu cau nay
/ba-do toi nhan module auth-flow
/ba-do gui module payment cho Lead BA review
/ba-do publish SRS len Notion
/ba-do đồng bộ Figma cho module auth-flow
/ba-do đồng bộ Stitch cho module auth-flow
/ba-do tạo UI từ SRS module payment
/ba-do tao tai lieu tu code co san
/ba-do reverse engineer requirements from codebase
/ba-do xem trang thai reverse lane
```

<execution_context>
Read `~/.claude/core/workflows/do.md`, `~/.claude/core/contract.yaml`, `~/.claude/core/contract-behavior.md`.
If missing, fall back to reading from the BA-kit repo root at `core/workflows/do.md`, etc.
</execution_context>

<context>
$ARGUMENTS
</context>

<process>
Execute the BA routing workflow from `core/workflows/do.md` end-to-end.
Dispatch to `ba-impact`, `ba-next`, `ba-start`, `ba-collab`, `ba-notion`, `ba-figma-sync`, or `ba-stitch-sync`.
</process>
