#!/usr/bin/env bash
# BA-kit License Heartbeat Hook — UserPromptSubmit
# Runs before every prompt to verify license + send enterprise heartbeat.
# Writes BLOCK file if license invalid (skills read this as hard gate).

set -euo pipefail

HEARTBEAT_SCRIPT="${HOME}/.claude/ba-kit/scripts/license-heartbeat.sh"
BLOCK_FILE="${HOME}/.claude/ba-kit/state/license-blocked.txt"

if [[ ! -f "${HEARTBEAT_SCRIPT}" ]]; then
  exit 0  # Not installed yet, silent
fi

# ── Detect BA-kit command from user prompt ───────────────────────────
detect_command() {
  local prompt="${CLAUDE_PROMPT:-}"

  # ba-start with explicit subcommand: /ba-start stories → ba-start:stories
  if echo "${prompt}" | grep -qiE '\bba-start\s+(intake|frd|stories|srs|package|status|next)\b'; then
    local sub
    sub="$(echo "${prompt}" | grep -oiE '\bba-start\s+(intake|frd|stories|srs|package|status|next)\b' | head -1 | tr '[:upper:]' '[:lower:]')"
    echo "${sub}"  # e.g. "ba-start stories"
    return 0
  fi

  # ba-start without explicit subcommand
  if echo "${prompt}" | grep -qiE '\b(ba-start)\b'; then
    echo "ba-start"
    return 0
  fi

  # Natural language → ba-start subcommand mapping
  if echo "${prompt}" | grep -qiE '\b(phân tích|thu thập|intake|đầu vào)\b'; then
    echo "ba-start:intake"
    return 0
  fi
  if echo "${prompt}" | grep -qiE '\b(tạo|viết|làm|build|create|generate)\b.*\b(FRD|functional requirements|yêu cầu chức năng)\b'; then
    echo "ba-start:frd"
    return 0
  fi
  if echo "${prompt}" | grep -qiE '\b(tạo|viết|làm|build|create|generate)\b.*\b(user stories|stories|câu chuyện)\b'; then
    echo "ba-start:stories"
    return 0
  fi
  if echo "${prompt}" | grep -qiE '\b(tạo|viết|làm|build|create|generate)\b.*\b(SRS|software requirements|đặc tả)\b'; then
    echo "ba-start:srs"
    return 0
  fi
  if echo "${prompt}" | grep -qiE '\b(đóng gói|bàn giao|handoff|package|xuất gói|export)\b'; then
    echo "ba-start:package"
    return 0
  fi

  # Other BA-kit commands
  if echo "${prompt}" | grep -qiE '\b(ba-next|ba-impact|ba-do|ba-collab|ba-figma-sync|ba-stitch-sync|ba-notion|ba-kit-update|ba-qc-export|ba-content-audit)\b'; then
    echo "${prompt}" | grep -oiE '\b(ba-next|ba-impact|ba-do|ba-collab|ba-figma-sync|ba-stitch-sync|ba-notion|ba-kit-update|ba-qc-export|ba-content-audit)\b' | head -1 | tr '[:upper:]' '[:lower:]'
    return 0
  fi

  echo "ba-kit"
  return 0
}

# ── Detect project slug from CWD ─────────────────────────────────────
detect_project_slug() {
  local dir="${PWD}"

  # If inside a plans/{slug}-{date} directory, extract slug
  if [[ "${dir}" =~ /plans/([^/]+)-[0-9]{6}-[0-9]{4} ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi

  # Fallback: use the current directory name
  echo "$(basename "${dir}")"
  return 0
}

export BA_KIT_COMMAND
BA_KIT_COMMAND="$(detect_command)"
export BA_KIT_PROJECT_SLUG
BA_KIT_PROJECT_SLUG="$(detect_project_slug)"
export BA_KIT_VERSION
BA_KIT_VERSION="${BA_KIT_VERSION:-unknown}"

OUTPUT=$(bash "${HEARTBEAT_SCRIPT}" 2>&1) || HEARTBEAT_EXIT=$?

if [[ ${HEARTBEAT_EXIT:-0} -eq 1 ]]; then
  echo ""
  echo "⛔️  BA-KIT LICENSE CHECK FAILED"
  echo "${OUTPUT}"
  echo ""
  echo "Run: ba-kit reauth"
  echo ""
else
  # Clear any stale block file
  rm -f "${BLOCK_FILE}"
fi

exit 0  # Hook itself never blocks Claude Code
