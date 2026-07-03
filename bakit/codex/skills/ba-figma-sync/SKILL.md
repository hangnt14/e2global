---
name: "ba-figma-sync"
description: "Sync approved BA-kit screen canon to Figma through Figma MCP. Downstream only; never mutates BA canon."
metadata:
  short-description: "Sync BA-kit SRS canon screens to Figma."
---

<codex_skill_adapter>
## A. Skill Invocation
- This skill is invoked by mentioning `$ba-figma-sync`.
- Treat all user text after `$ba-figma-sync` as `{{BA_ARGS}}`.
- If no arguments are present, treat `{{BA_ARGS}}` as empty.
</codex_skill_adapter>

<objective>
Synchronize approved BA-kit screen canon to Figma through the configured Figma MCP server.
</objective>

<required_reading>
Read these files in order:
- `@$HOME/.codex/ba-kit/contract.yaml`
- `@$HOME/.codex/ba-kit/contract-behavior.md`
- `@$HOME/.codex/ba-kit/behavior/figma-sync.md`
</required_reading>

<context>
{{BA_ARGS}}
</context>

<process>
1. Resolve `--slug`, `--date`, and `--module` exactly. If ambiguous, ask one focused question.
2. Run or follow the equivalent of `ba-kit check-prereq figma-sync --slug <slug> --module <module>`.
3. Run or follow the equivalent of `ba-kit doctor-srs plans/{slug}-{date}/03_modules/{module}`.
4. Read `srs-index.md`, then only the indexed screen canon files needed for sync.
5. Read `DESIGN.md`, `shared-shell-contract.md`, and optionally `shared-shell-index.md`.
6. If no Figma MCP tool is available, stop and report that no Figma changes were made.
7. Use Figma MCP to create/update frames from screen canon, ASCII wireframes, visual state coverage, and shared shell rules.
8. Write only `figma-sync/figma-sync-report.md` and `figma-sync/figma-mismatch-report.md`; never mutate BA canon.
</process>

<guardrails>
- Figma is downstream. It must not redefine requirements.
- If Figma differs from canon, write a mismatch report and ask the BA to update canon first when requirement meaning changed.
- Before repo writes, validate the target path with `ba-kit check-write-scope --command figma-sync <target-path>`.
</guardrails>
