---
name: ba-start
description: Lifecycle engine for BA-kit. Accepts raw requirements, normalizes them, locks scope, builds a requirements backbone, emits canon-first SRS artifacts, and packages deliverables.
argument-hint: "[intake|impact|options|backbone|frd|stories|srs|package|status|next] [file|--slug|--date|--module|--mode|--select|--skip]"
---

# BA Start

Use this skill when the BA lifecycle step is explicit. Treat `ba-do` as the freeform router and `ba-start` as the execution engine.

## Required Read Order

1. Read `~/.claude/core/contract.yaml` for exact paths, prerequisites, defaults, states, command metadata, and `behavior_shards`. If missing, fall back to `../../core/contract.yaml` from the BA-kit repo root.
2. Read `~/.claude/core/contract-behavior.md` for shared runtime-neutral policy. If missing, fall back to `../../core/contract-behavior.md` from the BA-kit repo root.
3. Parse arguments and resolve the selected subcommand.
4. For guarded commands (`frd`, `stories`, `srs`, `package`, `status`, `next`): run `ba-kit guardrail --command <cmd> --slug <slug> --date <date> [--module <module>]`. If `status=block`, surface the block message and stop. Otherwise use `ALLOW_READS` for file discovery.
5. Read only the behavior shard(s) listed in `behavior_shards.<command>`.
6. Read only the matching file under `steps/`.
7. Read templates and upstream artifacts only when the active step actually needs them.

## Invocation

```text
/ba-start
/ba-start intake <file>
/ba-start impact --slug <slug> [change-file]
/ba-start options --slug <slug>
/ba-start options --slug <slug> --select option-02
/ba-start options --slug <slug> --skip
/ba-start backbone --slug <slug>
/ba-start frd --slug <slug> --module <module_slug>
/ba-start stories --slug <slug> --module <module_slug>
/ba-start srs --slug <slug> --module <module_slug>
/ba-start package --slug <slug>
/ba-start status --slug <slug>
/ba-start next --slug <slug>
/ba-start reverse --slug <slug> [--focus <area>] [--commit <hash>]
```

Figma MCP sync is intentionally outside `ba-start`. Use `ba-figma-sync` only after `ba-start srs` has produced current canon sources, `ascii-screen/index.md`, `srs.md`, and `srs-compile-receipt.json`.

## Step Dispatch

| Command | Read next | Notes |
| --- | --- | --- |
| no subcommand | `steps/intake.md`, then downstream gated steps | full lifecycle |
| `intake` | `steps/intake.md` | Steps 1-4 |
| `impact` | `steps/impact.md` | analysis only |
| `options` | `steps/options.md` | pre-backbone optioning |
| `backbone` | `steps/backbone.md` | Step 5 |
| `frd` | `steps/frd.md` | Step 6 |
| `stories` | `steps/stories.md` | Step 7 |
| `srs` | `steps/srs.md` | Canon-first SRS router; owns `userstories/`, `usecases/`, `ascii-screen/`, `srs/`, compiled `srs.md`, and compile receipt |
| `wireframes` | `steps/wireframes.md` | Deprecated compatibility validation; ASCII belongs in `ascii-screen/*.md` |
| `package` | `steps/package.md` | Step 12 |
| `status` | `steps/status.md` | inspection only |
| `next` | `~/.claude/core/workflows/next.md` (fallback: `../../core/workflows/next.md`) | next-step recommendation; no mutation |
| `reverse` | `steps/reverse.md` | scan/lock; refresh; promote |
| `reverse status` | `steps/reverse-status.md` | progress; no mutation |
| `reverse impact` | `steps/reverse-impact.md` | classify evidence |

## Fast Execution Contract

1. Parse arguments before doing any work.
2. Resolve the command and target scope with exact matching only.
3. Enforce prerequisites from the already-read `~/.claude/core/contract.yaml` (or repo root fallback).
4. Stop on ambiguity instead of guessing.
5. Ask before overwriting any mutable target.
6. Keep the accepted rerun step locked once the user approves it.

## Stop Conditions

- If `behavior_shards.<command>` references a missing path, stop and report the exact missing shard path.
- Never silently choose a slug, date, or module by mtime.
- Never use broad `*-{slug}*` matching when exact modular paths exist.
- Never mutate artifacts from a bare change statement; route through `impact` first.
- Never delegate merge or packaging assembly of large artifacts.

## Shared References

- [~/.claude/templates/manifest.json](~/.claude/templates/manifest.json) (fallback: [../../templates/manifest.json](../../templates/manifest.json))
- [~/.claude/templates/sub-agent-handoff-template.md](~/.claude/templates/sub-agent-handoff-template.md) (fallback: [../../templates/sub-agent-handoff-template.md](../../templates/sub-agent-handoff-template.md))
