#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_HOME="$(mktemp -d)"
LOG_DIR="${TMP_HOME}/logs"

cleanup() {
  if [[ "${BA_KIT_KEEP_INSTALL_SMOKE_HOME:-0}" == "1" ]]; then
    printf 'Keeping smoke HOME at %s\n' "${TMP_HOME}"
  else
    rm -rf "${TMP_HOME}"
  fi
}
trap cleanup EXIT

mkdir -p "${LOG_DIR}"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

check_file() {
  local path="$1"
  [[ -f "${path}" ]] || fail "missing file: ${path}"
  printf '  OK: %s\n' "${path#"${TMP_HOME}/"}"
}

check_dir() {
  local path="$1"
  [[ -d "${path}" ]] || fail "missing directory: ${path}"
  printf '  OK: %s\n' "${path#"${TMP_HOME}/"}"
}

run_installer() {
  local runtime="$1"
  local log_path="${LOG_DIR}/${runtime}.log"
  shift

  printf 'Running %s installer...\n' "${runtime}"
  if ! HOME="${TMP_HOME}" "$@" >"${log_path}" 2>&1; then
    printf 'Installer failed: %s\n' "${runtime}" >&2
    sed -n '1,220p' "${log_path}" >&2
    exit 1
  fi
}

printf 'Runtime install smoke HOME: %s\n\n' "${TMP_HOME}"

run_installer "claude" bash "${ROOT_DIR}/install.sh"
run_installer "codex" bash "${ROOT_DIR}/scripts/install-codex-ba-kit.sh"
run_installer "antigravity" bash "${ROOT_DIR}/scripts/install-antigravity-ba-kit.sh"

printf '\nSeeding stale managed runtime assets and reinstalling...\n'
mkdir -p \
  "${TMP_HOME}/.claude/skills/ba-stale" \
  "${TMP_HOME}/.codex/skills/ba-stale" \
  "${TMP_HOME}/.gemini/antigravity/knowledge/ba-kit-workflow/artifacts"
printf 'stale\n' > "${TMP_HOME}/.claude/skills/ba-stale/SKILL.md"
printf 'stale\n' > "${TMP_HOME}/.codex/skills/ba-stale/SKILL.md"
printf 'stale\n' > "${TMP_HOME}/.gemini/antigravity/knowledge/ba-kit-workflow/artifacts/stale.md"
cat >> "${TMP_HOME}/.codex/config.toml" <<'EOF'

[agents.requirements-engineer]
description = "stale BA-kit registration"
config_file = "agents/requirements-engineer.toml"
EOF

run_installer "claude-reinstall" bash "${ROOT_DIR}/install.sh"
run_installer "codex-reinstall" bash "${ROOT_DIR}/scripts/install-codex-ba-kit.sh"
run_installer "antigravity-reinstall" bash "${ROOT_DIR}/scripts/install-antigravity-ba-kit.sh"

[[ ! -e "${TMP_HOME}/.claude/skills/ba-stale" ]] || fail "stale Claude skill survived reinstall"
[[ ! -e "${TMP_HOME}/.codex/skills/ba-stale" ]] || fail "stale Codex skill survived reinstall"
[[ ! -e "${TMP_HOME}/.gemini/antigravity/knowledge/ba-kit-workflow/artifacts/stale.md" ]] || fail "stale Antigravity KI artifact survived reinstall"
if [[ "$(grep -c '^\[agents\.requirements-engineer\]$' "${TMP_HOME}/.codex/config.toml")" -ne 1 ]]; then
  sed -n '1,220p' "${TMP_HOME}/.codex/config.toml" >&2
  fail "Codex agent registration was not refreshed cleanly"
fi

printf '\nChecking installed runtime assets...\n'
check_file "${TMP_HOME}/.local/bin/ba-kit"
check_file "${TMP_HOME}/.local/share/ba-kit/installations/claude.env"
check_file "${TMP_HOME}/.local/share/ba-kit/installations/codex.env"
check_file "${TMP_HOME}/.local/share/ba-kit/installations/antigravity.env"

check_file "${TMP_HOME}/.claude/skills/ba-start/SKILL.md"
check_file "${TMP_HOME}/.claude/skills/ba-collab/SKILL.md"
check_file "${TMP_HOME}/.claude/skills/ba-figma-sync/SKILL.md"
check_file "${TMP_HOME}/.claude/skills/ba-start/steps/status.md"
check_file "${TMP_HOME}/.claude/templates/project-home-template.md"
check_file "${TMP_HOME}/.claude/templates/collab-home-template.md"
check_file "${TMP_HOME}/.claude/templates/project-memory-index-template.md"
check_file "${TMP_HOME}/.claude/ba-kit/contract.yaml"
check_file "${TMP_HOME}/.claude/settings.json"
check_file "${TMP_HOME}/.claude/ba-kit/hooks/guardrail-preflight-hook.sh"
check_file "${TMP_HOME}/.claude/ba-kit/hooks/guardrail-audit-hook.sh"
check_file "${TMP_HOME}/.claude/ba-kit/hooks/guardrail-write-scope-hook.sh"
check_file "${TMP_HOME}/.claude/ba-kit/hooks/guardrail-context-preflight-guard-hook.sh"
check_file "${TMP_HOME}/.claude/ba-kit/hooks/guardrail-context-output-guard-hook.sh"
check_file "${TMP_HOME}/.claude/ba-kit/hooks/guardrail-context-audit-hook.sh"

check_file "${TMP_HOME}/.codex/skills/ba-start/SKILL.md"
check_file "${TMP_HOME}/.codex/skills/ba-collab/SKILL.md"
check_file "${TMP_HOME}/.codex/skills/ba-figma-sync/SKILL.md"
check_file "${TMP_HOME}/.codex/skills/ba-start/steps/status.md"
check_file "${TMP_HOME}/.codex/templates/project-home-template.md"
check_file "${TMP_HOME}/.codex/templates/collab-home-template.md"
check_file "${TMP_HOME}/.codex/templates/project-memory-index-template.md"
check_file "${TMP_HOME}/.codex/ba-kit/contract.yaml"
check_file "${TMP_HOME}/.codex/config.toml"
check_file "${TMP_HOME}/.codex/hooks.json"
check_file "${TMP_HOME}/.codex/ba-kit/hooks/guardrail-preflight-hook.sh"
check_file "${TMP_HOME}/.codex/ba-kit/hooks/guardrail-audit-hook.sh"
check_file "${TMP_HOME}/.codex/ba-kit/hooks/guardrail-write-scope-hook.sh"
check_file "${TMP_HOME}/.codex/ba-kit/hooks/guardrail-context-preflight-guard-hook.sh"
check_file "${TMP_HOME}/.codex/ba-kit/hooks/guardrail-context-output-guard-hook.sh"
check_file "${TMP_HOME}/.codex/ba-kit/hooks/guardrail-context-audit-hook.sh"
check_file "${TMP_HOME}/.codex/ba-kit/scripts/guardrail-preflight.py"
check_file "${TMP_HOME}/.codex/ba-kit/scripts/guardrail-audit.py"
check_file "${TMP_HOME}/.codex/ba-kit/scripts/check-write-scope.py"
check_file "${TMP_HOME}/.codex/ba-kit/scripts/validate-index-quality.py"

check_dir "${TMP_HOME}/.gemini/antigravity/knowledge/ba-kit-workflow"
check_file "${TMP_HOME}/.gemini/antigravity/knowledge/ba-kit-workflow/metadata.json"
check_file "${TMP_HOME}/.gemini/antigravity/knowledge/ba-kit-workflow/artifacts/workflow-reference.md"

printf '\nChecking hook registration parity...\n'
python3 - "${TMP_HOME}/.claude/settings.json" "${TMP_HOME}/.codex/hooks.json" <<'PY'
import json
import pathlib
import sys

claude_settings = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
codex_hooks = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))

expected = {
    "UserPromptSubmit": [("", "guardrail-preflight-hook.sh")],
    "Stop": [(None, "guardrail-audit-hook.sh"), (None, "guardrail-context-audit-hook.sh")],
    "PreToolUse": [
        ("Write|Edit", "guardrail-write-scope-hook.sh"),
        ("Read|Glob", "guardrail-context-preflight-guard-hook.sh"),
    ],
    "PostToolUse": [("Bash|Read|Grep|Glob", "guardrail-context-output-guard-hook.sh")],
}

def commands(entry):
    return [hook.get("command", "") for hook in entry.get("hooks", []) if isinstance(hook, dict)]

def assert_hooks(label, cfg):
    hooks = cfg.get("hooks", {})
    for event, requirements in expected.items():
        entries = hooks.get(event, [])
        if not isinstance(entries, list):
            raise SystemExit(f"{label}: {event} hooks missing or not a list")
        for matcher, script in requirements:
            matched = False
            for entry in entries:
                if matcher is not None and entry.get("matcher") != matcher:
                    continue
                if any(script in command for command in commands(entry)):
                    matched = True
                    break
            if not matched:
                matcher_label = "*" if matcher is None else matcher
                raise SystemExit(f"{label}: missing {event} matcher={matcher_label} script={script}")

assert_hooks("claude", claude_settings)
assert_hooks("codex", codex_hooks)
print("  OK: Claude and Codex hook registrations match expected guardrail set")
PY

printf '\nRunning installed CLI doctor...\n'
if ! HOME="${TMP_HOME}" BA_KIT_SKIP_UPDATE_CHECK=1 "${TMP_HOME}/.local/bin/ba-kit" doctor >"${LOG_DIR}/doctor.log" 2>&1; then
  sed -n '1,260p' "${LOG_DIR}/doctor.log" >&2
  fail "installed ba-kit doctor failed"
fi

if grep -q '^\- \[fail\]' "${LOG_DIR}/doctor.log"; then
  sed -n '1,260p' "${LOG_DIR}/doctor.log" >&2
  fail "installed ba-kit doctor reported failures"
fi

printf 'Runtime install smoke passed.\n'
