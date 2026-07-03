#!/usr/bin/env bash
# BA-kit PostToolUse hook — validate screen/usecase files after write/edit
# Installed to runtime BA-kit hook directory.
# Hook luôn exit 0 (non-blocking). Tắt bằng BA_KIT_SKIP_HOOKS=1
set -euo pipefail

if [[ -z "${BA_KIT_HOOK_HOME:-}" ]]; then
  if [[ -d "${HOME}/.codex/ba-kit" ]]; then
    BA_KIT_HOOK_HOME="${HOME}/.codex/ba-kit"
  else
    BA_KIT_HOOK_HOME="${HOME}/.claude/ba-kit"
  fi
fi
SCRIPTS_DIR="${BA_KIT_HOOK_HOME}/scripts"

if [[ "${BA_KIT_SKIP_HOOKS:-0}" == "1" ]]; then
  exit 0
fi

TOOL_DATA="$(cat - 2>/dev/null || echo "{}")"
FILE_PATH="${2:-}"
if [[ -z "${FILE_PATH}" ]] && [[ -n "${TOOL_DATA}" ]] && [[ "${TOOL_DATA}" != "{}" ]]; then
  FILE_PATH="$(echo "${TOOL_DATA}" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    tool_input = data.get('tool_input', data)
    if not isinstance(tool_input, dict):
        tool_input = {}
    print(tool_input.get('file_path') or tool_input.get('path') or tool_input.get('file') or data.get('file_path') or data.get('path') or data.get('file') or '')
except Exception:
    pass
" 2>/dev/null || echo "")"
fi

if [[ ! "${FILE_PATH}" =~ (ascii-screen|usecases)/.*\.md$ ]]; then
  exit 0
fi

if [[ "${FILE_PATH}" =~ ascii-screen/ ]]; then
  if [[ -f "${SCRIPTS_DIR}/check-control-type-compliance.py" ]]; then
    python3 "${SCRIPTS_DIR}/check-control-type-compliance.py" "${FILE_PATH}" --json 2>/dev/null | \
      python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    issues=[i for r in d.get('results',[]) for i in r.get('issues',[])]
    blocks=[i for i in issues if i.get('severity')=='BLOCK']
    warns=[i for i in issues if i.get('severity')=='WARN']
    if blocks: print(f'SCREEN CT: {len(blocks)} BLOCK, {len(warns)} WARN')
    elif warns: print(f'SCREEN CT: {len(warns)} WARN')
except: pass
" || true
  fi

  if [[ -f "${SCRIPTS_DIR}/check-message-placement.py" ]]; then
    python3 "${SCRIPTS_DIR}/check-message-placement.py" "${FILE_PATH}" --json 2>/dev/null | \
      python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    issues=[i for r in d.get('results',[]) for i in r.get('issues',[])]
    if issues: print(f'SCREEN MSG: {len(issues)} issues')
except: pass
" || true
  fi
fi

if [[ -f "${SCRIPTS_DIR}/check-terminology-consistency.py" ]]; then
  python3 "${SCRIPTS_DIR}/check-terminology-consistency.py" "${FILE_PATH}" --json 2>/dev/null | \
    python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    n=len(d.get('findings',[]))
    if n: print(f'TERM: {n} forbidden terms')
except: pass
" || true
fi

# Reference check: scan SCR-* references → verify target screen exists
if [[ "${FILE_PATH}" =~ ascii-screen/ ]]; then
  NEW_REFS=$(grep -oE '\bSCR-[A-Z0-9]+(?:-[A-Z0-9]+)*\b' "${FILE_PATH}" 2>/dev/null | sort -u || true)
  if [[ -n "${NEW_REFS}" ]]; then
    MODULE_DIR="$(dirname "$(dirname "${FILE_PATH}")")"
    for ref in ${NEW_REFS}; do
      if [[ "${ref}" =~ ^SCR-[0-9]{2}$ ]]; then
        SCR_COUNT=$(find "${MODULE_DIR}/ascii-screen/" -name "*${ref}*.md" 2>/dev/null | wc -l || true)
        if [[ "${SCR_COUNT}" -eq 0 ]]; then
          echo "REF: ${ref} referenced in ${FILE_PATH} but screen file not found in ascii-screen/"
        fi
      fi
    done
  fi
fi

exit 0
