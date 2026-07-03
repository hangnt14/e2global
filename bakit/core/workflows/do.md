<purpose>
Analyze freeform BA text and route it to the most appropriate BA-kit command.

This is a dispatcher. It should not do the downstream BA work itself.
</purpose>

<required_reading>
Read the installed BA playbook, `contract.yaml`, and `contract-behavior.md` before routing.
</required_reading>

<process>

<step name="validate">
If the input is empty, ask:

"What would you like to do? Describe the BA task, artifact, or requirement change and I will route it to the right BA-kit command."
</step>

<step name="preflight">
Detect BA-kit project context from CWD (matches `plans/{slug}-{date}` pattern). If a project is detected:

1. Extract slug and date from the plan directory name.
2. Run: `ba-kit guardrail --command status --slug <slug> --date <date>`.
3. If `status=block`:
   - Print compact advisory (≤150 chars):
     "BA-kit indexes missing for this legacy project. Run: python3 scripts/context-budget-bootstrap.py --repo . --slug {slug} --date {date}"
   - Continue routing — do NOT block the freeform request.
4. If `status=warn`:
   - Print compact advisory (≤100 chars):
     "Some BA-kit indexes are stale. Consider running index refresh before broad file reads."
   - Continue routing.
5. If `status=ok`: proceed silently.

This step is advisory only. It must not block, delay, or require user confirmation. The goal is awareness, not enforcement.
</step>

<step name="route">
Match intent using the first rule that fits:

| If the text describes... | Route to | Why |
| --- | --- | --- |
| publishing to Notion | `ba-notion` | publish workflow |
| syncing approved screen canon to Figma, creating Figma frames, updating Figma wireframes, or "đồng bộ Figma" | `ba-figma-sync` | downstream Figma MCP sync from canon |
| exporting BA artifacts for QC handoff, preparing QC-kit input, "xuất cho QC", "export QC", "qc handoff", or generating per-UC QC format | `ba-qc-export` | one-way export bridge to QC-kit |
| claiming/assigning a module, sending review, checking module conflict, approving/integrating module work, or GitHub PR/commit/merge handoff | `ba-collab` | BA collaboration workflow |
| checking status, completion, or missing artifacts | `ba-start status` | inspection path |
| asking to continue a project, resume work, or "toi nen lam gi tiep" | `ba-next` | BA-facing continuation path |
| asking what the next BA step should be | `ba-next` | state-aware recommendation |
| adding, changing, removing, or correcting a requirement/rule/scope item | `ba-impact` | change triage before mutation |
| a bare correction statement in an existing BA project context | `ba-impact` | safe default before edits |
| asking to prepare or refresh ASCII wireframes, UI screen visuals, or screen review evidence | `ba-start srs` | ASCII wireframes are mandatory in screen canon |
| asking to export, publish a review package, or create stakeholder handoff HTML | `ba-start package` | friendly alias for packaging |
| asking to brainstorm solution options, create multiple solution directions, compare solution approaches, choose an option, or skip optioning | `ba-start options` | pre-backbone decision support |
| reconstructing docs from existing source code, reverse-engineering requirements from a codebase, or "tao tai lieu tu code co san" | `ba-start reverse` | reverse mode entry — source-first reconstruction |
| checking reverse lane progress, baseline lock state, or evidence classification status | `ba-start reverse status` | reverse lane inspection |
| classifying reverse evidence, separating as-built drift from future-state requests | `ba-start reverse impact` | reverse evidence triage |
| promoting validated reverse evidence to backbone or SRS | `ba-start reverse promote` | reverse promotion path |
| exploring a vague idea, brainstorming a feature concept, or describing an idea without structured requirements ("ý tưởng", "brainstorm", "thử nghĩ", "explore idea", "idea cho feature", "tôi có ý tưởng") — no file path provided, no structured stakeholders/goals/scope | `/brainstorm` | pre-intake idea clarification |
| directly generating or rerunning intake/options/backbone/frd/stories/srs/package | `ba-start` with the matching subcommand | direct BA lifecycle step |
| a new BA engagement from raw input | `ba-start` | full lifecycle |

If the text could match both `ba-impact` and a direct edit request, prefer `ba-impact` unless the user explicitly says to update, edit, overwrite, regenerate, or rerun a named artifact or step.
</step>

<step name="display">
Show the decision:

```text
BA-kit Routing

Input: {short input excerpt}
Routing to: {command}
Reason: {one-line reason}
```
</step>

<step name="dispatch">
Hand off to the chosen command and stop.

Before dispatching to a guarded command (`ba-start frd`, `ba-start stories`, `ba-start srs`, `ba-start package`), instruct the runtime to run `ba-kit guardrail --command <cmd> --slug <slug> --date <date> [--module <module>]` first. If blocked, surface the message and the refresh command instead of proceeding.

Rules:
- `ba-impact` for requirement changes or correction statements
- `ba-next` for "what should I do next"
- `ba-start` for explicit lifecycle steps
- `ba-start reverse` for source-first reconstruction, reverse lane entry, refresh, promote, status, and impact
- `ba-collab` for module collaboration and approval-gated GitHub handoff
- `ba-notion` for publishing
- `ba-figma-sync` for downstream Figma MCP sync from approved SRS canon
- `ba-qc-export` for one-way BA-to-QC artifact export bridge

Reverse routing rules:
- Route to `ba-start reverse` only when the user explicitly signals source-code-first reconstruction, missing docs from existing code, or reverse lane commands.
- Do NOT route to `ba-start reverse` for normal forward-lifecycle BA work, even if the project has a reverse lane open.
- If the project has both a reverse lane and a forward lifecycle in progress, prefer the command the user explicitly named. If ambiguous, ask one focused question.

The dispatcher must not directly edit BA artifacts.
</step>

</process>

<success_criteria>
- [ ] Input validated
- [ ] Exactly one BA command chosen
- [ ] `ba-impact` preferred for ambiguous change statements
- [ ] Reverse intent routed to `ba-start reverse` only when explicitly signaled
- [ ] Routing reason shown before handoff
- [ ] Dispatcher does not mutate artifacts itself
</success_criteria>
