# Using BA-kit With Codex

## Purpose

BA-kit can work with Codex as a repo-native BA operating guide. The root [AGENTS.md](../AGENTS.md) gives Codex persistent instructions, while the `skills/`, `rules/`, and `templates/` folders provide detailed task guidance.

## What Codex Uses

- [AGENTS.md](../AGENTS.md) as the persistent repo instruction file
- `skills/` as reference playbooks for BA task types
- `rules/` as BA quality and workflow constraints
- `templates/` as deliverable structures
- `designs/` for project-specific runtime `DESIGN.md` files used to constrain screen canon ASCII

## Codex Conversion Install

If you have the Codex-converted bundle for `ba-start`, install it from the repository root with:

```bash
bash scripts/install-codex-ba-kit.sh
```

The installer expects the converted source tree under:

- `codex/skills/**`
- `codex/agents/**`

It copies those files into:

- `~/.codex/skills`
- `~/.codex/agents`
- `~/.codex/templates`
- `~/.codex/ba-kit`

It also appends any missing Codex agent registrations into `~/.codex/config.toml` in an idempotent way, so rerunning the script is safe.
It also refreshes the shared `ba-kit` update command in `~/.local/bin/ba-kit` and records the source repo for future one-command updates.
The same install now stages the low-token guardrail runtime bundle under `~/.codex/ba-kit/`:

- `core/`
- `scripts/guardrail-preflight.py`
- `scripts/guardrail-build-excerpts.py`
- `scripts/guardrail-audit.py`
- `scripts/validate-index-quality.py`
- `docs/runtime-hard-guardrails.md`

Prerequisite:
- `node` must be available because the installer uses a small Node.js registration step.

After installation, update BA-kit with:

```bash
ba-kit doctor
ba-kit update
ba-kit status --slug warehouse-rfp
```

`ba-kit doctor` and `ba-kit status` also surface update availability when the registered upstream branch is ahead of the local install.

## Low-Token Guardrail Preflight

For `frd`, `stories`, `package`, `status`, and `next`, the preferred first pass is to run the repo guardrail scripts before starting `codex exec`, then inject only the compact verdict plus exact path hints.

Preflight example:

```bash
python3 ~/.codex/ba-kit/scripts/guardrail-preflight.py \
  --repo /path/to/ba-kit-project \
  --command stories \
  --slug warehouse-rfp \
  --date 260331-1015 \
  --module auth-flow \
  --output /tmp/ba-kit-preflight.json
```

Behavior:

- `status=block`: do not start Codex; surface `message` and run `refresh_command`. Emit a `probe` packet only: `output_mode=probe`, `status`, `command`, `resolved_slug`, `message`.
- `status=ok` or `status=warn` with current index: emit a `delta` packet — portable-core fields (`status`, `command`, `resolved_slug`, `resolved_module`, `guardrail_mode`, `reason`, `message`, `indexes`) plus `action_guardrail` (if present), `allow_reads`, and any generated excerpt path.
- broad read required or no current index: emit a `full` packet — delta fields plus `deny_reads`, `canonical_state_summary`, `canonical_next_command`, and `refresh_command` (if block). Emit `READ_ESCALATION: {command} read {path} due to {reason}.` before the read.

See `CLAUDE.md` Runtime Guardrails → Output Modes for the canonical field definitions.

Optional targeted excerpt build:

```bash
python3 ~/.codex/ba-kit/scripts/guardrail-build-excerpts.py \
  --repo /path/to/ba-kit-project \
  --index-key backbone_index \
  --slug warehouse-rfp \
  --date 260331-1015 \
  --module auth-flow \
  --output-dir /tmp/ba-kit-guardrail
```

Optional post-run audit when a runtime trace or read manifest exists:

```bash
python3 ~/.codex/ba-kit/scripts/guardrail-audit.py \
  --preflight /tmp/ba-kit-preflight.json \
  --reads-manifest /tmp/ba-kit-reads.json \
  --output /tmp/ba-kit-audit.json
```

The Codex install manifest at `~/.local/share/ba-kit/installations/codex.env` records the staged guardrail paths as `BA_KIT_GUARDRAIL_*` variables.
It also records `BA_KIT_INDEX_VALIDATOR` so wrappers can run the producer-side validator without rediscovering paths.

Producer-side reminder:

- after generating `backbone_index`, `stories_index`, or `srs_index`, run `validate-index-quality.py --writeback`
- do not treat a newly written index as trusted until the validator stamps `validated_at`, `validated_by`, and promotes `stale_status` to `current`
- for each downstream `frd`, `stories`, `package`, `status`, or `next` action that can route from backbone, re-send only the compact `ACTION_GUARDRAIL` packet instead of reopening full backbone context

Or ask Codex to run:

```text
/ba-kit-update
/ba-do dang lam do SRS thi them yeu cau nay
/ba-impact --slug warehouse-rfp Khong co nhom admin user
/ba-next --slug warehouse-rfp
/ba-collab Toi nhan module auth-flow
/ba-notion srs --slug warehouse-rfp --page https://www.notion.so/... --mode overwrite
```

## Recommended Codex Workflow

1. Start with the business outcome or artifact you need, not command names.
2. For freeform BA requests, use `ba-do` as the router first.
3. Tell Codex to read `PROJECT-HOME.md` when present, then use the BA playbook for the resolved step.
4. If UI is involved, point it at the relevant project `DESIGN.md`, system shared shell contract, and module SRS canon files under `screens/`, `usecases/`, and `srs-index.md`.
5. For collaboration, use `ba-collab` for module claims, review packets, conflict checks, and approval-gated GitHub handoff.
6. Use `/ba-start` for full workflow runs and the matching explicit subcommand for reruns.
7. Use `/ba-start options --slug <slug>` when intake should brainstorm solution options before the backbone is written.
8. Use `/ba-start options --slug <slug> --select option-02` to lock the chosen direction after reviewing the option pack.
9. Use `/ba-start options --slug <slug> --skip` when the team explicitly wants to bypass optioning and move on.
10. The option pack and comparison live under `plans/{slug}-{date}/01_intake/options/`.
11. For rerun commands, pass `--slug <slug>` when more than one project may exist.
12. If one slug has multiple dated artifact sets, Codex should stop and ask which date to use instead of silently taking the latest set.
13. When a requirement or rule changes during `frd`, `stories`, `srs`, `wireframes`, or `package`, route through `/ba-start impact --slug <slug>` before mutating downstream artifacts unless the edit is clearly wording-only.
14. If the user describes a change in natural language without naming a subcommand, infer the equivalent of `impact` when the project set already exists.
15. If the user sends only a short correction statement such as `Không có nhóm admin user`, treat it as change evidence for `impact`, not as permission to edit artifacts directly.
16. Ask for assumptions, open questions, and a draft output.
17. If you installed the Codex conversion, ask Codex to use `ba-do` from `~/.codex/skills/ba-do/SKILL.md` for freeform routing, `ba-start` from `~/.codex/skills/ba-start/SKILL.md` for explicit lifecycle execution, and the registered BA agents from `~/.codex/agents`.
18. Unless you explicitly override it, BA-kit should use Shadcn UI as the default component baseline for screen canon ASCII and UI handoff.
19. Before Step 9 is run, BA-kit should ask for or confirm the design decisions needed to persist the project runtime artifact `designs/{slug}/DESIGN.md`, then use that file as the system design document.
20. Unless you explicitly override it, BA deliverables should be written in Vietnamese.
21. Treat the dated artifact-set token as `YYMMDD-HHmm` across both report filenames and `plans/{slug}-{date}/01_intake/plan.md`.
22. When delegating, pass only narrow artifact slices and exact excerpts, not full upstream documents.
23. If a delegated worker reports missing context or `NEEDS_REPARTITION`, split the scope and rerun only that slice.
24. For non-trivial delegation, use the packet structure from `templates/sub-agent-handoff-template.md` or the equivalent snippet embedded in `ba-start`.
25. For `srs`, resolve the exact backbone and user-stories artifacts first and pull the FRD only when it exists or is required instead of scanning every report in `plans/reports/final/` and `plans/reports/drafts/`.
26. For `frd` and `stories`, resolve the exact backbone prerequisite first and begin authoring from that file instead of scanning every report in `plans/reports/final/`.
27. If only legacy report names like `002-intake-form.md` exist, stop and migrate or rerun them explicitly; do not infer the current slug/date from legacy filenames.
28. If context truncation happens after the target workflow was already confirmed, recover from the resolved command and exact artifacts on disk instead of asking the user to restate the task.
29. Once the user explicitly approves a mutating rerun step, keep that step locked for the current run and do not fall back to generic "what do you want me to do with this document?" prompts.
30. For non-trivial delegated work, create a dedicated tracker under `plans/{slug}-{date}/delegation/` and pass its path into the worker packet.
31. Treat a delegated slice as likely stalled when its tracker has no heartbeat for more than 10 minutes and the target artifact has not advanced.

Global command helpers after Codex install:
- `ba-do` — preferred freeform router for BA requests
- `ba-impact` — run change-impact triage without mutating artifacts
- `ba-next` — inspect the current artifact set and recommend the next BA command
- `ba-figma-sync` — sync approved screen canon to Figma through Figma MCP

Use `options` when intake needs multiple solution directions before backbone. The commands are:

```text
/ba-start options --slug warehouse-rfp
/ba-start options --slug warehouse-rfp --select option-02
/ba-start options --slug warehouse-rfp --skip
```

## Prompt Patterns

### Full BA Engagement

```text
Use the installed `ba-do` skill from ~/.codex/skills/ba-do/SKILL.md.
Route this BA request to the correct BA-kit command and then follow that workflow:
"Parse the requirements in docs/raw/warehouse-rfp.pdf.
Default to `hybrid` mode for a solo IT BA.
If intake recommends multiple solution directions, create the option pack + comparison before backbone.
Then build the requirements backbone and emit FRD, user stories, use case specifications, Screen Contract Plus, screen canon with mandatory ASCII wireframes, final screen descriptions, and FRD/SRS HTML only when each artifact is justified.
If UI support is needed, ask me for design decisions and persist `designs/{slug}/DESIGN.md` before ASCII generation."
```

### Step-Level Rerun

```text
Use AGENTS.md and skills/ba-start/SKILL.md.
Run the equivalent of `/ba-start srs --slug warehouse-rfp --module auth-flow` for screen-canon ASCII refresh.
Use the existing Screen Contract Plus artifacts only.
Reuse the existing `designs/{slug}/DESIGN.md` if it is approved, otherwise ask to refresh it before preparing ASCII wireframes.
If more than one dated set exists for `warehouse-rfp`, stop and ask me which date to use.
Do not regenerate intake, FRD, or user stories.
```

### Options Before Backbone

```text
Use AGENTS.md and skills/ba-start/SKILL.md.
Run the equivalent of `/ba-start options --slug warehouse-rfp`.
If the option pack already exists under `plans/{slug}-{date}/01_intake/options/`, review it first.
If one option is accepted, run `/ba-start options --slug warehouse-rfp --select option-02`.
If optioning is unnecessary, run `/ba-start options --slug warehouse-rfp --skip`.
Keep the decision explicit before `/ba-start backbone --slug warehouse-rfp`.
```

### Change Impact Triage

```text
Use AGENTS.md and skills/ba-start/SKILL.md.
I am midway through the SRS for slug warehouse-rfp and this new requirement arrived:
"Every export must require explicit permission, write an audit log, and display a success or failure banner."
Run the equivalent of `/ba-start impact --slug warehouse-rfp`.
Resolve the exact dated set instead of choosing by mtime.
Tell me the current source of truth, the affected artifacts, the unaffected artifacts, and the exact commands I should run next.
If the change is only wording-only, say so explicitly and keep the rerun path narrow.
```

### BA Router

```text
Use the installed `ba-do` skill from ~/.codex/skills/ba-do/SKILL.md.
Route this BA request to the right BA-kit command:
"Dang lam do SRS thi them yeu cau moi ve audit log."
```

### BA-Friendly Resume

```text
Use AGENTS.md.
Read PROJECT-HOME.md for slug warehouse-rfp if it exists.
Tell me the next step in BA-friendly Vietnamese first.
Then show the internal BA-kit command equivalent and run it only if safe.
```

### BA Collaboration

```text
Use AGENTS.md and skills/ba-collab/SKILL.md.
I claim module auth-flow.
Create or update the collaboration artifacts, but do not commit, push, create PR, or merge without my explicit approval.
```

### BA Next

```text
Use the installed `ba-next` skill from ~/.codex/skills/ba-next/SKILL.md.
Inspect the current BA artifact set and tell me the next exact command to run.
Do not mutate any artifact.
```

### Package Only

```text
Use AGENTS.md and skills/ba-start/SKILL.md.
Run the equivalent of `/ba-start package --slug warehouse-rfp`.
If the wireframe state is `missing`, stop and tell me to rerun `wireframes`.
If the wireframe state is `completed`, `skipped`, or `not-applicable`, continue to HTML packaging.
Keep the package scope narrow: regenerate final FRD and SRS HTML when those markdown artifacts exist, unless I explicitly ask for a broader HTML repack.
```

### Status Check

```text
Use AGENTS.md and skills/ba-start/SKILL.md.
Run the equivalent of `/ba-start status --slug warehouse-rfp`.
Print artifact names, exists or missing status, last-modified dates, the persisted backbone, the explicit wireframe state, and any persisted wireframe input/map artifacts when present.
Also print any delegation trackers under `plans/{slug}-{date}/delegation/`, including `running`, `blocked`, `needs-repartition`, or likely stalled slices.
```

### Publish To Notion

```text
Use AGENTS.md and skills/ba-notion/SKILL.md.
Publish the exact `srs` artifact for slug warehouse-rfp to Notion.
If I provided a page URL, update that page.
If I provided only a parent page, create a new child page.
Choose `overwrite`, `append`, or `fill-gaps` based on my request.
Do not silently choose a slug or dated set by mtime.
```

### Codex Conversion

```text
Use the installed ba-start skill from ~/.codex/skills/ba-start/SKILL.md.
Use the registered Codex BA agents from ~/.codex/agents when the skill delegates work.
Parse the requirements in docs/raw/warehouse-rfp.pdf.
Produce an intake form, requirements backbone, gated FRD/stories/SRS artifacts, project runtime `DESIGN.md`, screen canon with mandatory ASCII wireframes, final screen descriptions, and the FRD/SRS HTML deliverables required by the selected mode.
```

### Formal Requirements Only

```text
Use AGENTS.md and skills/ba-start/SKILL.md.
Draft an SRS from templates/srs-template.md.
Include use cases, screen descriptions, and linked requirements.
Make room for user-supplied wireframe references under each screen section instead of assuming BA-kit-generated mockups.
```

### Agile Story Breakdown

```text
Use AGENTS.md and skills/ba-start/SKILL.md.
Break this feature into epics, features, and stories.
Use templates/user-story-template.md.
Keep acceptance criteria testable and align any UI stories to the SRS screens.
```

## Important Constraint

The `skills/` directory is written in Claude-style skill format. Codex should treat those files as instruction content to read and apply, not as an automatic native skill system.

That means prompts should explicitly tell Codex which playbook to consult when the task is non-trivial.
The root `AGENTS.md` carries the short non-negotiable defaults, but it does not replace the detailed routing and prerequisite logic in `skills/ba-start/SKILL.md`.
For delegated BA work, resolve the workflow once in the orchestrator, then pass only the minimal handoff packet to each registered agent instead of replaying the entire playbook and merged artifact set every time.

## ASCII Wireframes For Codex

Use the canon-first BA-kit flow for UI-backed SRS work:
- persist or reuse `designs/{slug}/DESIGN.md` for visual direction
- keep shared menu/layout ownership in `shared-shell-contract.md`
- author screen behavior and ASCII wireframes in `screens/*.md`
- compile the reader-facing `srs.md` and `srs-compile-receipt.json` from canon sources
- treat Figma MCP sync as a separate downstream lane that writes sync/mismatch reports, not BA canon

## HTML Deliverable

The generated HTML set uses one shared BA-kit document shell. Open the packaged artifacts in a browser to update text, replace images, and add or remove blocks without editing the source HTML manually. SRS HTML remains the primary stakeholder handoff, while FRD HTML provides the aligned functional review copy. The `package` step should stay narrow by default: validate any existing packaged HTML artifacts, then regenerate FRD and SRS HTML only when those markdown artifacts exist.

If the user manually inserts wireframe images or links into the markdown source, the packaged HTML preserves those references only when the asset path stays inside the allowed base directory. Mermaid diagrams are bootstrapped explicitly after `DOMContentLoaded`, while PlantUML diagrams always prefer local rendering. Use `ba-kit install-plantuml` to auto-install PlantUML locally, or `--auto-install-plantuml` when running the renderer, before considering a configured server fallback.

`/ba-start status` should report screen canon ASCII coverage, compile receipt state, and shared shell state. It should also surface delegated slice trackers and flag likely stalls from stale heartbeats.

## Good Outcomes

You are set up correctly when Codex can:
- follow `AGENTS.md` without extra repo explanation
- use `PROJECT-HOME.md` as a BA-facing resume dashboard without treating it as source of truth
- use `COLLAB-HOME.md`, `MODULE-HOME.md`, and review packets for BA collaboration without exposing Git first
- read the BA playbook from `skills/ba-start/SKILL.md`
- draft a structured artifact from `templates/`
- reference screen canon ASCII and optional user-supplied mockups consistently from the SRS
