#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ACTIVE_AGY_HOMES=()
for dir in "${HOME}/.gemini/antigravity-cli" "${HOME}/.gemini/antigravity" "${HOME}/.gemini/antigravity-ide"; do
  if [[ -d "${dir}" ]]; then
    ACTIVE_AGY_HOMES+=("${dir}")
  fi
done
if [[ ${#ACTIVE_AGY_HOMES[@]} -eq 0 ]]; then
  ACTIVE_AGY_HOMES+=("${HOME}/.gemini/antigravity")
fi

PRIMARY_HOME="${ACTIVE_AGY_HOMES[0]}"

TARGET_HOME="${PRIMARY_HOME}"
KI_BASE="${TARGET_HOME}/knowledge"
BA_KIT_KI="${KI_BASE}/ba-kit-workflow"
GUARDRAIL_TARGET="${TARGET_HOME}/ba-kit"
GUARDRAIL_SCRIPT_TARGET="${GUARDRAIL_TARGET}/scripts"
GUARDRAIL_DOC_TARGET="${GUARDRAIL_TARGET}/docs"
LOCAL_BIN_TARGET="${HOME}/.local/bin"
STATE_TARGET="${HOME}/.local/share/ba-kit/installations"

GUARDRAIL_SCRIPTS=()

ensure_dir() {
  mkdir -p "$1"
}

load_guardrail_scripts() {
  local runtime="$1" line
  GUARDRAIL_SCRIPTS=()
  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "${line}" || "${line}" == \#* ]] && continue
    if [[ "${line}" =~ ^\[([a-z]+)\][[:space:]]+(.+)$ ]]; then
      [[ "${BASH_REMATCH[1]}" == "${runtime}" ]] && GUARDRAIL_SCRIPTS+=("${BASH_REMATCH[2]}")
    else
      GUARDRAIL_SCRIPTS+=("${line}")
    fi
  done < "${ROOT_DIR}/scripts/guardrail-scripts-list.txt"
}

install_core_assets() {
  # Core files for scripts (REPO_ROOT = ~/.claude/ba-kit/)
  local target_ba_kit="${TARGET_HOME}/ba-kit"
  ensure_dir "${target_ba_kit}/core/behavior"
  cp "${ROOT_DIR}/core/contract.yaml" "${target_ba_kit}/core/contract.yaml"
  cp "${ROOT_DIR}/core/contract-behavior.md" "${target_ba_kit}/core/contract-behavior.md"
  cp "${ROOT_DIR}/core/behavior/"*.md "${target_ba_kit}/core/behavior/"
  ensure_dir "${target_ba_kit}/templates"
  cp -r "${ROOT_DIR}/templates/"* "${target_ba_kit}/templates/"
  ensure_dir "${target_ba_kit}/skills"
  cp -r "${ROOT_DIR}/skills/"* "${target_ba_kit}/skills/"
  # Also for load_contract() home-first check
  ensure_dir "${TARGET_HOME}/core"
  cp "${ROOT_DIR}/core/contract.yaml" "${TARGET_HOME}/core/contract.yaml"
}

install_cli() {
  local temp_target
  mkdir -p "${LOCAL_BIN_TARGET}"
  temp_target="$(mktemp "${LOCAL_BIN_TARGET}/ba-kit.tmp.XXXXXX")"
  cp "${ROOT_DIR}/scripts/ba-kit" "${temp_target}"
  chmod +x "${temp_target}"
  mv "${temp_target}" "${LOCAL_BIN_TARGET}/ba-kit"
}

install_guardrail_assets() {
  local target_home="$1"
  local guardrail_target="${target_home}/ba-kit"
  local guardrail_script_target="${guardrail_target}/scripts"
  local guardrail_doc_target="${guardrail_target}/docs"
  local script_name

  mkdir -p "${guardrail_script_target}" "${guardrail_doc_target}"
  for script_name in "${GUARDRAIL_SCRIPTS[@]}"; do
    if [[ ! -f "${ROOT_DIR}/scripts/${script_name}" ]]; then
      echo "Guardrail script missing: ${ROOT_DIR}/scripts/${script_name}" >&2
      exit 1
    fi
    cp "${ROOT_DIR}/scripts/${script_name}" "${guardrail_script_target}/${script_name}"
  done

  cp "${ROOT_DIR}/docs/runtime-hard-guardrails.md" "${guardrail_doc_target}/runtime-hard-guardrails.md"
  if [[ -f "${ROOT_DIR}/core/token-budget.md" ]]; then
    cp "${ROOT_DIR}/core/token-budget.md" "${guardrail_doc_target}/token-budget.md"
  fi
}

write_manifest() {
  mkdir -p "${STATE_TARGET}"
  cat > "${STATE_TARGET}/antigravity.env" <<EOF
BA_KIT_RUNTIME=antigravity
BA_KIT_SOURCE_REPO=${ROOT_DIR}
BA_KIT_INSTALLED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BA_KIT_INSTALLER=scripts/install-antigravity-ba-kit.sh
BA_KIT_GUARDRAIL_ROOT=${GUARDRAIL_TARGET}
BA_KIT_GUARDRAIL_PREFLIGHT=${GUARDRAIL_SCRIPT_TARGET}/guardrail-preflight.py
BA_KIT_GUARDRAIL_EXCERPTS=${GUARDRAIL_SCRIPT_TARGET}/guardrail-build-excerpts.py
BA_KIT_GUARDRAIL_AUDIT=${GUARDRAIL_SCRIPT_TARGET}/guardrail-audit.py
BA_KIT_INDEX_VALIDATOR=${GUARDRAIL_SCRIPT_TARGET}/validate-index-quality.py
BA_KIT_CHECK_TOKEN_BUDGET=${GUARDRAIL_SCRIPT_TARGET}/check-token-budget.py
BA_KIT_CHECK_WRITE_SCOPE=${GUARDRAIL_SCRIPT_TARGET}/check-write-scope.py
BA_KIT_GUARDRAIL_DOC=${GUARDRAIL_DOC_TARGET}/runtime-hard-guardrails.md
EOF
}

create_ki_metadata() {
  local ki_dir="$1"
  local summary="$2"
  local title="$3"
  ensure_dir "${ki_dir}"
  cat > "${ki_dir}/metadata.json" <<EOF
{
  "title": "${title}",
  "summary": "${summary}",
  "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "references": [
    {
      "type": "file",
      "path": "${ROOT_DIR}/GEMINI.md"
    },
    {
      "type": "file",
      "path": "${ROOT_DIR}/core/contract-behavior.md"
    },
    {
      "type": "file",
      "path": "${ROOT_DIR}/skills/ba-start/SKILL.md"
    }
  ]
}
EOF
}

create_workflow_ki() {
  local target_home="$1"
  local ki_base="${target_home}/knowledge"
  local ba_kit_ki="${ki_base}/ba-kit-workflow"
  local artifacts_dir="${ba_kit_ki}/artifacts"
  rm -rf "${ba_kit_ki}"
  ensure_dir "${artifacts_dir}"

  create_ki_metadata "${ba_kit_ki}" \
    "BA-kit workflow reference for Antigravity. Covers BA-friendly resume prompts, PROJECT-HOME.md usage, lifecycle routing, agent roles, template mapping, and artifact conventions." \
    "BA-kit Workflow Reference"

  cat > "${artifacts_dir}/workflow-reference.md" <<'KIEOF'
# BA-kit Workflow Reference For Antigravity

> Use this KI to understand the BA-kit lifecycle when working inside Antigravity.

## BA Lifecycle

1. Accept input → Parse into intake form
2. Create or refresh PROJECT-HOME.md as the BA-facing dashboard
3. Gap analysis → Clarifying questions
4. Scope lock → Select mode (lite/hybrid/formal)
5. Build requirements backbone (source of truth)
6. Emit downstream artifacts only when gates are open:
   - FRD, user stories, canon-first SRS, mandatory ASCII screen wireframes
7. Final screen descriptions compiled from screen canon ASCII
9. Quality review and HTML packaging

## BA-Friendly Entrypoints

Prefer natural Vietnamese intent first, then map to the internal workflow:

| BA says | Internal workflow |
|---------|-------------------|
| "Tạo dự án mới từ tài liệu này" | intake/full lifecycle |
| "Tiếp tục dự án này" | read PROJECT-HOME.md, then ba-next |
| "Tôi nên làm gì tiếp?" | ba-next |
| "Đánh giá thay đổi này" | impact |
| "Chuẩn bị ASCII wireframe" | ba-start srs |
| "Đồng bộ Figma cho module X" | ba-figma-sync downstream visual sync |
| "Xuất gói bàn giao" | package |
| "Kiểm tra trạng thái" | status |
| "Tôi nhận module X" | ba-collab claim |
| "Gửi module X cho Lead BA review" | ba-collab review packet |
| "Tạo PR cho module X" | ba-collab GitHub handoff; approval required |

PROJECT-HOME.md is a dashboard only. Use it to orient the user, but verify the contract artifacts before mutating anything.
COLLAB-HOME.md and MODULE-HOME.md are BA-facing collaboration dashboards. GitHub commit/push/PR/merge requires explicit user approval.

## Prompt Patterns (Antigravity has no slash commands)

| Claude Code Command | Antigravity Prompt Equivalent |
|---------------------|-------------------------------|
| `/ba-start` | "Read skills/ba-start/SKILL.md and run the full BA workflow" |
| `/ba-start intake <file>` | "Read skills/ba-start/SKILL.md and run intake for <file>" |
| `/ba-start backbone --slug X` | "Read skills/ba-start/SKILL.md and run backbone for slug X" |
| `/ba-start frd --slug X --module Y` | "Read skills/ba-start/SKILL.md and run frd for slug X module Y" |
| `/ba-start stories --slug X --module Y` | "Read skills/ba-start/SKILL.md and run stories for slug X module Y" |
| `/ba-start srs --slug X --module Y` | "Read skills/ba-start/SKILL.md and run srs for slug X module Y" |
| `/ba-figma-sync --slug X --module Y` | "Read skills/ba-figma-sync/SKILL.md and sync Figma for slug X module Y" |
| `/ba-start package --slug X` | "Read skills/ba-start/SKILL.md and run package for slug X" |
| `/ba-start status --slug X` | "Read skills/ba-start/SKILL.md and run status for slug X" |
| `/ba-start impact --slug X` | "Read skills/ba-start/SKILL.md and run impact for slug X" |
| `/ba-do <description>` | "Read skills/ba-do/SKILL.md and route: <description>" |
| `/ba-next --slug X` | "Read skills/ba-next/SKILL.md and inspect slug X" |
| `/ba-collab <description>` | "Read skills/ba-collab/SKILL.md and run collaboration workflow: <description>" |

## Agent Roles (reference only — no auto-delegation in Antigravity)

| Agent | Focus | Agent File |
|-------|-------|------------|
| requirements-engineer | Backbone, FRD, stories, SRS content | agents/requirements-engineer.md |
| ui-ux-designer | Wireframe constraints and handoff checklist | agents/ui-ux-designer.md |
| ba-documentation-manager | Quality, packaging, consistency | agents/ba-documentation-manager.md |
| ba-researcher | Domain research | agents/ba-researcher.md |

## Key Templates

| Artifact | Template |
|----------|----------|
| Intake form | templates/intake-form-template.md |
| Project Home / BA dashboard | templates/project-home-template.md |
| Collab Home / BA collaboration dashboard | templates/collab-home-template.md |
| Module Home | templates/module-home-template.md |
| Module review packet | templates/review-packet-template.md |
| Requirements backbone | templates/requirements-backbone-template.md |
| FRD | templates/frd-template.md |
| User stories | templates/user-story-template.md |
| SRS | templates/srs-template.md |
| Design system | templates/design-md-template.md |
| Project memory summary | templates/project-memory-template.md |
| Project memory index | templates/project-memory-index-template.md |
| Memory packet | templates/memory-packet-template.md |
| File-back record | templates/project-memory-fileback-record-template.md |

## Defaults

- Language: Vietnamese (unless English explicitly requested)
- Date token: YYMMDD-HHmm
- Mode: hybrid
- UI baseline: Shadcn UI (unless DESIGN.md overrides)
- Canonical contract: core/contract.yaml + core/contract-behavior.md
- Memory: compact `project-memory.md` by default; shard mode navigates via `project-memory/index.md` first
- Delegation: pass bounded packets, not full memory trees or merged artifacts

## Guardrail Enforcement

Before running guarded commands (FRD, stories, SRS, package), run:
  `ba-kit guardrail --command <cmd> --slug <s> --date <d> [--module <m>]`

If blocked: surface the block message and run the refresh command.
If ok: use ALLOW_READS paths for file discovery.

After writing artifacts, validate indexes:
  `ba-kit validate-index --index-key <key> --slug <s> --date <d> [--module <m>] --writeback`

Before packaging, check token budgets:
  `ba-kit check-token-budget`

Guardrail scripts are installed at `~/.gemini/antigravity/ba-kit/scripts/`.
KIEOF
}

echo "Installing BA-kit for Antigravity from: ${ROOT_DIR}"

for h in "${ACTIVE_AGY_HOMES[@]}"; do
  echo "Installing workflow reference KI and guardrails to ${h}..."
  ensure_dir "${h}"
  ensure_dir "${h}/knowledge"
  
  create_workflow_ki "${h}"
  load_guardrail_scripts "antigravity"
  install_guardrail_assets "${h}"
done

install_cli
write_manifest
install_core_assets

echo "Created BA-kit KI in active Antigravity runtimes"
echo "Installed guardrail assets (${#GUARDRAIL_SCRIPTS[@]} scripts + docs)"
echo "Installed core assets to core/ + templates/ + skills/"
echo "Installed update CLI to ${LOCAL_BIN_TARGET}/ba-kit"
echo "BA-kit Antigravity installation complete."
echo ""
echo "Antigravity reads GEMINI.md and AGENTS.md directly from the repo."
echo "Use prompt patterns like 'Read skills/ba-start/SKILL.md and run intake' to invoke BA workflows."
