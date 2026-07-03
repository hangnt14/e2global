#!/usr/bin/env bash
# BA-kit index validation hook — PostToolUse (matcher: Write|Edit)
# Detects writes to index files and auto-runs validator.
# Primary enforcement is the hard instruction in step files.
# This hook is the fallback safety net.

set -euo pipefail

BA_KIT_HOOK_HOME="${HOME}/.claude/ba-kit"

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
  return 1
}

# ── read tool input ──────────────────────────────────────────────────

TOOL_DATA="$(cat - 2>/dev/null || echo "{}")"
if [[ -z "${TOOL_DATA}" ]] || [[ "${TOOL_DATA}" == "{}" ]]; then
  exit 0
fi

# Extract file_path from tool input JSON
FILE_PATH="$(echo "${TOOL_DATA}" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('file_path', data.get('path', data.get('file', ''))))
except Exception:
    pass
" 2>/dev/null || echo "")"

if [[ -z "${FILE_PATH}" ]]; then
  exit 0
fi

# ── detect index files ───────────────────────────────────────────────

# Map path patterns to index keys
# backbone-index.md            -> backbone_index  (no module)
# userstories/index.md         -> userstories_index
# usecases/index.md            -> usecases_index
# ascii-screen/index.md        -> ascii_screen_index
# reverse-index.md             -> reverse_index    (no module, optional)

INDEX_KEY=""
IS_MODULE_INDEX="false"

if [[ "${FILE_PATH}" =~ /backbone-index\.md$ ]]; then
  INDEX_KEY="backbone_index"
elif [[ "${FILE_PATH}" =~ /userstories/index\.md$ ]]; then
  INDEX_KEY="userstories_index"
  IS_MODULE_INDEX="true"
elif [[ "${FILE_PATH}" =~ /usecases/index\.md$ ]]; then
  INDEX_KEY="usecases_index"
  IS_MODULE_INDEX="true"
elif [[ "${FILE_PATH}" =~ /ascii-screen/index\.md$ ]]; then
  INDEX_KEY="ascii_screen_index"
  IS_MODULE_INDEX="true"
fi

if [[ -z "${INDEX_KEY}" ]]; then
  exit 0
fi

# ── extract slug, date, module from path ─────────────────────────────

# Path format: plans/{slug}-{date}/...
# date = YYMMDD-HHmm (6 digits - 4 digits)
SLUG_DATE="$(echo "${FILE_PATH}" | python3 -c "
import re, sys
text = sys.stdin.read().strip()
m = re.search(r'plans/(.+?)-(\d{6}-\d{4})/', text)
if m:
    print(f'{m.group(1)}|{m.group(2)}', end='')
" 2>/dev/null || echo "")"

if [[ -z "${SLUG_DATE}" ]]; then
  exit 0
fi

SLUG="${SLUG_DATE%%|*}"
DATE_TOKEN="${SLUG_DATE##*|}"

MODULE_SLUG=""
if [[ "${IS_MODULE_INDEX}" == "true" ]]; then
  MODULE_SLUG="$(echo "${FILE_PATH}" | python3 -c "
import re, sys
text = sys.stdin.read().strip()
m = re.search(r'03_modules/([^/]+)/', text)
if m:
    print(m.group(1), end='')
" 2>/dev/null || echo "")"
fi

# ── run validator ─────────────────────────────────────────────────────

VALIDATOR_SCRIPT="${BA_KIT_HOOK_HOME}/scripts/validate-index-quality.py"
if [[ ! -f "${VALIDATOR_SCRIPT}" ]]; then
  # Fallback: look in registered repo
  if [[ -f "${BA_KIT_HOOK_HOME}/state/claude.env" ]]; then
    REPO="$(grep 'BA_KIT_SOURCE_REPO=' "${BA_KIT_HOOK_HOME}/state/claude.env" 2>/dev/null | cut -d= -f2- || echo "")"
    if [[ -n "${REPO}" ]] && [[ -f "${REPO}/scripts/validate-index-quality.py" ]]; then
      VALIDATOR_SCRIPT="${REPO}/scripts/validate-index-quality.py"
    fi
  fi
fi

if [[ ! -f "${VALIDATOR_SCRIPT}" ]]; then
  echo "[BA-kit index hook] WARNING: validator script not found, cannot auto-validate ${INDEX_KEY}" >&2
  exit 0
fi

# Build arguments
ARGS=(--repo . --index-key "${INDEX_KEY}" --slug "${SLUG}" --date "${DATE_TOKEN}")
if [[ -n "${MODULE_SLUG}" ]]; then
  ARGS+=(--module "${MODULE_SLUG}")
fi
ARGS+=(--writeback)

# Run validation
RESULT="$(python3 "${VALIDATOR_SCRIPT}" "${ARGS[@]}" 2>&1)"
EXIT_CODE=$?

# ── inject result into context ───────────────────────────────────────

STATUS="$(echo "${RESULT}" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('status', 'fail'), end='')
except Exception:
    print('fail', end='')
" 2>/dev/null || echo "fail")"

STALE_STATUS="$(echo "${RESULT}" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('suggested_stale_status', 'stale'), end='')
except Exception:
    print('stale', end='')
" 2>/dev/null || echo "stale")"

if [[ "${EXIT_CODE}" -eq 0 ]] && [[ "${STATUS}" == "pass" ]]; then
  echo "[BA-kit index hook] ${INDEX_KEY} validated: stale_status=${STALE_STATUS}" >&2
elif [[ "${EXIT_CODE}" -eq 0 ]] && [[ "${STATUS}" == "warn" ]]; then
  echo "[BA-kit index hook] ${INDEX_KEY} validated with warnings: stale_status=${STALE_STATUS}. Review warnings above." >&2
else
  echo "[BA-kit index hook] WARNING: ${INDEX_KEY} validation FAILED — stale_status=${STALE_STATUS}. Run 'ba-kit validate-index --index-key ${INDEX_KEY} --slug ${SLUG} --date ${DATE_TOKEN}$([[ -n "${MODULE_SLUG}" ]] && echo " --module ${MODULE_SLUG}") --writeback' after fixing index." >&2
fi

exit 0
