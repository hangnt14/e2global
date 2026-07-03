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
  # Replace placeholder with the real Python we already found
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

TARGET_HOME="${HOME}/.claude"
TARGET_BA_KIT="${TARGET_HOME}/ba-kit"
TARGET_SCRIPTS="${TARGET_BA_KIT}/scripts"
TARGET_HOOKS="${TARGET_BA_KIT}/hooks"
TARGET_DOCS="${TARGET_BA_KIT}/docs"
TARGET_STATE="${TARGET_BA_KIT}/state"
LOCAL_BIN_TARGET="${HOME}/.local/bin"
STATE_TARGET="${HOME}/.local/share/ba-kit/installations"
SETTINGS_FILE="${TARGET_HOME}/settings.json"

# CodeX targets
CODEX_HOME="${HOME}/.codex"
CODEX_BA_KIT="${CODEX_HOME}/ba-kit"
CODEX_SCRIPTS="${CODEX_BA_KIT}/scripts"
CODEX_HOOKS="${CODEX_BA_KIT}/hooks"
CODEX_STATE="${CODEX_BA_KIT}/state"
CODEX_HOOKS_FILE="${CODEX_HOME}/hooks.json"

GUARDRAIL_SCRIPTS=()

# ── helpers ──────────────────────────────────────────────────────────

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

install_cli() {
  local temp_target
  mkdir -p "${LOCAL_BIN_TARGET}"
  temp_target="$(mktemp "${LOCAL_BIN_TARGET}/ba-kit.tmp.XXXXXX")"
  cp "${ROOT_DIR}/scripts/ba-kit" "${temp_target}"
  chmod +x "${temp_target}"
  mv "${temp_target}" "${LOCAL_BIN_TARGET}/ba-kit"
}

# ── guardrail script installation ────────────────────────────────────

install_guardrail_scripts() {
  local script_name

  ensure_dir "${TARGET_SCRIPTS}"
  for script_name in "${GUARDRAIL_SCRIPTS[@]}"; do
    if [[ ! -f "${ROOT_DIR}/scripts/${script_name}" ]]; then
      echo "Guardrail script missing: ${ROOT_DIR}/scripts/${script_name}" >&2
      exit 1
    fi
    cp "${ROOT_DIR}/scripts/${script_name}" "${TARGET_SCRIPTS}/${script_name}"
  done
}

install_guardrail_docs() {
  ensure_dir "${TARGET_DOCS}"
  cp "${ROOT_DIR}/docs/runtime-hard-guardrails.md" "${TARGET_DOCS}/runtime-hard-guardrails.md"
  if [[ -f "${ROOT_DIR}/core/token-budget.md" ]]; then
    cp "${ROOT_DIR}/core/token-budget.md" "${TARGET_DOCS}/token-budget.md"
  fi
  if [[ -f "${ROOT_DIR}/docs/ba-qc-export-bridge-note.md" ]]; then
    cp "${ROOT_DIR}/docs/ba-qc-export-bridge-note.md" "${TARGET_DOCS}/ba-qc-export-bridge-note.md"
  fi
}

# ── core assets installation ──────────────────────────────────────────

install_core_assets() {
  # Core files for scripts (REPO_ROOT = ~/.claude/ba-kit/)
  ensure_dir "${TARGET_BA_KIT}/core/behavior"
  cp "${ROOT_DIR}/core/contract.yaml" "${TARGET_BA_KIT}/core/contract.yaml"
  cp "${ROOT_DIR}/core/contract-behavior.md" "${TARGET_BA_KIT}/core/contract-behavior.md"
  cp "${ROOT_DIR}/core/behavior/"*.md "${TARGET_BA_KIT}/core/behavior/"

  # Templates
  ensure_dir "${TARGET_BA_KIT}/templates"
  cp -r "${ROOT_DIR}/templates/"* "${TARGET_BA_KIT}/templates/"

  # Skills (step files)
  ensure_dir "${TARGET_BA_KIT}/skills"
  cp -r "${ROOT_DIR}/skills/"* "${TARGET_BA_KIT}/skills/"

  # Also copy contract.yaml to home for load_contract() home-first check
  ensure_dir "${TARGET_HOME}/core"
  cp "${ROOT_DIR}/core/contract.yaml" "${TARGET_HOME}/core/contract.yaml"

  echo "Installed core assets to ${TARGET_BA_KIT}/core/ and templates/"
}

# ── hook script generation ───────────────────────────────────────────

write_preflight_hook() {
  cat > "${TARGET_HOOKS}/guardrail-preflight-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit guardrail preflight hook — UserPromptSubmit
# Detects BA-kit context, resolves command/slug/date, runs guardrail-preflight.py,
# and outputs a compact verdict into the prompt context.

set -euo pipefail

BA_KIT_HOOK_HOME="${HOME}/.claude/ba-kit"
BA_KIT_STATE_DIR="${BA_KIT_HOOK_HOME}/state"

# ── detect BA-kit context ────────────────────────────────────────────

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
  local dirname
  dirname="$(basename "${plan_dir}")"
  # plans/{slug}-{YYMMDD-HHmm}
  local slug="${dirname%-[0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]}"
  local date_token="${dirname#${slug}-}"
  printf '%s\n%s\n' "${slug}" "${date_token}"
}

detect_command_from_prompt() {
  local prompt_text="$1"

  # Explicit ba-start subcommands
  if echo "${prompt_text}" | grep -qiE '\bba-start\s+(frd|stories|srs|package|status|next)\b'; then
    echo "${prompt_text}" | grep -oiE '\bba-start\s+(frd|stories|srs|package|status|next)\b' \
      | head -1 | sed 's/ba-start //'
    return 0
  fi

  # Natural language patterns (from core/workflows/do.md routing table)
  if echo "${prompt_text}" | grep -qiE '\b(create|generate|produce|build|write)\b.*\b(FRD|functional requirements)\b'; then
    echo "frd"
    return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(create|generate|produce|build|write)\b.*\b(user stories|stories)\b'; then
    echo "stories"
    return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(create|generate|produce|build|write)\b.*\b(SRS|software requirements|spec)\b'; then
    echo "srs"
    return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(package|bundle|handoff|deliver|ban giao|xuat goi)\b'; then
    echo "package"
    return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(status|check|kiem tra)\b.*\b(progress|tien do)\b'; then
    echo "status"
    return 0
  fi
  if echo "${prompt_text}" | grep -qiE '\b(tiep tuc|tiep theo|next|continue|resume)\b'; then
    echo "next"
    return 0
  fi

  return 1
}

detect_module() {
  local plan_dir="$1"
  local modules_dir="${plan_dir}/03_modules"
  if [[ ! -d "${modules_dir}" ]]; then
    return 0
  fi

  # If user typed --module in prompt, extract it
  local module_from_prompt
  module_from_prompt="$(echo "${PROMPT_TEXT:-}" | grep -oP '(?<=--module\s)\S+' | head -1 || true)"
  if [[ -n "${module_from_prompt}" ]]; then
    printf '%s\n' "${module_from_prompt}"
    return 0
  fi

  # If only one module exists, use it
  local count=0
  local single=""
  for d in "${modules_dir}"/*/; do
    [[ -d "${d}" ]] || continue
    count=$((count + 1))
    single="$(basename "${d}")"
  done
  if [[ "${count}" -eq 1 ]]; then
    printf '%s\n' "${single}"
  fi
}

# ── main ─────────────────────────────────────────────────────────────

PLAN_DIR="$(detect_plan_dir)" || exit 0

PROMPT_TEXT="${1:-}"
if [[ -z "${PROMPT_TEXT}" ]] && [[ -n "${CLAUDE_PROMPT:-}" ]]; then
  PROMPT_TEXT="${CLAUDE_PROMPT}"
fi

COMMAND="$(detect_command_from_prompt "${PROMPT_TEXT}")" || exit 0

# Only preflight guarded commands
case "${COMMAND}" in
  frd|stories|srs|package|status|next) ;;
  *) exit 0 ;;
esac

SLUG_DATE=($(extract_slug_date "${PLAN_DIR}"))
SLUG="${SLUG_DATE[0]}"
DATE_TOKEN="${SLUG_DATE[1]}"
MODULE="$(detect_module "${PLAN_DIR}")"

# Build preflight args
# Resolve BA-kit source repo from manifest (same logic as CLI resolve_registered_repo)
SOURCE_REPO=""
if [[ -f "${HOME}/.local/share/ba-kit/installations/claude.env" ]]; then
  SOURCE_REPO="$(grep '^BA_KIT_SOURCE_REPO=' "${HOME}/.local/share/ba-kit/installations/claude.env" | head -1 | cut -d= -f2-)"
fi
if [[ -z "${SOURCE_REPO}" ]] && [[ -f "${HOME}/.local/share/ba-kit/installations/claude-code.env" ]]; then
  SOURCE_REPO="$(grep '^BA_KIT_SOURCE_REPO=' "${HOME}/.local/share/ba-kit/installations/claude-code.env" | head -1 | cut -d= -f2-)"
fi
if [[ -z "${SOURCE_REPO}" ]]; then
  exit 0
fi

PREFLIGHT_ARGS=(
  --command "${COMMAND}"
  --slug "${SLUG}"
  --date "${DATE_TOKEN}"
  --repo "${PLAN_DIR%/plans/${SLUG}-${DATE_TOKEN}}"
)
if [[ -n "${MODULE:-}" ]]; then
  PREFLIGHT_ARGS+=(--module "${MODULE}")
fi

mkdir -p "${BA_KIT_STATE_DIR}"
PREFLIGHT_OUT="${BA_KIT_STATE_DIR}/last-preflight.json"

# Resolve Python (python3 may be a non-functional Windows Store stub)
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

"${_PY}" "${HOME}/.claude/ba-kit/scripts/guardrail-preflight.py" \
  "${PREFLIGHT_ARGS[@]}" \
  --output "${PREFLIGHT_OUT}" >/dev/null 2>&1 || true

if [[ ! -f "${PREFLIGHT_OUT}" ]]; then
  exit 0
fi

# Parse preflight JSON and emit verdict
"${_PY}" - "${PREFLIGHT_OUT}" <<'PYEOF'
import json, sys, pathlib

preflight = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
status = preflight.get("status", "")
command = preflight.get("command", "")
resolved_slug = preflight.get("resolved_slug", "")
message = preflight.get("message", "").strip()
indexes = preflight.get("indexes", {})

has_current = any(
    v.get("state") == "current" for v in indexes.values() if isinstance(v, dict)
)
action_guardrail = preflight.get("action_guardrail", {})

if status == "block":
    output_mode = "probe"
elif has_current:
    output_mode = "delta"
else:
    output_mode = "full"

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

lines.append(
    f"If a broader read is necessary, emit exactly: READ_ESCALATION: {command} read <path> due to <reason>."
)

print("\n".join(lines))
PYEOF
HOOKEOF

  chmod +x "${TARGET_HOOKS}/guardrail-preflight-hook.sh"
}

write_audit_hook() {
  cat > "${TARGET_HOOKS}/guardrail-audit-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit guardrail audit hook — Stop
# After Claude Code session ends, audits actual reads against preflight allowlist.

set -euo pipefail

# Resolve Python (python3 may be a non-functional Windows Store stub)
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

PREFLIGHT_PATH="${HOME}/.claude/ba-kit/state/last-preflight.json"
AUDIT_OUT="${HOME}/.claude/ba-kit/state/last-audit.json"

if [[ ! -f "${PREFLIGHT_PATH}" ]]; then
  exit 0
fi

READS_MANIFEST="${HOME}/.claude/ba-kit/state/reads-manifest.json"
if [[ ! -f "${READS_MANIFEST}" ]]; then
  # No reads tracked — nothing to audit
  rm -f "${PREFLIGHT_PATH}"
  exit 0
fi

"${_PY}" "${HOME}/.claude/ba-kit/scripts/guardrail-audit.py" \
  --preflight "${PREFLIGHT_PATH}" \
  --reads-manifest "${READS_MANIFEST}" \
  --output "${AUDIT_OUT}" >/dev/null 2>&1 || true

if [[ -f "${AUDIT_OUT}" ]]; then
  status="$("${_PY}" -c "
import json, pathlib
d = json.loads(pathlib.Path('${AUDIT_OUT}').read_text())
print(d.get('status', ''))
" 2>/dev/null || echo "")"

  case "${status}" in
    fail)
      echo "GUARDRAIL_AUDIT_FAIL: read audit found violations" >&2
      ;;
    warn)
      echo "GUARDRAIL_AUDIT_WARN: read audit found minor issues" >&2
      ;;
    pass)
      echo "GUARDRAIL_AUDIT_PASS" >&2
      ;;
  esac
fi

# Cleanup state after audit
rm -f "${PREFLIGHT_PATH}" "${READS_MANIFEST}"
HOOKEOF

  chmod +x "${TARGET_HOOKS}/guardrail-audit-hook.sh"
}

write_context_output_guard_hook() {
  cat > "${TARGET_HOOKS}/guardrail-context-output-guard-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit context output guard — PostToolUse (matcher: Bash|Read|Grep)
# Detects oversized tool outputs and injects context warnings.
# Tracks violations for end-of-session audit.

set -euo pipefail

BA_KIT_HOOK_HOME="${HOME}/.claude/ba-kit"
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

# Read the tool call data from stdin (Claude Code passes JSON)
TOOL_DATA="$(cat - 2>/dev/null || echo "{}")"

if [[ -z "${TOOL_DATA}" ]] || [[ -z "${_PY}" ]]; then
  exit 0
fi

if [[ "${TOOL_DATA}" == "{}" ]]; then
  exit 0
fi

# Run the context guard check — outputs warning to stdout if oversized
"${_PY}" "${HOME}/.claude/ba-kit/scripts/context-output-guard.py" <<< "${TOOL_DATA}" 2>/dev/null || true
HOOKEOF
  chmod +x "${TARGET_HOOKS}/guardrail-context-output-guard-hook.sh"
}

write_context_preflight_guard_hook() {
  cat > "${TARGET_HOOKS}/guardrail-context-preflight-guard-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit context preflight guard — PreToolUse (matcher: Read)
# Checks file size BEFORE Read executes. Blocks oversized files lacking offset+limit.
# Tracks reads for re-read detection. Writes warnings to stdout (injected into context).

set -euo pipefail

BA_KIT_HOOK_HOME="${HOME}/.claude/ba-kit"
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

# Read the tool call data from stdin (Claude Code passes JSON)
TOOL_DATA="$(cat - 2>/dev/null || echo "{}")"

if [[ -z "${TOOL_DATA}" ]] || [[ "${TOOL_DATA}" == "{}" ]]; then
  exit 0
fi

# Run the preflight check — exits 1 to BLOCK, 0 to proceed (may still emit warning)
"${_PY}" "${HOME}/.claude/ba-kit/scripts/context-preflight-guard.py" <<< "${TOOL_DATA}" 2>/dev/null
PREFLIGHT_EXIT=$?

if [[ ${PREFLIGHT_EXIT} -eq 1 ]]; then
  # BLOCK: file too large, no offset+limit. Exit 1 blocks the Read tool.
  # Warning message was already written to stdout by the Python script.
  exit 1
fi

# Exit 0: proceed normally (may include a warning message on stdout)
exit 0
HOOKEOF
  chmod +x "${TARGET_HOOKS}/guardrail-context-preflight-guard-hook.sh"
}

write_context_audit_hook() {
  cat > "${TARGET_HOOKS}/guardrail-context-audit-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit context audit hook — Stop
# After session ends, reports context waste from oversized tool outputs.

set -euo pipefail

STATE_DIR="${HOME}/.claude/ba-kit/state"
VIOLATIONS_FILE="${STATE_DIR}/context-violations.jsonl"

if [[ ! -f "${VIOLATIONS_FILE}" ]]; then
  exit 0
fi

# Resolve Python (python3 may be a non-functional Windows Store stub)
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

"${_PY}" - "${VIOLATIONS_FILE}" <<'PYEOF'
import json, sys, pathlib

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

# Carry proxy: violation sequence distance, not actual assistant-turn count.
# Sorts violations by timestamp; each violation's carry = number of subsequent violations.
sorted_by_time = sorted(violations, key=lambda v: v.get("timestamp", ""))
cached_token_waste = 0
for i, v in enumerate(sorted_by_time):
    subsequent = len(sorted_by_time) - i - 1
    carry = max(1, subsequent)
    cached_token_waste += v["estimated_tokens"] * carry

if len(violations) <= 1:
    carry_label = "estimated (fallback, single violation)"
else:
    avg_proxy = sum(max(1, len(sorted_by_time) - i - 1) for i in range(len(sorted_by_time))) / len(sorted_by_time)
    carry_label = f"carry proxy (avg {avg_proxy:.1f} violation sequence distance)"

tool_counts = {}
for v in violations:
    t = v["tool_name"]
    tool_counts[t] = tool_counts.get(t, 0) + 1

# Session budget
budget_path = vf.parent / "context-session-budget.txt"
session_budget_bytes = 0
if budget_path.exists():
    try:
        session_budget_bytes = int(budget_path.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        pass

print("\nCONTEXT_GUARD_AUDIT: session context waste report")
print(f"  Violations: {len(violations)} ({warn_count} warn, {crit_count} critical)")
print(f"  Raw output: {total_bytes / 1024:.1f}kB total ({total_est_tokens} tokens)")
print(f"  Est. cached waste: ~{cached_token_waste} tokens ({carry_label})")
print(f"  Session budget: {session_budget_bytes / 1024:.1f}kB total")
print(f"  By tool: {', '.join(f'{k}={v}' for k, v in sorted(tool_counts.items()))}")
print()

# Top violations
print("  Top 5 largest outputs:")
by_size = sorted(violations, key=lambda v: v["size_bytes"], reverse=True)[:5]
for i, v in enumerate(by_size, 1):
    summary = v["tool_input_summary"][:80]
    print(f"    {i}. {v['tool_name']}: {v['size_bytes'] / 1024:.1f}kB — {summary}")

print()
print("  Remediation:")
print("    - Use Glob not find. Use Read with offset+limit. Use Grep with head_limit.")
print("    - Read large files in sections (TOC first, then targeted ranges).")
print("    - Pipe Bash output through head/tail when uncertain.")
print()
PYEOF

# Cleanup after audit
rm -f "${VIOLATIONS_FILE}"
rm -f "${STATE_DIR}/context-reads-manifest.jsonl"
rm -f "${STATE_DIR}/context-session-budget.txt"
HOOKEOF
  chmod +x "${TARGET_HOOKS}/guardrail-context-audit-hook.sh"
}

write_write_scope_hook() {
  cat > "${TARGET_HOOKS}/guardrail-write-scope-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit write-scope enforcement hook — PreToolUse (matcher: Write|Edit)
# Blocks file writes outside the command-owned artifact scope.

set -euo pipefail

BA_KIT_HOOK_HOME="${HOME}/.claude/ba-kit"
BA_KIT_STATE_DIR="${BA_KIT_HOOK_HOME}/state"

# ── detect BA-kit context ────────────────────────────────────────────

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

detect_plan_dir >/dev/null 2>&1 || exit 0

# Resolve Python (python3 may be a non-functional Windows Store stub)
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

# ── extract target path from tool input ──────────────────────────────

TOOL_INPUT="${1:-}"
TOOL_NAME="${2:-}"

# Claude Code passes tool input as JSON on stdin for PreToolUse hooks
# The hook receives: tool_name, tool_input (JSON string)
if [[ -z "${TOOL_INPUT}" ]]; then
  # Try reading from stdin (Claude Code hook interface)
  TOOL_INPUT="$(cat - 2>/dev/null || echo "")"
fi

# Extract file path from tool input
TARGET_PATH="$(echo "${TOOL_INPUT}" | "${_PY}" -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('file_path', data.get('path', data.get('file', ''))))
except Exception:
    pass
" 2>/dev/null || echo "")"

if [[ -z "${TARGET_PATH}" ]]; then
  exit 0
fi

# ── resolve last detected command ────────────────────────────────────

PREFLIGHT_PATH="${HOME}/.claude/ba-kit/state/last-preflight.json"
DETECTED_CMD=""
if [[ -f "${PREFLIGHT_PATH}" ]]; then
  DETECTED_CMD="$("${_PY}" -c "
import json, pathlib
d = json.loads(pathlib.Path('${PREFLIGHT_PATH}').read_text())
print(d.get('command', ''))
" 2>/dev/null || echo "")"
fi

if [[ -z "${DETECTED_CMD}" ]]; then
  exit 0
fi

# ── run write-scope check ────────────────────────────────────────────

if "${HOME}/.local/bin/ba-kit" check-write-scope --command "${DETECTED_CMD}" "${TARGET_PATH}" 2>/dev/null; then
  exit 0
else
  echo "GUARDRAIL_BLOCK: write-scope violation — ${TARGET_PATH} not in allowed scope for ${DETECTED_CMD}" >&2
  exit 1
fi
HOOKEOF

  chmod +x "${TARGET_HOOKS}/guardrail-write-scope-hook.sh"
}

write_index_validation_hook() {
  cp "${ROOT_DIR}/scripts/guardrail-index-validation-hook.sh" "${TARGET_HOOKS}/guardrail-index-validation-hook.sh"
  chmod +x "${TARGET_HOOKS}/guardrail-index-validation-hook.sh"
}

write_postwrite_guardrail_hook() {
  cp "${ROOT_DIR}/scripts/hooks/postwrite-guardrail.sh" "${TARGET_HOOKS}/postwrite-guardrail.sh"
  chmod +x "${TARGET_HOOKS}/postwrite-guardrail.sh"
}

# ── settings.json hook registration ──────────────────────────────────

register_hooks() {
  ensure_dir "${TARGET_HOME}"

  # Initialize settings.json if it doesn't exist
  if [[ ! -f "${SETTINGS_FILE}" ]]; then
    echo '{}' > "${SETTINGS_FILE}"
  fi

  "${PYTHON3}" - "${SETTINGS_FILE}" "${TARGET_HOOKS}" <<'PYEOF'
import json, pathlib, sys

settings_path = pathlib.Path(sys.argv[1])
hooks_dir = sys.argv[2]
settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
if not isinstance(settings, dict):
    settings = {}

hooks = settings.setdefault("hooks", {})

# UserPromptSubmit — license heartbeat (runs BEFORE preflight)
ups_hooks = hooks.setdefault("UserPromptSubmit", [])
ups_hooks[:] = [h for h in ups_hooks if "license-heartbeat-hook.sh" not in str(h)]
ups_hooks.insert(0, {
    "matcher": "",
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/license-heartbeat-hook.sh\""
    }]
})

# Remove any existing ba-kit UserPromptSubmit preflight hooks
ups_hooks[:] = [h for h in ups_hooks if "guardrail-preflight-hook.sh" not in str(h)]
ups_hooks.append({
    "matcher": "",
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/guardrail-preflight-hook.sh\""
    }]
})

# Stop — audit
stop_hooks = hooks.setdefault("Stop", [])
stop_hooks[:] = [h for h in stop_hooks if "guardrail-audit-hook.sh" not in str(h) and "guardrail-context-audit-hook.sh" not in str(h)]
stop_hooks.append({
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/guardrail-audit-hook.sh\""
    }]
})
stop_hooks.append({
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/guardrail-context-audit-hook.sh\""
    }]
})

# PreToolUse — write-scope (matcher: Write|Edit)
ptu_hooks = hooks.setdefault("PreToolUse", [])
ptu_hooks[:] = [h for h in ptu_hooks if "guardrail-write-scope-hook.sh" not in str(h) and "guardrail-context-preflight-guard-hook.sh" not in str(h)]
ptu_hooks.append({
    "matcher": "Write|Edit",
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/guardrail-write-scope-hook.sh\""
    }]
})
# PreToolUse — context preflight guard (matcher: Read|Glob)
ptu_hooks.append({
    "matcher": "Read|Glob",
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/guardrail-context-preflight-guard-hook.sh\""
    }]
})

# PostToolUse — context output guard (matcher: Bash|Read|Grep|Glob)
post_hooks = hooks.setdefault("PostToolUse", [])
post_hooks[:] = [h for h in post_hooks if "guardrail-context-output-guard-hook.sh" not in str(h)]
post_hooks.append({
    "matcher": "Bash|Read|Grep|Glob",
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/guardrail-context-output-guard-hook.sh\""
    }]
})

# PostToolUse — index validation (matcher: Write|Edit)
# Auto-validates index files after write. Fallback safety net for the hard instruction in step files.
post_hooks[:] = [h for h in post_hooks if "guardrail-index-validation-hook.sh" not in str(h) and "postwrite-guardrail.sh" not in str(h)]
post_hooks.append({
    "matcher": "Write|Edit",
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/guardrail-index-validation-hook.sh\""
    }]
})
post_hooks.append({
    "matcher": "Write|Edit",
    "hooks": [{
        "type": "command",
        "command": f"BA_KIT_HOOK_HOME=\"{pathlib.Path.home()}/.claude/ba-kit\" bash \"{hooks_dir}/postwrite-guardrail.sh\""
    }]
})

settings["hooks"] = hooks
settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PYEOF
}

# ── manifest ─────────────────────────────────────────────────────────

write_manifest() {
  mkdir -p "${STATE_TARGET}"
  cat > "${STATE_TARGET}/claude.env" <<EOF
BA_KIT_RUNTIME=claude-code
BA_KIT_SOURCE_REPO=${ROOT_DIR}
BA_KIT_INSTALLED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BA_KIT_INSTALLER=scripts/install-claude-code-ba-kit.sh
BA_KIT_GUARDRAIL_ROOT=${TARGET_BA_KIT}
BA_KIT_GUARDRAIL_PREFLIGHT=${TARGET_SCRIPTS}/guardrail-preflight.py
BA_KIT_GUARDRAIL_EXCERPTS=${TARGET_SCRIPTS}/guardrail-build-excerpts.py
BA_KIT_GUARDRAIL_AUDIT=${TARGET_SCRIPTS}/guardrail-audit.py
BA_KIT_INDEX_VALIDATOR=${TARGET_SCRIPTS}/validate-index-quality.py
BA_KIT_CHECK_TOKEN_BUDGET=${TARGET_SCRIPTS}/check-token-budget.py
BA_KIT_CHECK_WRITE_SCOPE=${TARGET_SCRIPTS}/check-write-scope.py
BA_KIT_CONTEXT_OUTPUT_GUARD=${TARGET_SCRIPTS}/context-output-guard.py
BA_KIT_CONTEXT_PREFLIGHT_GUARD=${TARGET_SCRIPTS}/context-preflight-guard.py
BA_KIT_GUARDRAIL_DOC=${TARGET_DOCS}/runtime-hard-guardrails.md
EOF
}

# ── CodeX installation ───────────────────────────────────────────────

install_codex_scripts() {
  ensure_dir "${CODEX_SCRIPTS}"
  ensure_dir "${CODEX_STATE}"
  cp "${ROOT_DIR}/scripts/context-output-guard.py" "${CODEX_SCRIPTS}/context-output-guard.py"
  cp "${ROOT_DIR}/scripts/context-preflight-guard.py" "${CODEX_SCRIPTS}/context-preflight-guard.py"
}

write_codex_context_preflight_guard_hook() {
  ensure_dir "${CODEX_HOOKS}"
  cat > "${CODEX_HOOKS}/guardrail-context-preflight-guard-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
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
  chmod +x "${CODEX_HOOKS}/guardrail-context-preflight-guard-hook.sh"
}

write_codex_context_output_guard_hook() {
  ensure_dir "${CODEX_HOOKS}"
  cat > "${CODEX_HOOKS}/guardrail-context-output-guard-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
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
TOOL_DATA="$(cat - 2>/dev/null || echo "{}")"
if [[ -z "${TOOL_DATA}" ]] || [[ -z "${_PY}" ]] || [[ "${TOOL_DATA}" == "{}" ]]; then
  exit 0
fi
"${_PY}" "${BA_KIT_HOOK_HOME}/scripts/context-output-guard.py" <<< "${TOOL_DATA}" 2>/dev/null || true
HOOKEOF
  chmod +x "${CODEX_HOOKS}/guardrail-context-output-guard-hook.sh"
}

write_codex_context_audit_hook() {
  ensure_dir "${CODEX_HOOKS}"
  cat > "${CODEX_HOOKS}/guardrail-context-audit-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
set -euo pipefail
STATE_DIR="${HOME}/.codex/ba-kit/state"
VIOLATIONS_FILE="${STATE_DIR}/context-violations.jsonl"
if [[ ! -f "${VIOLATIONS_FILE}" ]]; then
  exit 0
fi
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
"${_PY}" - "${VIOLATIONS_FILE}" <<'PYEOF'
import json, sys, pathlib
vf = pathlib.Path(sys.argv[1])
lines = [l for l in vf.read_text(encoding="utf-8").strip().split("\n") if l]
if not lines:
    sys.exit(0)
violations = [json.loads(l) for l in lines if l]
violations = [v for v in violations if isinstance(v, dict)]
if not violations:
    sys.exit(0)
total_bytes = sum(v["size_bytes"] for v in violations)
total_est_tokens = sum(v["estimated_tokens"] for v in violations)
warn_count = sum(1 for v in violations if v["level"] == "warn")
crit_count = sum(1 for v in violations if v["level"] == "critical")
avg_carry_turns = 30
cached_token_waste = sum(v["estimated_tokens"] * avg_carry_turns for v in violations)
tool_counts = {}
for v in violations:
    t = v["tool_name"]
    tool_counts[t] = tool_counts.get(t, 0) + 1
print("\nCONTEXT_GUARD_AUDIT: CodeX session context waste report")
print(f"  Violations: {len(violations)} ({warn_count} warn, {crit_count} critical)")
print(f"  Raw output: {total_bytes / 1024:.1f}kB total ({total_est_tokens} tokens)")
print(f"  Est. cached waste: ~{cached_token_waste} tokens (avg {avg_carry_turns} turn carry)")
print(f"  By tool: {', '.join(f'{k}={v}' for k, v in sorted(tool_counts.items()))}")
print()
print("  Top 5 largest outputs:")
by_size = sorted(violations, key=lambda v: v["size_bytes"], reverse=True)[:5]
for i, v in enumerate(by_size, 1):
    summary = v["tool_input_summary"][:80]
    print(f"    {i}. {v['tool_name']}: {v['size_bytes'] / 1024:.1f}kB — {summary}")
print()
print("  Remediation:")
print("    - Use Glob not find. Use Read with offset+limit. Use Grep with head_limit.")
print("    - Read large files in sections (TOC first, then targeted ranges).")
print("    - Pipe Bash output through head/tail when uncertain.")
print()
PYEOF
rm -f "${VIOLATIONS_FILE}"
rm -f "${STATE_DIR}/context-reads-manifest.jsonl"
HOOKEOF
  chmod +x "${CODEX_HOOKS}/guardrail-context-audit-hook.sh"
}

register_codex_hooks() {
  ensure_dir "${CODEX_HOME}"

  if [[ ! -f "${CODEX_HOOKS_FILE}" ]]; then
    echo '{"hooks":{}}' > "${CODEX_HOOKS_FILE}"
  fi

  python3 - "${CODEX_HOOKS_FILE}" "${CODEX_HOOKS}" <<'PYEOF'
import json, pathlib, sys

hooks_path = pathlib.Path(sys.argv[1])
hooks_dir = sys.argv[2]
cfg = json.loads(hooks_path.read_text(encoding="utf-8")) if hooks_path.exists() else {}
if not isinstance(cfg, dict):
    cfg = {}
hooks = cfg.setdefault("hooks", {})

# PreToolUse — context preflight guard (matcher: Read|Glob)
ptu = hooks.setdefault("PreToolUse", [])
ptu[:] = [h for h in ptu if "guardrail-context-preflight-guard" not in str(h)]
ptu.append({
    "matcher": "Read|Glob",
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/guardrail-context-preflight-guard-hook.sh\""
    }]
})

# PostToolUse — context output guard (matcher: Bash|Read|Grep|Glob)
post = hooks.setdefault("PostToolUse", [])
post[:] = [h for h in post if "guardrail-context-output-guard" not in str(h)]
post.append({
    "matcher": "Bash|Read|Grep|Glob",
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/guardrail-context-output-guard-hook.sh\""
    }]
})

# Stop — context audit
stop = hooks.setdefault("Stop", [])
stop[:] = [h for h in stop if "guardrail-context-audit" not in str(h)]
stop.append({
    "hooks": [{
        "type": "command",
        "command": f"bash \"{hooks_dir}/guardrail-context-audit-hook.sh\""
    }]
})

cfg["hooks"] = hooks
hooks_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PYEOF
}

write_codex_manifest() {
  mkdir -p "${STATE_TARGET}"
  cat > "${STATE_TARGET}/codex.env" <<EOF
BA_KIT_RUNTIME=codex
BA_KIT_SOURCE_REPO=${ROOT_DIR}
BA_KIT_INSTALLED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BA_KIT_INSTALLER=scripts/install-claude-code-ba-kit.sh
BA_KIT_CONTEXT_PREFLIGHT_GUARD=${CODEX_SCRIPTS}/context-preflight-guard.py
BA_KIT_CONTEXT_OUTPUT_GUARD=${CODEX_SCRIPTS}/context-output-guard.py
EOF
}

install_codex() {
  echo ""
  echo "Installing BA-kit guardrail hooks for CodeX..."
  bash "${ROOT_DIR}/scripts/install-codex-ba-kit.sh"
}

# ── main ─────────────────────────────────────────────────────────────

echo "Installing BA-kit guardrail system for Claude Code from: ${ROOT_DIR}"

ensure_dir "${TARGET_BA_KIT}"
ensure_dir "${TARGET_HOOKS}"
ensure_dir "${TARGET_STATE}"

load_guardrail_scripts "claude"
install_guardrail_scripts
echo "Installed guardrail scripts to ${TARGET_SCRIPTS}"

install_guardrail_docs
echo "Installed guardrail docs to ${TARGET_DOCS}"

install_core_assets

# ── license scripts ──────────────────────────────────────────────────

install_license_scripts() {
  ensure_dir "${TARGET_SCRIPTS}"
  cp "${ROOT_DIR}/scripts/license-register.sh" "${TARGET_SCRIPTS}/license-register.sh"
  cp "${ROOT_DIR}/scripts/license-heartbeat.sh" "${TARGET_SCRIPTS}/license-heartbeat.sh"
  cp "${ROOT_DIR}/scripts/license-reauth.sh" "${TARGET_SCRIPTS}/license-reauth.sh"
  cp "${ROOT_DIR}/scripts/ba-kit-dashboard.py" "${TARGET_SCRIPTS}/ba-kit-dashboard.py"
  chmod +x "${TARGET_SCRIPTS}/license-register.sh"
  chmod +x "${TARGET_SCRIPTS}/license-heartbeat.sh"
  chmod +x "${TARGET_SCRIPTS}/license-reauth.sh"
}

write_license_heartbeat_hook() {
  cat > "${TARGET_HOOKS}/license-heartbeat-hook.sh" <<'HOOKEOF'
#!/usr/bin/env bash
# BA-kit License Heartbeat Hook — UserPromptSubmit
set -euo pipefail
HEARTBEAT_SCRIPT="${HOME}/.claude/ba-kit/scripts/license-heartbeat.sh"
if [[ ! -f "${HEARTBEAT_SCRIPT}" ]]; then
  exit 0
fi
OUTPUT=$(bash "${HEARTBEAT_SCRIPT}" 2>&1) || HEARTBEAT_EXIT=$?
if [[ ${HEARTBEAT_EXIT:-0} -eq 1 ]]; then
  echo ""
  echo "⛔️  BA-KIT LICENSE CHECK FAILED"
  echo "${OUTPUT}"
  echo ""
  echo "Run: ba-kit reauth"
  echo ""
fi
exit 0
HOOKEOF
  chmod +x "${TARGET_HOOKS}/license-heartbeat-hook.sh"
}

install_license_scripts
write_license_heartbeat_hook
echo "Installed license scripts to ${TARGET_SCRIPTS}"

write_preflight_hook
write_audit_hook
write_write_scope_hook
write_context_output_guard_hook
write_context_preflight_guard_hook
write_context_audit_hook
write_index_validation_hook
write_postwrite_guardrail_hook
echo "Created hook scripts in ${TARGET_HOOKS}"

register_hooks
echo "Registered hooks in ${SETTINGS_FILE}"

install_cli
echo "Installed CLI to ${LOCAL_BIN_TARGET}/ba-kit"

write_manifest
echo "Wrote manifest to ${STATE_TARGET}/claude.env"

echo ""
echo "BA-kit Claude Code installation complete."
echo ""
echo "Installed:"
echo "  - ${#GUARDRAIL_SCRIPTS[@]} guardrail Python scripts → ${TARGET_SCRIPTS}"
echo "  - 7 hook scripts → ${TARGET_HOOKS}"
echo "  - Guardrail docs → ${TARGET_DOCS}"
echo "  - Core assets → ${TARGET_HOME}/core/ + templates/ + skills/"
echo "  - CLI → ${LOCAL_BIN_TARGET}/ba-kit"
echo "  - Hooks registered in ${SETTINGS_FILE}"
echo ""
echo "Hooks active for:"
echo "  - UserPromptSubmit: guardrail preflight (detects BA-kit context, emits verdict)"
echo "  - Stop: guardrail audit + context waste audit (post-session reports)"
echo "  - PreToolUse (Write|Edit): write-scope enforcement"
echo "  - PreToolUse (Read|Glob): context preflight guard (blocks oversized reads, detects re-reads)"
echo "  - PostToolUse (Bash|Read|Grep|Glob): context output guard (warns on oversized outputs)"
echo "  - PostToolUse (Write|Edit): index validation (auto-validates index files after write)"
echo ""
echo "Hooks silent outside BA-kit plan directories. No overhead for non-BA work."

# Install CodeX context guard hooks if CodeX is detected
if [[ -d "${CODEX_HOME}" ]]; then
  install_codex
fi
