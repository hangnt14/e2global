# BA-kit Getting Started

## Purpose

This guide shows how to install BA-kit and use it in Claude Code and Codex.

For BA non-tech usage, start from natural-language requests and `PROJECT-HOME.md`. Commands remain available for precise reruns, but they should not be the first thing a BA has to learn.

## 1. Clone The Repository

```bash
git clone https://github.com/anhdam2/bakit.git
cd bakit
```

## 2. Choose Your Runtime

BA-kit supports two usage modes:
- **Claude Code**: install BA-kit assets into `~/.claude`
- **Codex**: open the repo and use the root `AGENTS.md`

## 3. Install For Claude Code

Run:

```bash
./install.sh
```

What this installs:
- skills to `~/.claude/skills/`
- agents to `~/.claude/agents/`
- rules to `~/.claude/rules/ba-kit/`
- templates to `~/.claude/templates/`
- shared BA workflows and references to `~/.claude/ba-kit/`
- the shared update command to `~/.local/bin/ba-kit`

Then restart Claude Code if it is already open.

To update later, use these maintenance commands as needed:

```bash
ba-kit doctor
ba-kit install-plantuml
ba-kit update
ba-kit status --slug warehouse-rfp
```

This checks the registered BA-kit source repo, blocks when the repo has local changes or unfinished merge/rebase state, runs `git pull --ff-only`, then reruns the installers for any previously installed runtimes.
`ba-kit status` reads the registered source repo, prints the current artifact set, and flags likely stalled delegated slices from stale tracker heartbeats.
`ba-kit doctor` checks runtime readiness: install manifests, registered repo health, required local tools, and optional MCP hints for Notion.
`ba-kit install-plantuml` attempts to install PlantUML locally through a supported package manager so HTML packaging can render swimlanes without sending diagrams to a remote service.
Both commands also surface update availability when the registered upstream has newer commits.

## 4. Use BA-kit In Claude Code

Preferred natural-language entry:

```text
/ba-do <description>
```

Use `/ba-start` when you already know the lifecycle step, want the full BA pipeline, or need the reverse as-built lane.

Full workflow:

```text
/ba-start
```

BA-friendly workflow:

```text
/ba-do Tôi có tài liệu yêu cầu mới, hãy tạo dự án BA
/ba-do Tiếp tục dự án warehouse-rfp, bước tiếp theo là gì?
/ba-do Đánh giá thay đổi: Export CSV phải có audit log
/ba-do Phân tích ngược hệ thống hiện tại để tạo as-built SRS
/ba-do Chuẩn bị handoff UI cho module auth-flow
/ba-do Đồng bộ Figma cho module auth-flow của dự án warehouse-rfp
/ba-do Tôi nhận module auth-flow
/ba-do Gửi module auth-flow cho Lead BA review
/ba-do Xuất gói bàn giao cho stakeholder
```

Step-level reruns:

```text
/ba-start intake docs/raw/warehouse-rfp.pdf
/ba-start impact --slug warehouse-rfp
/ba-start options --slug warehouse-rfp
/ba-start options --slug warehouse-rfp --select option-02
/ba-start options --slug warehouse-rfp --skip
/ba-start backbone --slug warehouse-rfp
/ba-start frd --slug warehouse-rfp --module auth-flow
/ba-start stories --slug warehouse-rfp --module auth-flow
/ba-start srs --slug warehouse-rfp --module auth-flow
/ba-start wireframes --slug warehouse-rfp --module auth-flow
/ba-start package --slug warehouse-rfp
/ba-start status --slug warehouse-rfp
/ba-start reverse --slug warehouse-rfp
/ba-start reverse impact --slug warehouse-rfp
/ba-figma-sync --slug warehouse-rfp --module auth-flow
/ba-notion srs --slug warehouse-rfp --page https://www.notion.so/... --mode overwrite
```

Router and deterministic helpers:

```text
/ba-do dang lam do SRS thi them yeu cau nay
/ba-impact --slug warehouse-rfp Khong co nhom admin user
/ba-next --slug warehouse-rfp
/ba-collab Tôi nhận module auth-flow
```

Use `options` when intake needs multiple solution directions before the backbone is written. The pre-backbone option pack and comparison live under `plans/{slug}-{date}/01_intake/options/`.

Use `reverse` when the goal is to document the system as implemented today. Reverse mode produces evidence-backed as-built outputs, not future-state proposals. If the user is asking for a change, new capability, or desired target behavior, route that request through `impact` or the normal forward lifecycle instead. In reverse mode, wireframes are skipped / not-applicable because no new UI is being proposed.

Default `/ba-start` handles the full BA lifecycle once routing is already clear:
1. Parse raw input into an intake form
2. Gap analysis and clarifying questions
3. Scope lock and mode selection
4. Option pack + comparison when intake needs multiple solution directions
5. Requirements backbone production
6. Gated FRD and user story generation
7. Selective SRS production
8. Design decision capture and project runtime `DESIGN.md` creation when UI support is justified
9. Mandatory ASCII wireframe production inside `screens/*.md` from the use cases, Screen Contract Plus, locked IA snapshot, and approved `DESIGN.md`
10. Final screen description production as an enrich pass from screen canon
11. HTML packaging for the emitted artifact set

### Claude Example

```text
/ba-start
Here is our requirements doc: docs/raw/warehouse-rfp.pdf
```

When prompted, provide the file path or paste your requirements text. The skill will:
1. Parse and normalize the input into a structured intake form
2. Identify gaps (missing stakeholders, unclear scope, no success criteria)
3. Ask 3-8 clarifying questions
4. Generate `PROJECT-HOME.md` so the BA can resume from a plain-language dashboard
5. Generate a scoped work plan
6. Open an option pack + comparison first when intake recommends multiple solution directions; otherwise proceed directly to the requirements backbone
7. Emit FRD, user stories, use cases, Screen Contract Plus, project runtime `DESIGN.md`, screen canon with mandatory ASCII, final screen descriptions, and FRD/SRS HTML output only when their gates are open

For rerun commands:
- pass `--slug <slug>` when more than one project exists
- if one slug has multiple dated artifact sets, BA-kit should stop and ask which set to use
- use `/ba-start status --slug <slug>` to inspect completion before rerunning a downstream step
- use `/ba-start impact --slug <slug>` when a requirement, rule, scope item, actor responsibility, or screen behavior changes while a downstream artifact is already being drafted
- treat `impact` as the default change-triage path when the user says things like "đang làm dở SRS thì thêm yêu cầu này" unless the edit is obviously wording-only
- treat a short correction statement like "Không có nhóm admin user" as `impact` in an existing project context; do not interpret it as a direct edit request unless the user explicitly asks to update an artifact
- for `srs`, start from the exact resolved backbone and user-stories artifacts, and pull the FRD only when it exists or is required, instead of rereading the whole `plans/reports/final/` and `plans/reports/drafts/` directories
- for `frd` and `stories`, start from the exact resolved backbone artifact instead of rereading the whole `plans/reports/final/` directory
- if you only have old reports named like `002-intake-form.md`, treat them as a legacy suite and rerun or migrate them before expecting the current `/ba-start` contract to resume from them
- for non-trivial delegated work, expect BA-kit to create trackers under `plans/{slug}-{date}/delegation/`
- treat a delegation tracker with no heartbeat for more than 10 minutes as likely stalled and inspect or rerun that slice instead of waiting blindly
- once you explicitly approve a mutating rerun step, BA-kit should continue that step instead of reverting to generic prompts about what to do with the document

## 5. Use BA-kit In Codex

Codex does not need `install.sh`.

Instead:
1. Open this repository in Codex
2. Make sure the root `AGENTS.md` is visible in the repo
3. For freeform BA requests, tell Codex to use `skills/ba-do/SKILL.md` first
4. Tell Codex to use `skills/ba-start/SKILL.md` when the lifecycle step is explicit
5. Point Codex to the correct template under `templates/`
6. If you have the Codex-converted bundle, run `bash scripts/install-codex-ba-kit.sh` once to copy the skills, agents, templates, and core contract into `~/.codex`, then register Codex agents in `~/.codex/config.toml`
7. If you use the installer, make sure `node` is available because the registration step runs on Node.js
8. The installer also records the source repo for the shared update command `ba-kit update`
9. The Codex installer also copies shared BA workflows and contract references into `~/.codex/ba-kit/`

### Codex Example

```text
Use AGENTS.md and skills/ba-start/SKILL.md.
Parse the requirements in docs/raw/warehouse-rfp.pdf.
Include use cases, Screen Contract Plus, a project runtime `DESIGN.md`, screen canon with mandatory ASCII wireframes, final screen descriptions, linked requirements, and test cases.
```

BA-friendly Codex resume prompt:

```text
Use AGENTS.md.
Read PROJECT-HOME.md for slug warehouse-rfp if it exists.
Tell me the next BA step in Vietnamese first, then run the safe BA-kit workflow for that step.
```

If the Codex conversion is installed, you can point Codex directly at the bundled skill:

```text
Use ~/.codex/skills/ba-start/SKILL.md and the registered BA agents under ~/.codex/agents.
Parse the requirements in docs/raw/warehouse-rfp.pdf.
Produce an intake form, a requirements backbone, gated FRD/stories/SRS artifacts, a project runtime `DESIGN.md`, screen canon with mandatory ASCII wireframes, final screen descriptions, and browser-editable FRD/SRS HTML when those artifacts are emitted.
```

For partial reruns in Codex, be explicit about the target slug and dated set when ambiguity exists. Example:

```text
Use AGENTS.md and skills/ba-start/SKILL.md.
Run only the SRS screen-canon ASCII refresh path for slug warehouse-rfp.
If multiple dated sets exist for that slug, stop and ask me which date to use.
Reuse the existing `designs/{slug}/DESIGN.md` if it is approved, otherwise ask me to refresh it before UI-backed SRS work.
Use `screens/*.md`, `usecases/*.md`, `srs-index.md`, and `srs-compile-receipt.json` as the SRS canon-first source set.
Then report `/ba-start status` semantics with artifact dates, canon source counts, ASCII coverage, compile receipt state, and shared shell state.
```

Change-impact triage in Codex:

```text
Use AGENTS.md and skills/ba-start/SKILL.md.
I am writing the SRS for slug warehouse-rfp and this new requirement arrived:
"Export CSV must require permission, record an audit log, and show a success or failure banner."
Run the equivalent of `/ba-start impact --slug warehouse-rfp`.
Resolve the exact dated set instead of choosing by mtime.
Tell me the source of truth to update, the affected artifacts, and the exact commands to run next.
```

See [codex-setup.md](./codex-setup.md) for more prompt patterns.

Runtime defaults for both Claude Code and Codex:
- BA deliverables are written in Vietnamese by default unless the user explicitly requests English
- the dated artifact-set token is `YYMMDD-HHmm` across report filenames and `plans/{slug}-{date}/01_intake/plan.md`
- Shadcn UI is the default wireframe constraint baseline unless explicitly overridden by the approved project `DESIGN.md`

`plans/` is a local runtime workspace. BA-kit writes generated plans and report artifacts there during an engagement, but those files are not meant to stay version-controlled in the toolkit repository.

## 5.1 Update BA-kit

Once you have installed BA-kit for Claude Code, Codex, or both, update it with:

```bash
ba-kit doctor
ba-kit update
```

Or from inside the agents:

```text
/ba-kit-update
/ba-notion frd --slug warehouse-rfp --parent https://www.notion.so/... --mode create
```

Expected behavior:
- read the registered source repo from the local install manifests
- fail fast if the repo has local edits, conflict state, or multiple conflicting source repos
- run `git pull --ff-only`
- rerun `install.sh` and/or `scripts/install-codex-ba-kit.sh` for the runtimes already installed from that repo

## 6. Add Mandatory ASCII Wireframes For SRS Work

BA-kit requires ASCII wireframes directly in screen canon for UI-backed SRS work.

Before Step 9 prepares or reruns ASCII coverage, capture or confirm the project-specific design decisions and persist them to:

```text
designs/[initiative-slug]/DESIGN.md
```

This `DESIGN.md` is a project-specific runtime artifact, not a BA-kit product artifact. It summarizes the approved visual tone, colors, typography, component feel, layout principles, responsive behavior, and anti-patterns for that initiative. Machine-readable menu/layout ownership belongs in the system-level shared shell contract, not in module screen prose.

The canon-first UI-backed SRS outputs are:

```text
designs/[initiative-slug]/DESIGN.md
plans/{slug}-{date}/02_backbone/shared-shell-contract.md
plans/{slug}-{date}/02_backbone/shared-shell-index.md
plans/{slug}-{date}/03_modules/{module_slug}/screens/*.md
plans/{slug}-{date}/03_modules/{module_slug}/usecases/*.md
plans/{slug}-{date}/03_modules/{module_slug}/srs-index.md
plans/{slug}-{date}/03_modules/{module_slug}/srs.md
plans/{slug}-{date}/03_modules/{module_slug}/srs-compile-receipt.json
```

Rules:
- keep screen IDs aligned between screen canon, use cases, compiled SRS, and any downstream visual output
- use the approved `DESIGN.md` as visual direction and the shared shell contract as menu/layout authority
- use Shadcn UI as the default component baseline only when `DESIGN.md` does not specify a different direction
- keep screen canon focused on behavior, validation, states, navigation, traceability, and ASCII wireframe coverage
- Figma MCP sync is downstream from canon and writes sync/mismatch reports instead of redefining requirements
- treat the packaged HTML suite as the editable stakeholder copy: update text, swap images, and add or remove blocks directly in the browser without editing the source HTML

## 7. Deliverables And Runtime Artifacts

A full `/ba-start` engagement produces final BA deliverables plus runtime artifacts used during downstream design handoff:

| Deliverable | Template | Location |
| --- | --- | --- |
| Project Home / BA dashboard | `project-home-template.md` | `plans/{slug}-{date}/PROJECT-HOME.md` |
| Collab Home / BA collaboration dashboard | `collab-home-template.md` | `plans/{slug}-{date}/COLLAB-HOME.md` |
| Module Home | `module-home-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/MODULE-HOME.md` |
| Module review packet | `review-packet-template.md` | `plans/{slug}-{date}/delegation/review-packets/{module_slug}.md` |
| Intake form | `intake-form-template.md` | `plans/{slug}-{date}/01_intake/intake.md` |
| Requirements backbone | `requirements-backbone-template.md` | `plans/{slug}-{date}/02_backbone/backbone.md` |
| FRD | `frd-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/frd.md` |
| FRD HTML | `scripts/md-to-html.py` | `plans/{slug}-{date}/04_compiled/compiled-frd.html` with rendered Mermaid and safely handled PlantUML diagrams |
| SRS | `srs-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/srs.md` |
| User stories | `userstory-item-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/userstories/us-{slug}.md` |
| User stories index | `userstories-index-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/userstories/index.md` |
| Project runtime DESIGN.md (bán thành phẩm) | `design-md-template.md` | `designs/{slug}/DESIGN.md` |
| Shared shell contract | `shared-shell-contract-template.md` | `plans/{slug}-{date}/02_backbone/shared-shell-contract.md` |
| Screen canon | `ascii-screen-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/ascii-screen/{screen}.md` |
| Screen index | `ascii-screen-index-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/ascii-screen/index.md` |
| Use case canon | `usecase-item-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/usecases/uc-{slug}.md` |
| Use case index | `usecases-index-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/usecases/index.md` |
| SRS spec | `srs-spec-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/srs/spec.md` |
| SRS compile receipt | `srs-compile-receipt-template.md` | `plans/{slug}-{date}/03_modules/{module_slug}/srs-compile-receipt.json` |
| SRS HTML | `scripts/md-to-html.py` | `plans/{slug}-{date}/04_compiled/compiled-srs.html` as the primary browser-editable stakeholder copy |

If you need a clean read-only stakeholder handoff, generate HTML with:

```bash
python scripts/md-to-html.py --no-editor plans/{slug}-{date}/03_modules/{module_slug}/srs.md
```

If `plantuml` is not installed yet, install it locally first:

```bash
ba-kit install-plantuml
```

If you want the packaging script to attempt local installation automatically before rendering, use:

```bash
python scripts/md-to-html.py \
  --no-editor \
  --auto-install-plantuml \
  plans/{slug}-{date}/03_modules/{module_slug}/srs.md
```

Only when local rendering is unavailable should you fall back to a self-hosted or otherwise approved PlantUML service:

```bash
python scripts/md-to-html.py \
  --no-editor \
  --plantuml-server https://plantuml.internal/plantuml/svg/ \
  plans/{slug}-{date}/03_modules/{module_slug}/srs.md
```

Packaged HTML keeps Mermaid diagrams visualized in-browser, always prefers local PlantUML rendering, can auto-install PlantUML locally when requested, and falls back to a configured server only when local rendering is unavailable. Wireframe images or links inserted into the markdown source are preserved only when those asset paths stay inside the allowed base directory.

## 8. Know Where To Look

- Runtime instructions for Codex: [AGENTS.md](../AGENTS.md)
- Claude-oriented project instructions: [CLAUDE.md](../CLAUDE.md)
- Codex-specific setup notes: [codex-setup.md](./codex-setup.md)
- Skill catalog: [skill-catalog.md](./skill-catalog.md)
- Methodology guide: [ba-methodology-guide.md](./ba-methodology-guide.md)
- Design runtime artifact details: [designs/README.md](../designs/README.md)

## 9. Practical Tips

- Start with `/ba-start` and let the skill guide you through the lifecycle
- Use subcommands when a later step must be rerun without redoing intake and FRD work
- Always provide raw input (file or text) when starting an engagement
- For UI scope, provide the project `DESIGN.md` direction explicitly, or let the skill ask for decisions and prepare mandatory ASCII in screen canon
- If you already have external mockups or links, plan to attach them manually into the final SRS after Step 9
- Use `--slug` for rerun commands whenever more than one project may exist
- Treat `/ba-start status` as the checkpoint view: it prints artifact dates, canon source counts, ASCII coverage, compile receipt state, and shared shell state
- Ask for assumptions and open questions before asking for finalization
- Use PlantUML for swimlanes; use Mermaid for sequence, data-flow, ERD, or simpler process views
- Use `/ba-notion` when the deliverable needs to be published into Notion rather than only packaged as local HTML
