#!/usr/bin/env bash
# BA-kit License Heartbeat — validates license + tracks usage
# Exit codes: 0=ok, 1=blocked

set -euo pipefail

LICENSE_FILE="${HOME}/.claude/ba-kit/.license"
BLOCK_FILE="${HOME}/.claude/ba-kit/state/license-blocked.txt"
LICENSE_SERVER="https://license.bakit.ai.vn"
DEBOUNCE_SECONDS=120       # 2 minutes between heartbeats (near-real-time)
TOKEN_REFRESH_SECONDS=82800 # 23 hours between re-verifications
HEARTBEAT_TIMEOUT=3         # seconds
MAX_OFFLINE_DAYS=7

# ── Helpers ──────────────────────────────────────────────────────────

read_license_field() {
  python3 -c "import json,pathlib; d=json.loads(pathlib.Path('${LICENSE_FILE}').read_text()); print(d.get('$1',''))" 2>/dev/null || echo ""
}

write_license_fields() {
  python3 -c "
import json, pathlib
lic = json.loads(pathlib.Path('${LICENSE_FILE}').read_text())
lic.update($1)
pathlib.Path('${LICENSE_FILE}').write_text(json.dumps(lic, indent=2))
" 2>/dev/null || true
}

deobfuscate_token() {
  # ponytail: base64 decode for now
  python3 -c "
import json, base64, pathlib
lic = json.loads(pathlib.Path('${LICENSE_FILE}').read_text())
print(base64.b64decode(lic['token_obfuscated']).decode())
" 2>/dev/null || echo ""
}

write_block() {
  local msg="$1"
  mkdir -p "$(dirname "${BLOCK_FILE}")"
  echo "${msg}" > "${BLOCK_FILE}"
  echo "BA_KIT_LICENSE_BLOCK: ${msg}" >&2
}

clear_block() {
  rm -f "${BLOCK_FILE}"
}

# ── Detect BA-kit context ────────────────────────────────────────────

detect_plan_dir() {
  local dir="${PWD}"
  while [[ "${dir}" != "/" ]]; do
    if [[ "${dir}" =~ /plans/[^/]+-[0-9]{6}-[0-9]{4}$ ]]; then
      printf '%s\n' "${dir}"
      return 0
    fi
    [[ "${dir}" == "${HOME}" ]] && break
    dir="$(dirname "${dir}")"
  done
  return 1
}

detect_ba_context() {
  printf '%s\n' "${PWD}"
  return 0
}

# ── Token tracking from JSONL ─────────────────────────────────────

# Returns: token_delta model_name session_id (space-separated)
compute_token_delta() {
  local plan_dir="$1"
  local last_known="$2"

  python3 -c "
import json, pathlib, os, sys

plan_dir = '${plan_dir}'
last_known = int(${last_known:-0})

# Find all JSONL files under ~/.claude/projects/
projects_dir = os.path.expanduser('~/.claude/projects')
total_tokens = 0
model_name = ''
session_id = ''

if os.path.isdir(projects_dir):
    for root, dirs, files in os.walk(projects_dir):
        for fname in files:
            if fname.endswith('.jsonl'):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath) as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                entry = json.loads(line)
                                # Support both old format (top-level usage) and new format (message.usage)
                                if entry.get('type') == 'assistant' and isinstance(entry.get('message'), dict):
                                    usage = entry['message'].get('usage', {})
                                    total_tokens += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                                    model_name = entry['message'].get('model', model_name)
                                    session_id = entry.get('sessionId', session_id)
                                else:
                                    usage = entry.get('usage', {})
                                    total_tokens += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                                    model_name = entry.get('model', model_name)
                                    session_id = entry.get('session_id', session_id)
                            except (json.JSONDecodeError, KeyError):
                                continue
                except (IOError, OSError):
                    continue

delta = max(0, total_tokens - last_known)
print(f'{delta} {model_name} {session_id}')
" 2>/dev/null || echo "0  "
}

# ── Enterprise heartbeat ────────────────────────────────────────────

send_enterprise_heartbeat() {
  local install_id="$1"
  local github_user="$2"
  local org_url="$3"
  local org_token="$4"
  local plan_dir="$5"

  local last_known_total
  last_known_total="$(read_license_field "last_known_total")"

  local token_info
  token_info="$(compute_token_delta "${plan_dir}" "${last_known_total}")"
  local token_delta="${token_info%% *}"
  local rest="${token_info#* }"
  local model_name="${rest%% *}"
  local session_id="${rest##* }"

  local now_iso
  now_iso="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local skill project_slug version
  skill="${BA_KIT_COMMAND:-unknown}"
  project_slug="${BA_KIT_PROJECT_SLUG:-unknown}"
  version="${BA_KIT_VERSION:-unknown}"

  # Build payload via temp file — token passed via stdin, not argv
  local payload_file
  payload_file="$(mktemp)"
  echo -n "${org_token}" | python3 -c "
import json, sys
org_token = sys.stdin.read().strip()
with open('${payload_file}', 'w') as f:
    json.dump({
        'install_id': '${install_id}',
        'github_user': '${github_user}',
        'org_token': org_token,
        'skill': '${skill}',
        'project_slug': '${project_slug}',
        'version': '${version}',
        'token_count': int('${token_delta}'),
        'model_name': '${model_name}',
        'session_id': '${session_id}',
        'timestamp': '${now_iso}'
    }, f)
" 2>/dev/null

  curl -sf -m 5 -X POST "${org_url}/org-heartbeat" \
    -H "Content-Type: application/json" \
    -H "User-Agent: ba-kit-license/1.0" \
    -d "@${payload_file}" 2>/dev/null && {
    # Update last_known_total on success
    local current_total
    current_total="$((last_known_total + token_delta))"
    write_license_fields "{\"last_known_total\": ${current_total}}"
  }
  rm -f "${payload_file}"
}

# ── Main ─────────────────────────────────────────────────────────────

main() {
  detect_ba_context >/dev/null 2>&1 || return 0

  # No license file?
  if [[ ! -f "${LICENSE_FILE}" ]]; then
    return 0  # Allow proceed (grace period)
  fi

  # Debounce
  local last_val
  last_val="$(read_license_field "last_validated")"
  if [[ -n "${last_val}" ]] && [[ "${last_val}" != "null" ]] && [[ "${last_val}" != "None" ]]; then
    local now
    now="$(date +%s)"
    local last_val_epoch
    last_val_epoch="$(python3 -c "
print(int('${last_val}'))
" 2>/dev/null || echo "0")"
    if [[ $((now - last_val_epoch)) -lt ${DEBOUNCE_SECONDS} ]]; then
      return 0  # Recent validation, skip
    fi
  fi

  local install_id
  install_id="$(read_license_field "install_id")"
  [[ -z "${install_id}" ]] && return 0

  # Determine if token refresh needed
  local include_token="false"
  local last_verified
  last_verified="$(read_license_field "last_verified")"
  if [[ -n "${last_verified}" ]] && [[ "${last_verified}" != "null" ]] && [[ "${last_verified}" != "None" ]]; then
    local last_v_epoch now
    now="$(date +%s)"
    last_v_epoch="$(python3 -c "
from datetime import datetime
ts = '${last_verified}'.replace('Z', '+00:00')
print(int(datetime.fromisoformat(ts).timestamp()))
" 2>/dev/null || echo "0")"
    if [[ $((now - last_v_epoch)) -gt ${TOKEN_REFRESH_SECONDS} ]]; then
      include_token="true"
    fi
  else
    include_token="true"
  fi

  # Build payload — only install_id + optional github_token for /validate
  local payload
  if [[ "${include_token}" == "true" ]]; then
    local token
    token="$(deobfuscate_token)"
    if [[ -z "${token}" ]]; then
      write_block "Cannot read license token. Re-run: ba-kit reauth"
      return 1
    fi
    payload_file="$(mktemp)"
    echo -n "${token}" | python3 -c "
import json, sys
token = sys.stdin.read().strip()
with open('${payload_file}', 'w') as f:
    json.dump({'install_id': '${install_id}', 'github_token': token}, f)
"
  else
    payload_file="$(mktemp)"
    python3 -c "
import json
with open('${payload_file}', 'w') as f:
    json.dump({'install_id': '${install_id}'}, f)
"
  fi

  # Send validate request
  local resp status
  resp="$(curl -sf -m "${HEARTBEAT_TIMEOUT}" \
    -X POST "${LICENSE_SERVER}/validate" \
    -H "Content-Type: application/json" \
    -H "User-Agent: ba-kit-license/1.0" \
    -d "@${payload_file}" 2>/dev/null || echo '{"status":"network_error"}')"
  rm -f "${payload_file}"

  status="$(echo "${resp}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','error'))" 2>/dev/null || echo "error")"

  case "${status}" in
    ok)
      local now_epoch github_user
      now_epoch="$(date +%s)"
      github_user="$(echo "${resp}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('github_user',''))" 2>/dev/null || echo "")"
      write_license_fields "{\"last_validated\": ${now_epoch}, \"offline_count\": 0}"
      clear_block

      # Enterprise heartbeat (if org configured)
      local org_url org_token plan_dir
      org_url="$(read_license_field "org_url")"
      org_token="$(read_license_field "org_token")"
      plan_dir="$(detect_ba_context 2>/dev/null || echo "")"
      if [[ -n "${org_url}" ]] && [[ -n "${org_token}" ]]; then
        send_enterprise_heartbeat "${install_id}" "${github_user}" "${org_url}" "${org_token}" "${plan_dir}" &
        # Fire-and-forget: don't block license validation waiting for enterprise
      fi
      return 0
      ;;
    denied|revoked)
      local reason
      reason="$(echo "${resp}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('reason','unknown'))" 2>/dev/null || echo "unknown")"
      write_block "GitHub access to BA-kit repository has been revoked (${reason}). Contact admin to regain access. Run: ba-kit reauth"
      return 1
      ;;
    *)
      # Network error — increment offline counter
      local offline_count
      offline_count="$(read_license_field "offline_count")"
      offline_count=$((offline_count + 1))
      write_license_fields "{\"offline_count\": ${offline_count}}"
      if [[ ${offline_count} -ge ${MAX_OFFLINE_DAYS} ]]; then
        write_block "BA-kit requires internet to verify license after ${MAX_OFFLINE_DAYS} days offline. Please connect and retry."
        return 1
      fi
      return 0
      ;;
  esac
}

main "$@"
