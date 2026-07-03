#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

find_python3() {
  for candidate in python3 python py; do
    if command -v "${candidate}" >/dev/null 2>&1 \
       && "${candidate}" -c "import sys; assert sys.version_info >= (3,6)" >/dev/null 2>&1; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

PYTHON3="$(find_python3)" || {
  echo "ERROR: Python 3.6+ is required but not found. Install from https://python.org" >&2
  echo "  On Windows: disable App Execution Aliases for Python in Settings > Apps > Advanced app settings" >&2
  exit 1
}

# Ensure python3 always resolves to a real interpreter — on Windows Git Bash
# it may point to a non-functional Microsoft Store stub. Creates ~/bin/python3
# wrapper if needed. macOS/Linux users get a no-op since python3 is standard.
bootstrap_python3() {
  if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
    return 0
  fi
  mkdir -p "${HOME}/bin"
  cat > "${HOME}/bin/python3" <<'WRAPEOF'
#!/usr/bin/env bash
exec "${_PYTHON_REAL}" "$@"
WRAPEOF
  sed -i "s|\${_PYTHON_REAL}|${PYTHON3}|g" "${HOME}/bin/python3"
  chmod +x "${HOME}/bin/python3"
  if ! "${HOME}/bin/python3" --version >/dev/null 2>&1; then
    rm -f "${HOME}/bin/python3"
    echo "WARNING: python3 bootstrap failed." >&2
    return 1
  fi
  echo "Bootstrap: created python3 → ${PYTHON3}"
}
bootstrap_python3

SOURCE_ROOT="${BA_KIT_CODEX_SOURCE_ROOT:-${ROOT_DIR}/codex}"
SOURCE_SKILLS="${SOURCE_ROOT}/skills"
SOURCE_AGENTS="${SOURCE_ROOT}/agents"
SOURCE_TEMPLATES="${ROOT_DIR}/templates"
CORE_SOURCE="${BA_KIT_CORE_SOURCE_ROOT:-${ROOT_DIR}/core}"
CANONICAL_STEP_SOURCE="${ROOT_DIR}/skills/ba-start/steps"
TARGET_HOME="${HOME}/.codex"
TARGET_SKILLS="${TARGET_HOME}/skills"
TARGET_AGENTS="${TARGET_HOME}/agents"
TARGET_TEMPLATES="${TARGET_HOME}/templates"
CORE_TARGET="${TARGET_HOME}/ba-kit"
GUARDRAIL_SCRIPT_TARGET="${CORE_TARGET}/scripts"
GUARDRAIL_DOC_TARGET="${CORE_TARGET}/docs"
HOOK_TARGET="${CORE_TARGET}/hooks"
TARGET_CONFIG="${TARGET_HOME}/config.toml"
HOOKS_FILE="${TARGET_HOME}/hooks.json"
LOCAL_BIN_TARGET="${HOME}/.local/bin"
STATE_TARGET="${HOME}/.local/share/ba-kit/installations"
GUARDRAIL_SCRIPTS=()
STALE_TEMPLATE_FILES=(
  "wireframe-input-template.md"
  "wireframe-map-template.md"
)
STALE_CORE_PATHS=(
  "references"
)
MANAGED_SKILL_DIRS=(
  "ba-*"
  "brainstorm"
  "reverse-web"
  "qc-uc-review"
)

cleanup_managed_skill_dirs() {
  local pattern path

  mkdir -p "${TARGET_SKILLS}"
  shopt -s nullglob
  for pattern in "${MANAGED_SKILL_DIRS[@]}"; do
    for path in "${TARGET_SKILLS}"/${pattern}; do
      [[ -e "${path}" ]] || continue
      rm -rf "${path}"
    done
  done
  shopt -u nullglob
}

cleanup_managed_agent_files() {
  local agent_path

  mkdir -p "${TARGET_AGENTS}"
  shopt -s nullglob
  for agent_path in "${SOURCE_AGENTS}"/*; do
    [[ -f "${agent_path}" ]] || continue
    rm -f "${TARGET_AGENTS}/$(basename "${agent_path}")"
  done
  shopt -u nullglob
}

cleanup_managed_template_files() {
  local template_path

  mkdir -p "${TARGET_TEMPLATES}"
  shopt -s nullglob
  for template_path in "${SOURCE_TEMPLATES}"/*; do
    [[ -f "${template_path}" ]] || continue
    rm -f "${TARGET_TEMPLATES}/$(basename "${template_path}")"
  done
  shopt -u nullglob
}

cleanup_previous_install() {
  cleanup_managed_skill_dirs
  cleanup_managed_agent_files
  cleanup_managed_template_files
  rm -rf "${CORE_TARGET}"
}

if [[ ! -d "${SOURCE_SKILLS}" ]] && [[ ! -d "${SOURCE_AGENTS}" ]]; then
  echo "BA-kit Codex conversion not found."
  echo "Expected converted assets under: ${SOURCE_ROOT}/skills and ${SOURCE_ROOT}/agents"
  echo "Set BA_KIT_CODEX_SOURCE_ROOT if your converted assets live elsewhere."
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node is required but not found in PATH" >&2
  exit 1
fi

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

install_cli() {
  local temp_target
  mkdir -p "${LOCAL_BIN_TARGET}"
  temp_target="$(mktemp "${LOCAL_BIN_TARGET}/ba-kit.tmp.XXXXXX")"
  cp "${ROOT_DIR}/scripts/ba-kit" "${temp_target}"
  chmod +x "${temp_target}"
  mv "${temp_target}" "${LOCAL_BIN_TARGET}/ba-kit"
}

generate_codex_assets() {
  if [[ ! -x "${ROOT_DIR}/scripts/generate-codex-assets.sh" ]]; then
    echo "Codex asset generator missing: ${ROOT_DIR}/scripts/generate-codex-assets.sh" >&2
    exit 1
  fi
  (cd "${ROOT_DIR}" && bash ./scripts/generate-codex-assets.sh)
}

copy_tree() {
  local source_dir="$1"
  local target_dir="$2"

  mkdir -p "$target_dir"
  cp -R "${source_dir}/." "$target_dir/"
}

write_manifest() {
  mkdir -p "${STATE_TARGET}"
  cat > "${STATE_TARGET}/codex.env" <<EOF
BA_KIT_RUNTIME=codex
BA_KIT_SOURCE_REPO=${ROOT_DIR}
BA_KIT_INSTALLED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BA_KIT_INSTALLER=scripts/install-codex-ba-kit.sh
BA_KIT_GUARDRAIL_ROOT=${CORE_TARGET}
BA_KIT_GUARDRAIL_PREFLIGHT=${GUARDRAIL_SCRIPT_TARGET}/guardrail-preflight.py
BA_KIT_GUARDRAIL_EXCERPTS=${GUARDRAIL_SCRIPT_TARGET}/guardrail-build-excerpts.py
BA_KIT_GUARDRAIL_AUDIT=${GUARDRAIL_SCRIPT_TARGET}/guardrail-audit.py
BA_KIT_INDEX_VALIDATOR=${GUARDRAIL_SCRIPT_TARGET}/validate-index-quality.py
BA_KIT_CHECK_TOKEN_BUDGET=${GUARDRAIL_SCRIPT_TARGET}/check-token-budget.py
BA_KIT_CHECK_WRITE_SCOPE=${GUARDRAIL_SCRIPT_TARGET}/check-write-scope.py
BA_KIT_CONTEXT_OUTPUT_GUARD=${GUARDRAIL_SCRIPT_TARGET}/context-output-guard.py
BA_KIT_CONTEXT_PREFLIGHT_GUARD=${GUARDRAIL_SCRIPT_TARGET}/context-preflight-guard.py
BA_KIT_HOOKS_DIR=${HOOK_TARGET}
BA_KIT_GUARDRAIL_DOC=${GUARDRAIL_DOC_TARGET}/runtime-hard-guardrails.md
EOF
}

install_guardrail_runtime_assets() {
  local script_name

  mkdir -p "${GUARDRAIL_SCRIPT_TARGET}" "${GUARDRAIL_DOC_TARGET}"
  for script_name in "${GUARDRAIL_SCRIPTS[@]}"; do
    if [[ ! -f "${ROOT_DIR}/scripts/${script_name}" ]]; then
      echo "Guardrail runtime script missing: ${ROOT_DIR}/scripts/${script_name}" >&2
      exit 1
    fi
    cp "${ROOT_DIR}/scripts/${script_name}" "${GUARDRAIL_SCRIPT_TARGET}/${script_name}"
  done

  cp "${ROOT_DIR}/docs/runtime-hard-guardrails.md" "${GUARDRAIL_DOC_TARGET}/runtime-hard-guardrails.md"
}

write_codex_hook_scripts() {
  mkdir -p "${HOOK_TARGET}" "${CORE_TARGET}/state"

  cat > "${HOOK_TARGET}/guardrail-preflight-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit guardrail preflight hook — UserPromptSubmit

set -euo pipefail

BA_KIT_HOOK_HOME="${HOME}/.codex/ba-kit"
BA_KIT_STATE_DIR="${BA_KIT_HOOK_HOME}/state"

detect_plan_dir() {
  local dir="${PWD}"
  while [[ "${dir}" != "/" ]]; do
    if [[ "${dir}" =~ /plans/[^/]+-[0-9]{6}-[0-9]{4}$ ]]; then
      printf '%s\n' "${dir}"
      return 0
    fi
    if [[ "${dir}" == "${HOME}" ]]; then
      break
    fi
    dir="$(dirname "${dir}")"
  done

  if [[ -n "${BA_KIT_HOME:-}" ]] && [[ -d "${BA_KIT_HOME}" ]]; then
    printf '%s\n' "${BA_KIT_HOME}"
    return 0
  fi

  return 1
}

extract_slug_date() {
  local plan_dir="$1"
  local dirname slug date_token
  dirname="$(basename "${plan_dir}")"
  slug="${dirname%-[0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]}"
  date_token="${dirname#${slug}-}"
  printf '%s\n%s\n' "${slug}" "${date_token}"
}

detect_command_from_prompt() {
  local prompt_text="$1"

  if echo "${prompt_text}" | grep -qiE '\bba-start\s+(frd|stories|srs|package|status|next)\b'; then
    echo "${prompt_text}" | grep -oiE '\bba-start\s+(frd|stories|srs|package|status|next)\b' \
      | head -1 | sed 's/ba-start //'
    return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(create|generate|produce|build|write)\b.*\b(FRD|functional requirements)\b'; then
    echo "frd"; return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(create|generate|produce|build|write)\b.*\b(user stories|stories)\b'; then
    echo "stories"; return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(create|generate|produce|build|write)\b.*\b(SRS|software requirements|spec)\b'; then
    echo "srs"; return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(package|bundle|handoff|deliver|ban giao|xuat goi)\b'; then
    echo "package"; return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(status|check|kiem tra)\b.*\b(progress|tien do)\b'; then
    echo "status"; return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(tiep tuc|tiep theo|next|continue|resume)\b'; then
    echo "next"; return 0
  fi

  return 1
}

detect_module() {
  local plan_dir="$1"
  local modules_dir="${plan_dir}/03_modules"
  if [[ ! -d "${modules_dir}" ]]; then
    return 0
  fi

  local module_from_prompt count single d
  module_from_prompt="$(echo "${PROMPT_TEXT:-}" | grep -oE -- '--module[[:space:]]+[^[:space:]]+' | awk '{print $2}' | head -1 || true)"
  if [[ -n "${module_from_prompt}" ]]; then
    printf '%s\n' "${module_from_prompt}"
    return 0
  fi

  count=0
  single=""
  for d in "${modules_dir}"/*/; do
    [[ -d "${d}" ]] || continue
    count=$((count + 1))
    single="$(basename "${d}")"
  done
  if [[ "${count}" -eq 1 ]]; then
    printf '%s\n' "${single}"
  fi
}

extract_prompt_text() {
  local stdin_data
  stdin_data="$(cat - 2>/dev/null || true)"
  if [[ -n "${1:-}" ]]; then
    printf '%s\n' "$1"
    return 0
  fi
  if [[ -n "${CODEX_PROMPT:-}" ]]; then
    printf '%s\n' "${CODEX_PROMPT}"
    return 0
  fi
  if [[ -n "${stdin_data}" ]]; then
    python3 - "${stdin_data}" <<'PYEOF' 2>/dev/null || printf '%s\n' "${stdin_data}"
import json, sys
raw = sys.argv[1]
try:
    data = json.loads(raw)
except Exception:
    print(raw)
else:
    print(data.get("prompt") or data.get("user_prompt") or data.get("message") or raw)
PYEOF
  fi
}

PLAN_DIR="$(detect_plan_dir)" || exit 0
PROMPT_TEXT="$(extract_prompt_text "${1:-}")"
COMMAND="$(detect_command_from_prompt "${PROMPT_TEXT}")" || exit 0

case "${COMMAND}" in
  frd|stories|srs|package|status|next) ;;
  *) exit 0 ;;
esac

SLUG_DATE=($(extract_slug_date "${PLAN_DIR}"))
SLUG="${SLUG_DATE[0]}"
DATE_TOKEN="${SLUG_DATE[1]}"
MODULE="$(detect_module "${PLAN_DIR}")"

SOURCE_REPO=""
if [[ -f "${HOME}/.local/share/ba-kit/installations/codex.env" ]]; then
  SOURCE_REPO="$(grep '^BA_KIT_SOURCE_REPO=' "${HOME}/.local/share/ba-kit/installations/codex.env" | head -1 | cut -d= -f2-)"
fi
if [[ -z "${SOURCE_REPO}" ]]; then
  exit 0
fi

PREFLIGHT_ARGS=(--command "${COMMAND}" --slug "${SLUG}" --date "${DATE_TOKEN}" --repo "${SOURCE_REPO}")
if [[ -n "${MODULE:-}" ]]; then
  PREFLIGHT_ARGS+=(--module "${MODULE}")
fi

mkdir -p "${BA_KIT_STATE_DIR}"
PREFLIGHT_OUT="${BA_KIT_STATE_DIR}/last-preflight.json"
python3 "${BA_KIT_HOOK_HOME}/scripts/guardrail-preflight.py" "${PREFLIGHT_ARGS[@]}" --output "${PREFLIGHT_OUT}" >/dev/null 2>&1 || true

if [[ ! -f "${PREFLIGHT_OUT}" ]]; then
  exit 0
fi

python3 - "${PREFLIGHT_OUT}" <<'PYEOF'
import json, pathlib, sys

preflight = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
status = preflight.get("status", "")
command = preflight.get("command", "")
resolved_slug = preflight.get("resolved_slug", "")
message = preflight.get("message", "").strip()
indexes = preflight.get("indexes", {})
has_current = any(v.get("state") == "current" for v in indexes.values() if isinstance(v, dict))
action_guardrail = preflight.get("action_guardrail", {})
output_mode = "probe" if status == "block" else "delta" if has_current else "full"

lines = [
    "",
    "Guardrail preflight:",
    f"output_mode={output_mode}",
    f"status={status}",
    f"command={command}",
    f"resolved_slug={resolved_slug}",
    message,
]
if output_mode in ("delta", "full"):
    allow_reads = preflight.get("allow_reads", [])
    if allow_reads:
        lines.append("ALLOW_READS:")
        lines.extend(f"- {item}" for item in allow_reads)
    for idx_name, idx_val in indexes.items():
        if isinstance(idx_val, dict):
            lines.append(f"INDEX: {idx_name} state={idx_val.get('state', '')}")
    if action_guardrail.get("required"):
        lines.extend([
            "ACTION_GUARDRAIL:",
            f"- navigation_source={action_guardrail.get('navigation_source', '')}",
            f"- packet_scope={action_guardrail.get('packet_scope', '')}",
            f"- reason={action_guardrail.get('reason', '')}",
        ])
if output_mode == "full":
    deny_reads = preflight.get("deny_reads", [])
    if deny_reads:
        lines.append("DENY_READS:")
        lines.extend(f"- {item}" for item in deny_reads)
    canonical_state_summary = preflight.get("canonical_state_summary", "").strip()
    if canonical_state_summary:
        lines.extend(["CANONICAL_STATE:", f"- {canonical_state_summary}"])
    canonical_next = preflight.get("canonical_next_command", "").strip()
    if canonical_next:
        lines.extend(["CANONICAL_NEXT_COMMAND:", f"- {canonical_next}"])
    refresh_cmd = preflight.get("refresh_command", "").strip()
    if refresh_cmd and status == "block":
        lines.append(f"REFRESH_COMMAND: {refresh_cmd}")
lines.append(f"If a broader read is necessary, emit exactly: READ_ESCALATION: {command} read <path> due to <reason>.")
print("\n".join(lines))
PYEOF
HOOKEOF

  cat > "${HOOK_TARGET}/guardrail-audit-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit guardrail audit hook — Stop

set -euo pipefail

PREFLIGHT_PATH="${HOME}/.codex/ba-kit/state/last-preflight.json"
AUDIT_OUT="${HOME}/.codex/ba-kit/state/last-audit.json"
READS_MANIFEST="${HOME}/.codex/ba-kit/state/reads-manifest.json"

if [[ ! -f "${PREFLIGHT_PATH}" ]]; then
  exit 0
fi
if [[ ! -f "${READS_MANIFEST}" ]]; then
  rm -f "${PREFLIGHT_PATH}"
  exit 0
fi

python3 "${HOME}/.codex/ba-kit/scripts/guardrail-audit.py" \
  --preflight "${PREFLIGHT_PATH}" \
  --reads-manifest "${READS_MANIFEST}" \
  --output "${AUDIT_OUT}" >/dev/null 2>&1 || true

if [[ -f "${AUDIT_OUT}" ]]; then
  status="$(python3 -c "
import json, pathlib
d = json.loads(pathlib.Path('${AUDIT_OUT}').read_text())
print(d.get('status', ''))
" 2>/dev/null || echo "")"
  case "${status}" in
    fail) echo "GUARDRAIL_AUDIT_FAIL: read audit found violations" >&2 ;;
    warn) echo "GUARDRAIL_AUDIT_WARN: read audit found minor issues" >&2 ;;
    pass) echo "GUARDRAIL_AUDIT_PASS" >&2 ;;
  esac
fi

rm -f "${PREFLIGHT_PATH}" "${READS_MANIFEST}"
HOOKEOF

  cat > "${HOOK_TARGET}/guardrail-write-scope-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit write-scope enforcement hook — PreToolUse (matcher: Write|Edit)

set -euo pipefail

detect_plan_dir() {
  local dir="${PWD}"
  while [[ "${dir}" != "/" ]]; do
    if [[ "${dir}" =~ /plans/[^/]+-[0-9]{6}-[0-9]{4}$ ]]; then
      return 0
    fi
    if [[ "${dir}" == "${HOME}" ]]; then
      break
    fi
    dir="$(dirname "${dir}")"
  done
  [[ -n "${BA_KIT_HOME:-}" ]] && [[ -d "${BA_KIT_HOME}" ]]
}

detect_plan_dir >/dev/null 2>&1 || exit 0

TOOL_INPUT="${1:-}"
if [[ -z "${TOOL_INPUT}" ]]; then
  TOOL_INPUT="$(cat - 2>/dev/null || echo "")"
fi

TARGET_PATH="$(echo "${TOOL_INPUT}" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    tool_input = data.get('tool_input', data)
    print(tool_input.get('file_path', tool_input.get('path', tool_input.get('file', ''))))
except Exception:
    pass
" 2>/dev/null || echo "")"

if [[ -z "${TARGET_PATH}" ]]; then
  exit 0
fi

PREFLIGHT_PATH="${HOME}/.codex/ba-kit/state/last-preflight.json"
DETECTED_CMD=""
if [[ -f "${PREFLIGHT_PATH}" ]]; then
  DETECTED_CMD="$(python3 -c "
import json, pathlib
d = json.loads(pathlib.Path('${PREFLIGHT_PATH}').read_text())
print(d.get('command', ''))
" 2>/dev/null || echo "")"
fi
if [[ -z "${DETECTED_CMD}" ]]; then
  exit 0
fi

if "${HOME}/.local/bin/ba-kit" check-write-scope --command "${DETECTED_CMD}" "${TARGET_PATH}" 2>/dev/null; then
  exit 0
fi

echo "GUARDRAIL_BLOCK: write-scope violation — ${TARGET_PATH} not in allowed scope for ${DETECTED_CMD}" >&2
exit 1
HOOKEOF

  cat > "${HOOK_TARGET}/guardrail-context-preflight-guard-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit context preflight guard — PreToolUse (matcher: Read|Glob)

set -euo pipefail

BA_KIT_HOOK_HOME="${HOME}/.codex/ba-kit"
STATE_DIR="${BA_KIT_HOOK_HOME}/state"
mkdir -p "${STATE_DIR}"

# Resolve Python (python3 may be a non-functional Windows Store stub; 'python' is common on Windows)
_PY=""
for _c in python3 python; do
  if command -v "${_c}" >/dev/null 2>&1 && "${_c}" --version >/dev/null 2>&1; then
    _PY="${_c}"
    break
  fi
done
if [[ -z "${_PY}" ]]; then
  exit 0
fi

TOOL_DATA="$(cat - 2>/dev/null || echo "{}")"
if [[ -z "${TOOL_DATA}" ]] || [[ "${TOOL_DATA}" == "{}" ]]; then
  exit 0
fi
"${_PY}" "${BA_KIT_HOOK_HOME}/scripts/context-preflight-guard.py" <<< "${TOOL_DATA}" 2>/dev/null
PREFLIGHT_EXIT=$?
if [[ ${PREFLIGHT_EXIT} -eq 1 ]]; then
  exit 1
fi
exit 0
HOOKEOF

  cat > "${HOOK_TARGET}/guardrail-context-output-guard-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit context output guard — PostToolUse (matcher: Bash|Read|Grep|Glob)

set -euo pipefail

BA_KIT_HOOK_HOME="${HOME}/.codex/ba-kit"
STATE_DIR="${BA_KIT_HOOK_HOME}/state"
mkdir -p "${STATE_DIR}"
TOOL_DATA="$(cat - 2>/dev/null || echo "{}")"
if [[ -z "${TOOL_DATA}" ]] || [[ "${TOOL_DATA}" == "{}" ]]; then
  exit 0
fi
python3 "${BA_KIT_HOOK_HOME}/scripts/context-output-guard.py" <<< "${TOOL_DATA}" 2>/dev/null || true
HOOKEOF

  cat > "${HOOK_TARGET}/guardrail-context-audit-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit context audit hook — Stop

set -euo pipefail

STATE_DIR="${HOME}/.codex/ba-kit/state"
VIOLATIONS_FILE="${STATE_DIR}/context-violations.jsonl"
if [[ ! -f "${VIOLATIONS_FILE}" ]]; then
  exit 0
fi

python3 - "${VIOLATIONS_FILE}" <<'PYEOF'
import json, pathlib, sys

vf = pathlib.Path(sys.argv[1])
lines = [l for l in vf.read_text(encoding="utf-8").strip().split("\n") if l]
if not lines:
    sys.exit(0)
violations = []
for line in lines:
    try:
        violations.append(json.loads(line))
    except json.JSONDecodeError:
        pass
if not violations:
    sys.exit(0)

total_bytes = sum(v["size_bytes"] for v in violations)
total_est_tokens = sum(v["estimated_tokens"] for v in violations)
warn_count = sum(1 for v in violations if v["level"] == "warn")
crit_count = sum(1 for v in violations if v["level"] == "critical")
sorted_by_time = sorted(violations, key=lambda v: v.get("timestamp", ""))
cached_token_waste = 0
for i, v in enumerate(sorted_by_time):
    cached_token_waste += v["estimated_tokens"] * max(1, len(sorted_by_time) - i - 1)
carry_label = "estimated (fallback, single violation)" if len(violations) <= 1 else "carry proxy"
tool_counts = {}
for v in violations:
    tool_counts[v["tool_name"]] = tool_counts.get(v["tool_name"], 0) + 1
budget_path = vf.parent / "context-session-budget.txt"
session_budget_bytes = 0
if budget_path.exists():
    try:
        session_budget_bytes = int(budget_path.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        pass

print("\nCONTEXT_GUARD_AUDIT: CodeX session context waste report")
print(f"  Violations: {len(violations)} ({warn_count} warn, {crit_count} critical)")
print(f"  Raw output: {total_bytes / 1024:.1f}kB total ({total_est_tokens} tokens)")
print(f"  Est. cached waste: ~{cached_token_waste} tokens ({carry_label})")
print(f"  Session budget: {session_budget_bytes / 1024:.1f}kB total")
print(f"  By tool: {', '.join(f'{k}={v}' for k, v in sorted(tool_counts.items()))}")
print()
print("  Top 5 largest outputs:")
for i, v in enumerate(sorted(violations, key=lambda v: v["size_bytes"], reverse=True)[:5], 1):
    print(f"    {i}. {v['tool_name']}: {v['size_bytes'] / 1024:.1f}kB — {v['tool_input_summary'][:80]}")
print()
print("  Remediation:")
print("    - Use Glob not find. Use Read with offset+limit. Use Grep with head_limit.")
print("    - Read large files in sections (TOC first, then targeted ranges).")
print("    - Pipe Bash output through head/tail when uncertain.")
print()
PYEOF

rm -f "${VIOLATIONS_FILE}"
rm -f "${STATE_DIR}/context-reads-manifest.jsonl"
rm -f "${STATE_DIR}/context-session-budget.txt"
HOOKEOF

  chmod +x "${HOOK_TARGET}"/guardrail-*-hook.sh
  cp "${ROOT_DIR}/scripts/hooks/postwrite-guardrail.sh" "${HOOK_TARGET}/postwrite-guardrail.sh"
  chmod +x "${HOOK_TARGET}/postwrite-guardrail.sh"
}

register_codex_hooks() {
  mkdir -p "${TARGET_HOME}"
  if [[ ! -f "${HOOKS_FILE}" ]]; then
    echo '{"hooks":{}}' > "${HOOKS_FILE}"
  fi

  "${PYTHON3}" - "${HOOKS_FILE}" "${HOOK_TARGET}" <<'PYEOF'
import json, pathlib, sys

hooks_path = pathlib.Path(sys.argv[1])
hooks_dir = sys.argv[2]
cfg = json.loads(hooks_path.read_text(encoding="utf-8")) if hooks_path.exists() else {}
if not isinstance(cfg, dict):
    cfg = {}
hooks = cfg.setdefault("hooks", {})

ups = hooks.setdefault("UserPromptSubmit", [])
ups[:] = [h for h in ups if "guardrail-preflight-hook.sh" not in str(h)]
ups.append({
    "matcher": "",
    "hooks": [{"type": "command", "command": f"bash \"{hooks_dir}/guardrail-preflight-hook.sh\""}],
})

stop = hooks.setdefault("Stop", [])
stop[:] = [h for h in stop if "guardrail-audit-hook.sh" not in str(h) and "guardrail-context-audit-hook.sh" not in str(h)]
stop.append({"hooks": [{"type": "command", "command": f"bash \"{hooks_dir}/guardrail-audit-hook.sh\""}]})
stop.append({"hooks": [{"type": "command", "command": f"bash \"{hooks_dir}/guardrail-context-audit-hook.sh\""}]})

pre = hooks.setdefault("PreToolUse", [])
pre[:] = [h for h in pre if "guardrail-write-scope-hook.sh" not in str(h) and "guardrail-context-preflight-guard-hook.sh" not in str(h)]
pre.append({
    "matcher": "Write|Edit",
    "hooks": [{"type": "command", "command": f"bash \"{hooks_dir}/guardrail-write-scope-hook.sh\""}],
})
pre.append({
    "matcher": "Read|Glob",
    "hooks": [{"type": "command", "command": f"bash \"{hooks_dir}/guardrail-context-preflight-guard-hook.sh\""}],
})

post = hooks.setdefault("PostToolUse", [])
post[:] = [h for h in post if "guardrail-context-output-guard-hook.sh" not in str(h) and "postwrite-guardrail.sh" not in str(h)]
post.append({
    "matcher": "Bash|Read|Grep|Glob",
    "hooks": [{"type": "command", "command": f"bash \"{hooks_dir}/guardrail-context-output-guard-hook.sh\""}],
})
post.append({
    "matcher": "Write|Edit",
    "hooks": [{"type": "command", "command": f"BA_KIT_HOOK_HOME=\"{pathlib.Path.home()}/.codex/ba-kit\" bash \"{hooks_dir}/postwrite-guardrail.sh\""}],
})

cfg["hooks"] = hooks
hooks_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PYEOF
}

remove_stale_templates() {
  local target_dir="$1"
  local file_name

  for file_name in "${STALE_TEMPLATE_FILES[@]}"; do
    rm -f "${target_dir}/${file_name}"
  done
}

remove_stale_core_paths() {
  local target_dir="$1"
  local path_name

  for path_name in "${STALE_CORE_PATHS[@]}"; do
    rm -rf "${target_dir}/${path_name}"
  done
}

generate_codex_assets
cleanup_previous_install

node - "${SOURCE_SKILLS}" "${SOURCE_AGENTS}" "${SOURCE_TEMPLATES}" "${TARGET_HOME}" "${TARGET_SKILLS}" "${TARGET_AGENTS}" "${TARGET_TEMPLATES}" "${TARGET_CONFIG}" "${CANONICAL_STEP_SOURCE}" <<'NODE'
const fs = require("node:fs");
const path = require("node:path");

const [
  sourceSkills,
  sourceAgents,
  sourceTemplates,
  targetHome,
  targetSkills,
  targetAgents,
  targetTemplates,
  targetConfig,
  canonicalStepSource,
] =
  process.argv.slice(2);

const ensureDir = (dirPath) => {
  fs.mkdirSync(dirPath, { recursive: true });
};

const copyContents = (sourceDir, targetDir) => {
  if (!fs.existsSync(sourceDir)) {
    return [];
  }

  ensureDir(targetDir);
  const copied = [];

  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    const sourcePath = path.join(sourceDir, entry.name);
    const targetPath = path.join(targetDir, entry.name);
    fs.cpSync(sourcePath, targetPath, {
      recursive: true,
      force: true,
      dereference: false,
      preserveTimestamps: true,
    });
    copied.push(targetPath);
  }

  return copied;
};

const parseField = (content, field) => {
  const match = content.match(new RegExp(`^${field}\\s*=\\s*"((?:\\\\.|[^"])*)"$`, "m"));
  if (!match) {
    return "";
  }

  return match[1].replace(/\\"/g, '"');
};

const escapeTomlString = (value) => value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
const managedAgentNames = new Set([
  "ba-documentation-manager",
  "ba-researcher",
  "requirements-engineer",
  "ui-ux-designer",
]);
const beginMarker = "# BEGIN BA-kit managed agents";
const endMarker = "# END BA-kit managed agents";

const removeManagedAgentRegistrations = (configPath) => {
  if (!fs.existsSync(configPath)) {
    return;
  }

  const lines = fs.readFileSync(configPath, "utf8").split(/\r?\n/);
  const kept = [];

  for (let index = 0; index < lines.length; ) {
    const line = lines[index];

    if (line.trim() === beginMarker) {
      index += 1;
      while (index < lines.length && lines[index].trim() !== endMarker) {
        index += 1;
      }
      if (index < lines.length) {
        index += 1;
      }
      continue;
    }

    const headerMatch = line.match(/^\[agents\.([^\]]+)\]$/);
    if (headerMatch && managedAgentNames.has(headerMatch[1])) {
      const block = [];
      while (index < lines.length && (block.length === 0 || !/^\[/.test(lines[index]))) {
        block.push(lines[index]);
        index += 1;
      }
      const agentName = headerMatch[1];
      const baKitConfigFile = new RegExp(`^config_file\\s*=\\s*"agents/${agentName}\\.toml"\\s*$`, "m");
      if (baKitConfigFile.test(block.join("\n"))) {
        continue;
      }
      kept.push(...block);
      continue;
    }

    kept.push(line);
    index += 1;
  }

  const cleaned = kept.join("\n").replace(/\n{3,}/g, "\n\n").replace(/\s+$/, "");
  fs.writeFileSync(configPath, cleaned ? `${cleaned}\n` : "");
};

const buildAgentRegistration = (agentTomlPath) => {
  const content = fs.readFileSync(agentTomlPath, "utf8");
  const agentName =
    parseField(content, "name") || path.basename(agentTomlPath, path.extname(agentTomlPath));
  const description =
    parseField(content, "description") || `Codex BA agent from ${path.basename(agentTomlPath)}`;
  const registrationHeader = `[agents.${agentName}]`;
  return [
    registrationHeader,
    `description = "${escapeTomlString(description)}"`,
    `config_file = "agents/${path.basename(agentTomlPath)}"`,
    "",
  ].join("\n");
};

const writeAgentRegistrations = (configPath, agentTomlPaths) => {
  removeManagedAgentRegistrations(configPath);
  const configContent = fs.existsSync(configPath) ? fs.readFileSync(configPath, "utf8").replace(/\s+$/, "") : "";
  const registrationBlock = [
    beginMarker,
    ...agentTomlPaths.map(buildAgentRegistration).map((block) => block.trimEnd()),
    endMarker,
    "",
  ].join("\n");

  ensureDir(path.dirname(configPath));
  const updated =
    configContent.length === 0 ? registrationBlock : `${configContent}\n\n${registrationBlock}`;
  fs.writeFileSync(configPath, updated);
};

ensureDir(targetHome);
ensureDir(targetSkills);
ensureDir(targetAgents);
ensureDir(targetTemplates);

const installedSkills = copyContents(sourceSkills, targetSkills);
const installedAgents = copyContents(sourceAgents, targetAgents);
const installedTemplates = copyContents(sourceTemplates, targetTemplates);
const installedStepFiles = copyContents(canonicalStepSource, path.join(targetSkills, "ba-start", "steps"));

const registrations = [];
const agentTomlPaths = [];
for (const entry of installedAgents) {
  if (entry.endsWith(".toml")) {
    agentTomlPaths.push(entry);
    registrations.push(path.basename(entry, ".toml"));
  }
}
writeAgentRegistrations(targetConfig, agentTomlPaths);

console.log(`Installed skills into ${targetSkills}`);
console.log(`Installed agents into ${targetAgents}`);
console.log(`Installed templates into ${targetTemplates}`);
if (installedSkills.length === 0) {
  console.log("No skill files were found to install.");
}
if (installedAgents.length === 0) {
  console.log("No agent files were found to install.");
}
if (installedTemplates.length === 0) {
  console.log("No template files were found to install.");
}
if (installedStepFiles.length === 0) {
  console.log("No canonical ba-start step files were copied.");
}
if (registrations.length > 0) {
  console.log(`Refreshed Codex agent registrations in ${targetConfig}: ${registrations.join(", ")}`);
} else {
  console.log(`No Codex agent registrations were available for ${targetConfig}`);
}
NODE

install_cli
if [[ -d "${CORE_SOURCE}" ]]; then
  copy_tree "${CORE_SOURCE}" "${CORE_TARGET}"
  remove_stale_core_paths "${CORE_TARGET}"
  echo "Installed BA core to ${CORE_TARGET}"
fi
remove_stale_templates "${TARGET_TEMPLATES}"
load_guardrail_scripts "codex"
install_guardrail_runtime_assets
echo "Installed guardrail runtime assets to ${CORE_TARGET} (${#GUARDRAIL_SCRIPTS[@]} scripts)"
write_codex_hook_scripts
echo "Created Codex hook scripts in ${HOOK_TARGET}"
register_codex_hooks
echo "Registered Codex hooks in ${HOOKS_FILE}"
write_manifest
echo "Installed update CLI to ${LOCAL_BIN_TARGET}/ba-kit"
