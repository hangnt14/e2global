#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "${ROOT_DIR}" "${ROOT_DIR}/core/contract.yaml" "${ROOT_DIR}/templates/manifest.json" <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path

root_dir = Path(sys.argv[1])
readme = (root_dir / "README.md").read_text(encoding="utf-8")
getting_started = (root_dir / "docs/getting-started.md").read_text(encoding="utf-8")
codex_setup = (root_dir / "docs/codex-setup.md").read_text(encoding="utf-8")
skill_catalog = (root_dir / "docs/skill-catalog.md").read_text(encoding="utf-8")

def load_structured(path_str):
    path = Path(path_str)
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        ruby = subprocess.run(
            [
                "ruby",
                "-rjson",
                "-ryaml",
                "-e",
                "print JSON.generate(YAML.load_file(ARGV[0]))",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(ruby.stdout)

contract = load_structured(sys.argv[2])
manifest = load_structured(sys.argv[3])
source_skill = (root_dir / "skills/ba-start/SKILL.md").read_text(encoding="utf-8")
options_step = root_dir / "skills/ba-start/steps/options.md"
behavior = (root_dir / "core/contract-behavior.md").read_text(encoding="utf-8")
do_workflow = (root_dir / "core/workflows/do.md").read_text(encoding="utf-8")
next_workflow = (root_dir / "core/workflows/next.md").read_text(encoding="utf-8")
backbone_step = (root_dir / "skills/ba-start/steps/backbone.md").read_text(encoding="utf-8")
intake_step = (root_dir / "skills/ba-start/steps/intake.md").read_text(encoding="utf-8")
project_home = (root_dir / "templates/project-home-template.md").read_text(encoding="utf-8")
generator = (root_dir / "scripts/generate-codex-assets.sh").read_text(encoding="utf-8")
codex_skill = (root_dir / "codex/skills/ba-start/SKILL.md").read_text(encoding="utf-8")

def fail(message):
    raise SystemExit(message)

def normalize(text):
    return " ".join(text.split()).lower()

def require_tokens(text, tokens, message):
    normalized = normalize(text)
    missing = [token for token in tokens if normalize(token) not in normalized]
    if missing:
        fail(f"{message}: missing {missing}")

def require_regex(text, pattern, message):
    if not re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL):
        fail(message)

def extract_section(text, heading):
    pattern = rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        fail(f"Missing section: {heading}")
    return match.group(1)

def require_in_order(text, snippets, message):
    cursor = 0
    for snippet in snippets:
        idx = text.find(snippet, cursor)
        if idx == -1:
            fail(f"{message}: missing ordered snippet {snippet!r}")
        cursor = idx + len(snippet)

if "options" not in contract["commands"]:
    fail("Missing commands.options")
if contract["commands"]["options"]["requires"] != ["intake"]:
    fail("options must require intake")
if "options" not in contract["next_step_order"]:
    fail("options missing from next_step_order")
if not (
    contract["next_step_order"].index("intake")
    < contract["next_step_order"].index("options")
    < contract["next_step_order"].index("backbone")
):
    fail("options must sit between intake and backbone")

paths = contract["paths"]
for key in ("options_root", "options_index", "option_item", "options_comparison"):
    if key not in paths:
        fail(f"Missing contract path: {key}")

for template_name in (
    "options-index-template.md",
    "solution-option-template.md",
    "options-comparison-template.md",
):
    if template_name not in manifest:
        fail(f"Missing template manifest entry: {template_name}")

if "/ba-start options --slug <slug>" not in source_skill:
    fail("Missing ba-start options invocation in source skill")
if "| `options` | `steps/options.md` |" not in source_skill:
    fail("Missing ba-start options dispatch row in source skill")
if not options_step.exists():
    fail("Missing ba-start options step")
step_body = options_step.read_text(encoding="utf-8")
if "`impact` -> `impact.md`" not in generator or "`options` -> `options.md`" not in generator:
    fail("Codex asset generator missing options step mapping")
if "`impact` -> `impact.md`" not in codex_skill or "`options` -> `options.md`" not in codex_skill:
    fail("Generated Codex ba-start asset missing options step mapping")

options_index_template = (root_dir / "templates/options-index-template.md").read_text(encoding="utf-8")
solution_option_template = (root_dir / "templates/solution-option-template.md").read_text(encoding="utf-8")
options_comparison_template = (root_dir / "templates/options-comparison-template.md").read_text(encoding="utf-8")

status_tokens = [
    "recommended",
    "in-progress",
    "completed",
    "skipped",
    "not-needed",
]

lifecycle_section = extract_section(behavior, "Canonical Lifecycle Status Mapping")
require_tokens(
    lifecycle_section,
    status_tokens + ["todo", "doing", "done"],
    "contract-behavior lifecycle mapping regressed",
)

options_gate_section = extract_section(behavior, "Options Decision-Ledger Gate")
require_tokens(
    options_gate_section,
    status_tokens
    + [
        "paths.options_root",
        "paths.plan",
        "recommend",
        "strongly recommend",
        "selected option",
        "backbone",
        "options",
    ],
    "contract-behavior options gate guidance regressed",
)
if "plan.md" in options_gate_section:
    fail("Options gate guidance should reference `paths.plan`, not hardcoded plan.md")

require_tokens(
    readme,
    [
        "/ba-start options --slug warehouse-rfp",
        "/ba-start options --slug warehouse-rfp --select option-02",
        "/ba-start options --slug warehouse-rfp --skip",
        "01_intake/options/*",
    ],
    "README must document the options command surface and artifacts",
)
require_tokens(
    getting_started,
    [
        "/ba-start options --slug warehouse-rfp",
        "/ba-start options --slug warehouse-rfp --select option-02",
        "/ba-start options --slug warehouse-rfp --skip",
        "plans/{slug}-{date}/01_intake/options/",
        "/ba-start frd --slug warehouse-rfp --module auth-flow",
        "/ba-start stories --slug warehouse-rfp --module auth-flow",
        "/ba-start srs --slug warehouse-rfp --module auth-flow",
        "plans/{slug}-{date}/01_intake/plan.md",
    ],
    "Getting started must document options commands and artifacts",
)
require_tokens(
    codex_setup,
    [
        "/ba-start options --slug warehouse-rfp",
        "/ba-start options --slug warehouse-rfp --select option-02",
        "/ba-start options --slug warehouse-rfp --skip",
        "plans/{slug}-{date}/01_intake/options/",
        "plans/{slug}-{date}/01_intake/plan.md",
    ],
    "Codex setup must mention the options flow command surface and artifacts",
)
require_tokens(
    skill_catalog,
    [
        "option pack + comparison",
        "/ba-start options --slug <slug>",
        "/ba-start options --slug <slug> --select option-02",
        "/ba-start options --slug <slug> --skip",
        "/ba-start frd --slug <slug> --module <module_slug>",
        "/ba-start stories --slug <slug> --module <module_slug>",
        "/ba-start srs --slug <slug> --module <module_slug>",
        "/ba-figma-sync --slug <slug> --module <module_slug>",
        "| `options` |",
        "| `ba-figma-sync` | Sync approved SRS screen canon to Figma through Figma MCP and write sync/mismatch reports |",
        "| `srs` | Produce folder-based SRS sources, use cases, mandatory ASCII screens, routing indexes, and compiled `srs.md` |",
    ],
    "Skill catalog must document options deliverables and explicit command surface",
)
for path_label, doc_text in (
    ("docs/getting-started.md", getting_started),
    ("docs/codex-setup.md", codex_setup),
    ("docs/skill-catalog.md", skill_catalog),
):
    if re.search(r"plans/\{date\}-\{slug\}", doc_text):
        fail(f"{path_label} must use canonical plans/{{slug}}-{{date}} paths")

require_tokens(
    source_skill,
    [
        "argument-hint: \"[intake|impact|options|backbone|frd|stories|srs|package|status|next] [file|--slug|--date|--module|--mode|--select|--skip]\"",
        "/ba-start options --slug <slug>",
        "/ba-start options --slug <slug> --select option-02",
        "/ba-start options --slug <slug> --skip",
        "/ba-start next --slug <slug>",
    ],
    "ba-start options invocation examples regressed",
)

require_tokens(
    step_body,
    [
        "## Prerequisites",
        "Resolve slug and date using the shared contract",
        "Require `paths.intake`",
        "Read `paths.plan` when it exists",
        "## Supported Intents",
        "generate option pack from intake",
        "select an existing option",
        "skip optioning explicitly",
        "## Generation Rules",
        "Generate 1-3 option artifacts only",
        "options status: in-progress",
        "Mark each option with `L1`, `L2`, or `L3`",
        "Generate `comparison.md` only when more than one viable option exists",
        "Keep options as solution briefs, not mini-backbones",
        "## Selection / Skip Rules",
        "--select option-02",
        "selected option",
        "options status: completed",
        "--skip",
        "options status: skipped",
        "refresh `paths.project_home`",
    ],
    "options step contract regressed",
)

require_regex(
    behavior,
    r"For `options`, allow `--select <option-id>` and `--skip` as mutually exclusive control arguments\.",
    "contract-behavior must define options control arguments",
)
require_regex(
    behavior,
    r"Stop when:\s*-\s*the requested option file does not exist\s*-\s*multiple options exist but no explicit selection/skip has been approved\s*-\s*a selection request names an unknown option id",
    "contract-behavior must define exact options stop conditions",
)

generation_section = extract_section(step_body, "Generation Rules")
require_regex(
    generation_section,
    r"Generate or open the option cycle[^\n]*`paths\.plan`[^\n]*`options status: in-progress`",
    "options step must tie generation/opening the option cycle to `paths.plan` and `in-progress`",
)
selection_skip_section = extract_section(step_body, "Selection / Skip Rules")
require_regex(
    selection_skip_section,
    r"`--select option-02`[^\n]*`selected option`[^\n]*`paths\.plan`[^\n]*`options status: completed`",
    "options step must tie selection to both `selected option` and `completed` in `paths.plan`",
)
require_regex(
    selection_skip_section,
    r"`--skip`[^\n]*`paths\.plan`[^\n]*`options status: skipped`",
    "options step must tie skip to `paths.plan` and `skipped`",
)
require_regex(
    options_gate_section,
    r"move the lifecycle to `in-progress`",
    "contract-behavior must require the options cycle to move to `in-progress`",
)
require_regex(
    options_gate_section,
    r"`completed` once `selected option` is recorded",
    "contract-behavior must tie `completed` to recorded `selected option`",
)
require_regex(
    options_gate_section,
    r"`backbone` may proceed only when the ledger records `not-needed`, `selected option` \(`completed`\), or `skipped`",
    "contract-behavior must tie the backbone proceed rule to `not-needed`, `selected option`, or `skipped`",
)

require_tokens(
    options_index_template,
    [
        "Trạng thái optioning",
        "Trạng thái từng option",
        "Difference Level",
        "draft/reviewing/selected/rejected/skipped",
        "lifecycle cấp dự án",
        "trạng thái của từng phương án",
        "Recommended option:",
        "Selected option:",
        "Comparison file:",
    ],
    "options index template regressed",
)
require_tokens(
    solution_option_template,
    [
        "## 1. Option Summary",
        "## 2. Business Intent",
        "## 3. Scope Shape",
        "## 4. Interaction View",
        "## 5. Key Constraints And Gaps",
        "## 6. Pros And Cons",
        "## 7. Indicative Assessment",
    ],
    "solution option template regressed",
)
require_tokens(
    options_comparison_template,
    [
        "Difference Level",
        "Time-to-Clarity",
        "Recommended When",
    ],
    "options comparison template regressed",
)

intake_gate_section = extract_section(intake_step, "Step 4.1 - Recommend direct backbone or optioning")
require_tokens(
    intake_gate_section,
    status_tokens + ["paths.plan", "decision ledger", "backbone", "options", "strongly recommend"],
    "intake recommendation gate contract regressed",
)
require_regex(
    intake_gate_section,
    r"direct[^\n`]*`backbone`|`backbone`[^\n]*direct",
    "intake must preserve the direct-to-backbone path",
)
require_regex(
    intake_gate_section,
    r"recommend[^\n`]*`options`|`options`[^\n]*recommend",
    "intake must preserve the recommend-options path",
)
require_regex(
    intake_gate_section,
    r"options status[^\n]*`not-needed`[^\n]*`recommended`",
    "intake must seed options status with `not-needed` or `recommended`",
)
require_regex(
    intake_gate_section,
    r"expected next command[^\n]*`backbone`[^\n]*`options`",
    "intake must map the expected next command to `backbone` or `options`",
)

if "Todo / Doing / Done" in project_home or "Not needed / Todo / Doing / Done" in project_home:
    fail("Project Home still uses legacy Todo/Doing/Done lifecycle labels")

require_tokens(
    project_home,
    status_tokens + ["Trạng thái lifecycle chuẩn", "Decision ledger", "optioning status"],
    "Project Home options lifecycle guidance regressed",
)
require_regex(
    project_home,
    r"^\|\s*Phương án giải pháp\s*\|\s*\[recommended \| in-progress \| completed \| skipped \| not-needed\]\s*\|",
    "Project Home must keep the solution-option lifecycle row",
)
require_regex(
    project_home,
    r"`01_intake/plan\.md`[^\n]*Decision ledger",
    "Project Home must describe `01_intake/plan.md` as the decision ledger",
)

require_regex(
    do_workflow,
    r"\|\s*asking to brainstorm solution options, create multiple solution directions, compare solution approaches, choose an option, or skip optioning\s*\|\s*`ba-start options`\s*\|",
    "ba-do must route optioning intent via `ba-start options`",
)
require_regex(
    do_workflow,
    r"\|\s*syncing approved screen canon to Figma, creating Figma frames, updating Figma wireframes, or \"đồng bộ Figma\"\s*\|\s*`ba-figma-sync`\s*\|",
    "ba-do must route Figma sync intent via `ba-figma-sync`",
)
require_in_order(
    do_workflow,
    [
        "asking to brainstorm solution options, create multiple solution directions, compare solution approaches, choose an option, or skip optioning",
        "directly generating or rerunning intake/options/backbone/frd/stories/srs/package",
    ],
    "ba-do must prioritize optioning intent above the generic direct-step route",
)
require_tokens(
    next_workflow,
    [
        "when the next exact command would be module-scoped (`frd`, `stories`, or `srs`),",
        "if multiple module directories exist, stop and ask instead of emitting an incomplete module-scoped command",
        "plan",
        "options index",
        "option files",
        "comparison file",
        "ba-start options --slug <slug>",
        "recommended",
        "in-progress",
        "skipped",
        "completed",
        "not-needed",
        "selected option",
        "ba-start backbone --slug <slug>",
        "ba-start status --slug <slug>",
        "ba-start frd --slug <slug> --module <module_slug>",
        "ba-start stories --slug <slug> --module <module_slug>",
        "ba-start srs --slug <slug> --module <module_slug>",
    ],
    "ba-next options inspection or recommendation regressed",
)
require_regex(
    do_workflow,
    r"directly generating or rerunning intake/options/backbone/frd/stories/srs/package",
    "ba-do generic direct-step route must include options",
)
require_regex(
    next_workflow,
    r"intake exists and `paths\.plan` says options are `recommended` or `in-progress` -> `ba-start options --slug <slug>`",
    "ba-next must recommend `ba-start options --slug <slug>` when optioning is recommended or in-progress",
)
require_regex(
    next_workflow,
    r"intake exists and `paths\.plan` is missing, invalid, or says `completed` without `selected option` -> `ba-start status --slug <slug>`",
    "ba-next must fail closed when the options decision ledger is missing or invalid",
)
require_regex(
    next_workflow,
    r"intake exists, `paths\.plan` says options are `not-needed`, and no backbone -> `ba-start backbone --slug <slug>`",
    "ba-next must preserve the direct-to-backbone path when optioning is not needed",
)
require_regex(
    next_workflow,
    r"intake exists, `paths\.plan` says options are `skipped`, or `completed` with `selected option` recorded in `paths\.plan`, and no backbone -> `ba-start backbone --slug <slug>`",
    "ba-next must gate backbone on resolved optioning with an explicit selected option for completed status",
)
require_tokens(
    backbone_step,
    [
        "Always verify write authority for the target artifact and its owning memory shard",
        "For first-pass creation (when `paths.backbone` does not yet exist), skip only the impact-receipt requirement",
        "For reruns (artifact already exists): locate the active impact receipt at `paths.impact_receipt`",
        "**Must read when it exists:** `paths.plan`",
        "read `paths.plan` when it exists",
        "when `paths.plan` records `options status: recommended` or `options status: in-progress`, stop because optioning is unresolved",
        "when `paths.plan` records `options status: completed` or `options status: skipped`, treat that as the backbone decision gate",
        "require `paths.plan` to state either `options status: skipped`, `options status: completed`, or `options status: not-needed` before proceeding",
        "if completed, require a `selected option`",
        "read only the selected option file as the decision overlay",
        "never require `paths.options_root` to exist before honoring the decision-ledger gate",
        "promote only the selected option's portal/module/actor/constraint decisions",
        "do not import rejected options or the full comparison into `backbone.md`",
    ],
    "backbone options fail-closed gating regressed",
)
require_tokens(
    behavior,
    [
        "Treat `paths.plan` as the execution decision ledger whenever intake seeds an `options status`, whether or not `paths.options_root` has been created yet.",
        "`paths.options_root` is evidence that option artifacts exist; it must not be used as the condition that turns backbone gating on or off.",
        "| backbone | contract.yaml, contract-behavior.md, paths.intake, paths.plan (when exists) | selected option file only when optioning is `completed`; paths.project_memory, paths.memory_index (nav only), paths.memory_hot_vocabulary, paths.memory_hot_decisions | log.md, cold/, warm/ |",
        "Exception: skip the impact requirement for first-pass `backbone` creation when `paths.backbone` does not yet exist, and for explicitly approved `wording-only` reruns.",
    ],
    "contract-behavior must keep backbone read scope and governance aligned with the options decision gate",
)
PY
