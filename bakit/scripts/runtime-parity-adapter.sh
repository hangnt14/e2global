#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  runtime-parity-adapter.sh <claude|codex|antigravity> <fixture.md> <golden.md> <output.json>

Exit codes:
  0  Runtime produced an output artifact
  1  Adapter execution failed
  2  Runtime is pending/manual and no certification artifact exists
EOF
}

json_field() {
  local json_path="$1"
  local field_path="$2"

  python3 - "$json_path" "$field_path" <<'PY'
import json
import sys

path = sys.argv[1]
field_path = sys.argv[2].split(".")
value = json.loads(open(path, encoding="utf-8").read())
for part in field_path:
    if isinstance(value, dict):
        value = value.get(part, "")
    else:
        value = ""
        break
if isinstance(value, bool):
    print("true" if value else "false")
elif isinstance(value, (list, dict)):
    print(json.dumps(value, ensure_ascii=False))
elif value is None:
    print("")
else:
    print(value)
PY
}

guardrail_enabled() {
  [[ -n "${BA_KIT_GUARDRAIL_COMMAND:-}" ]] || [[ -n "${BA_KIT_GUARDRAIL_SLUG:-}" ]] || [[ -n "${BA_KIT_GUARDRAIL_DATE:-}" ]]
}

require_guardrail_inputs() {
  if ! guardrail_enabled; then
    return 0
  fi

  local missing=()
  [[ -n "${BA_KIT_GUARDRAIL_COMMAND:-}" ]] || missing+=("BA_KIT_GUARDRAIL_COMMAND")
  [[ -n "${BA_KIT_GUARDRAIL_SLUG:-}" ]] || missing+=("BA_KIT_GUARDRAIL_SLUG")
  [[ -n "${BA_KIT_GUARDRAIL_DATE:-}" ]] || missing+=("BA_KIT_GUARDRAIL_DATE")

  if [[ "${#missing[@]}" -gt 0 ]]; then
    echo "Guardrail preflight requires: ${missing[*]}" >&2
    exit 1
  fi
}

append_guardrail_prompt() {
  local preflight_path="$1"
  local excerpt_path="$2"

  python3 - "${PROMPT_PATH}" "${preflight_path}" "${excerpt_path}" <<'PY'
import json
import pathlib
import sys

prompt_path = pathlib.Path(sys.argv[1])
preflight_path = pathlib.Path(sys.argv[2])
excerpt_path = sys.argv[3].strip()
preflight = json.loads(preflight_path.read_text(encoding="utf-8"))

status = preflight.get("status", "")
command = preflight.get("command", "")
resolved_slug = preflight.get("resolved_slug", "")
message = preflight.get("message", "").strip()

# Determine output mode: probe / delta / full
# probe: block or no index state available
# delta: ok/warn with current index and excerpt
# full: escalation path or no current index
indexes = preflight.get("indexes", {})
has_current_index = any(
    v.get("state") == "current" for v in indexes.values() if isinstance(v, dict)
)
action_guardrail = preflight.get("action_guardrail", {})
canonical_state_summary = preflight.get("canonical_state_summary", "").strip()
canonical_next_command = preflight.get("canonical_next_command", "").strip()
deny_reads = preflight.get("deny_reads", [])

if status == "block":
    output_mode = "probe"
elif has_current_index and not canonical_state_summary:
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

    if excerpt_path:
        lines.extend([
            "EXCERPTS:",
            f"- {excerpt_path}",
        ])

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
    if deny_reads:
        lines.append("DENY_READS:")
        lines.extend(f"- {item}" for item in deny_reads)

    if canonical_state_summary:
        lines.extend([
            "CANONICAL_STATE:",
            f"- {canonical_state_summary}",
        ])

    if canonical_next_command:
        lines.extend([
            "CANONICAL_NEXT_COMMAND:",
            f"- {canonical_next_command}",
        ])

    refresh_command = preflight.get("refresh_command", "").strip()
    if refresh_command and status == "block":
        lines.append(f"REFRESH_COMMAND: {refresh_command}")

lines.append(
    f"If a broader read is necessary, emit exactly: READ_ESCALATION: {command} read <path> due to <reason>."
)

with prompt_path.open("a", encoding="utf-8") as handle:
    handle.write("\n".join(lines) + "\n")
PY
}

allow_excerpt_read() {
  local preflight_path="$1"
  local excerpt_path="$2"

  [[ -n "${excerpt_path}" ]] || return 0

  python3 - "${preflight_path}" "${excerpt_path}" <<'PY'
import json
import pathlib
import sys

preflight_path = pathlib.Path(sys.argv[1])
excerpt_path = sys.argv[2].strip()
data = json.loads(preflight_path.read_text(encoding="utf-8"))
allow_reads = data.setdefault("allow_reads", [])
if excerpt_path and excerpt_path not in allow_reads:
    allow_reads.append(excerpt_path)
preflight_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
}

block_on_excerpt_failure() {
  local preflight_path="$1"
  local reason="$2"

  python3 - "${preflight_path}" "${reason}" "${BA_KIT_GUARDRAIL_COMMAND}" "${BA_KIT_GUARDRAIL_SLUG}" <<'PY'
import json
import pathlib
import sys

preflight_path = pathlib.Path(sys.argv[1])
reason = sys.argv[2]
command = sys.argv[3]
slug = sys.argv[4]
refresh_command = f"ba-start backbone --slug {slug}"

data = json.loads(preflight_path.read_text(encoding="utf-8"))
data["status"] = "block"
data["reason"] = reason
data["refresh_command"] = refresh_command
data["message"] = f"GUARDRAIL_BLOCK: cmd={command} reason={reason} refresh={refresh_command}"
preflight_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
}

build_guardrail_excerpt() {
  local preflight_path="$1"
  local excerpt_dir="$2"
  local excerpt_plan
  local preflight_status

  excerpt_plan="$(json_field "${preflight_path}" "excerpt_plan")"
  preflight_status="$(json_field "${preflight_path}" "status")"
  if [[ "${excerpt_plan}" != "backbone_by_module" ]] || [[ "${preflight_status}" != "ok" ]]; then
    return 0
  fi

  local args=(
    python3 "${SCRIPT_DIR}/guardrail-build-excerpts.py"
    --repo "${REPO_ROOT}"
    --index-key backbone_index
    --slug "${BA_KIT_GUARDRAIL_SLUG}"
    --date "${BA_KIT_GUARDRAIL_DATE}"
    --output-dir "${excerpt_dir}"
  )

  if [[ -n "${BA_KIT_GUARDRAIL_MODULE:-}" ]]; then
    args+=(--module "${BA_KIT_GUARDRAIL_MODULE}")
  fi
  if [[ -n "${BA_KIT_GUARDRAIL_FEATURE:-}" ]]; then
    args+=(--feature "${BA_KIT_GUARDRAIL_FEATURE}")
  fi
  if [[ -n "${BA_KIT_GUARDRAIL_TRACE_ID:-}" ]]; then
    args+=(--trace-id "${BA_KIT_GUARDRAIL_TRACE_ID}")
  fi
  if [[ -n "${BA_KIT_GUARDRAIL_HEADING:-}" ]]; then
    args+=(--heading "${BA_KIT_GUARDRAIL_HEADING}")
  fi

  local manifest_path="${excerpt_dir}/excerpt-manifest.json"
  local stderr_path="${excerpt_dir}/excerpt-error.log"
  if ! "${args[@]}" >"${manifest_path}" 2>"${stderr_path}"; then
    cat "${stderr_path}" >&2 || true
    rm -f "${manifest_path}"
    return 1
  fi

  local excerpt_path
  excerpt_path="$(json_field "${manifest_path}" "excerpt_path")"
  if [[ -z "${excerpt_path}" ]]; then
    echo "Guardrail excerpt build produced no excerpt path" >&2
    return 1
  fi

  printf '%s\n' "${excerpt_path}"
}

run_guardrail_preflight() {
  if ! guardrail_enabled; then
    return 1
  fi

  local preflight_path="$1"
  local excerpt_dir="$2"
  local excerpt_path=""
  local args=(
    python3 "${SCRIPT_DIR}/guardrail-preflight.py"
    --repo "${REPO_ROOT}"
    --command "${BA_KIT_GUARDRAIL_COMMAND}"
    --slug "${BA_KIT_GUARDRAIL_SLUG}"
    --date "${BA_KIT_GUARDRAIL_DATE}"
    --output "${preflight_path}"
  )

  if [[ -n "${BA_KIT_GUARDRAIL_MODULE:-}" ]]; then
    args+=(--module "${BA_KIT_GUARDRAIL_MODULE}")
  fi
  if [[ -n "${BA_KIT_GUARDRAIL_FEATURE:-}" ]]; then
    args+=(--feature "${BA_KIT_GUARDRAIL_FEATURE}")
  fi
  if [[ -n "${BA_KIT_GUARDRAIL_TRACE_ID:-}" ]]; then
    args+=(--trace-id "${BA_KIT_GUARDRAIL_TRACE_ID}")
  fi
  if [[ -n "${BA_KIT_GUARDRAIL_HEADING:-}" ]]; then
    args+=(--heading "${BA_KIT_GUARDRAIL_HEADING}")
  fi
  if [[ "${BA_KIT_GUARDRAIL_ALLOW_ESCALATION:-0}" == "1" ]]; then
    args+=(--allow-escalation)
  fi

  "${args[@]}" >/dev/null

  if [[ "$(json_field "${preflight_path}" "status")" == "block" ]]; then
    cp "${preflight_path}" "${OUTPUT_PATH}"
    echo "$(json_field "${preflight_path}" "message")" >&2
    return 2
  fi

  if ! excerpt_path="$(build_guardrail_excerpt "${preflight_path}" "${excerpt_dir}")"; then
    block_on_excerpt_failure "${preflight_path}" "excerpt_build_failed"
    cp "${preflight_path}" "${OUTPUT_PATH}"
    echo "$(json_field "${preflight_path}" "message")" >&2
    return 2
  fi
  allow_excerpt_read "${preflight_path}" "${excerpt_path}"
  append_guardrail_prompt "${preflight_path}" "${excerpt_path}"
  return 0
}

run_guardrail_audit() {
  local preflight_path="$1"
  local audit_path="$2"

  if [[ -z "${BA_KIT_GUARDRAIL_READS_MANIFEST:-}" ]]; then
    return 0
  fi

  python3 "${SCRIPT_DIR}/guardrail-audit.py" \
    --preflight "${preflight_path}" \
    --reads-manifest "${BA_KIT_GUARDRAIL_READS_MANIFEST}" \
    --output "${audit_path}" >/dev/null

  case "$(json_field "${audit_path}" "status")" in
    fail)
      echo "$(json_field "${audit_path}" "message")" >&2
      return 1
      ;;
    warn)
      echo "$(json_field "${audit_path}" "message")" >&2
      ;;
  esac

  return 0
}

if [[ "$#" -ne 4 ]]; then
  usage >&2
  exit 1
fi

RUNTIME="$1"
FIXTURE_PATH="$2"
GOLDEN_PATH="$3"
OUTPUT_PATH="$4"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FIXTURE_ID="$(basename "${FIXTURE_PATH}" | sed 's/-.*//')"
PROMPT_PATH="$(mktemp "${TMPDIR:-/tmp}/ba-kit-parity-prompt.XXXXXX")"
RAW_PATH="$(mktemp "${TMPDIR:-/tmp}/ba-kit-parity-raw.XXXXXX")"
GUARDRAIL_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ba-kit-guardrail.XXXXXX")"
PREFLIGHT_PATH="${GUARDRAIL_DIR}/preflight.json"
AUDIT_PATH="${GUARDRAIL_DIR}/audit.json"

cleanup() {
  rm -f "${PROMPT_PATH}" "${RAW_PATH}"
  rm -rf "${GUARDRAIL_DIR}"
}
trap cleanup EXIT

require_guardrail_inputs

python3 "${SCRIPT_DIR}/runtime-parity-normalize.py" prompt \
  --fixture "${FIXTURE_PATH}" \
  --golden "${GOLDEN_PATH}" >"${PROMPT_PATH}"

if run_guardrail_preflight "${PREFLIGHT_PATH}" "${GUARDRAIL_DIR}"; then
  :
elif [[ "$?" -eq 2 ]]; then
  exit 0
fi

case "${RUNTIME}" in
  claude)
    if ! command -v claude >/dev/null 2>&1; then
      echo "Claude Code CLI not found on PATH" >&2
      exit 2
    fi
    (
      cd "${REPO_ROOT}"
      claude -p \
        --no-session-persistence \
        --permission-mode dontAsk \
        --tools Read,Grep,Glob \
        --output-format text \
        "$(cat "${PROMPT_PATH}")" >"${OUTPUT_PATH}" </dev/null
    )
    ;;
  codex)
    if ! command -v codex >/dev/null 2>&1; then
      echo "Codex CLI not found on PATH" >&2
      exit 2
    fi
    codex exec \
      -C "${REPO_ROOT}" \
      --sandbox read-only \
      --ephemeral \
      --output-last-message "${OUTPUT_PATH}" \
      "$(cat "${PROMPT_PATH}")" >"${RAW_PATH}" </dev/null
    ;;
  antigravity)
    CERT_DIR="${BA_KIT_ANTIGRAVITY_CERT_DIR:-${REPO_ROOT}/tests/runtime-parity/certifications/antigravity}"
    CERT_PATH="${CERT_DIR}/${FIXTURE_ID}.json"
    if [[ ! -f "${CERT_PATH}" ]]; then
      echo "Antigravity manual certification missing: ${CERT_PATH}" >&2
      exit 2
    fi
    cp "${CERT_PATH}" "${OUTPUT_PATH}"
    ;;
  *)
    echo "Unsupported runtime adapter: ${RUNTIME}" >&2
    usage >&2
    exit 1
    ;;
esac

if [[ ! -s "${OUTPUT_PATH}" ]]; then
  echo "Runtime adapter produced no output: ${RUNTIME} ${FIXTURE_ID}" >&2
  exit 1
fi

if [[ -f "${PREFLIGHT_PATH}" ]]; then
  run_guardrail_audit "${PREFLIGHT_PATH}" "${AUDIT_PATH}"
fi
