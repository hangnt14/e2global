#!/usr/bin/env bash
# BA-kit License Registration — GitHub Device Flow OAuth
# Usage: bash license-register.sh
# Exit codes: 0=success, 1=user_skip, 2=access_denied, 3=network_error

set -euo pipefail

# ── Config ───────────────────────────────────────────────────────────
GITHUB_CLIENT_ID="Ov23linHDKO51UHCCaOM"
LICENSE_SERVER="https://license.bakit.ai.vn"
LICENSE_FILE="${HOME}/.claude/ba-kit/.license"
LICENSE_DIR="$(dirname "${LICENSE_FILE}")"
GITHUB_DEVICE_URL="https://github.com/login/device/code"
GITHUB_ACCESS_TOKEN_URL="https://github.com/login/oauth/access_token"
POLL_INTERVAL=5
POLL_TIMEOUT=300  # 5 minutes

# ── Helpers ──────────────────────────────────────────────────────────

log()  { echo "  $*" >&2; }
info() { echo "  ℹ️  $*" >&2; }
ok()   { echo "  ✅ $*" >&2; }
err()  { echo "  ❌ $*" >&2; }

check_prereqs() {
  for cmd in curl python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      err "Missing required command: $cmd"
      exit 3
    fi
  done
}

generate_install_id() {
  # Generate UUID v4
  python3 -c "import uuid; print(str(uuid.uuid4()))"
}

# ── Step 1: Request device code from GitHub ──────────────────────────

request_device_code() {
  log "Waiting GitHub response..."

  local resp
  resp="$(curl -s -X POST "${GITHUB_DEVICE_URL}" \
    -H "Accept: application/json" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "User-Agent: ba-kit-license/1.0" \
    --data-urlencode "client_id=${GITHUB_CLIENT_ID}" \
    --data-urlencode "scope=repo,read:user" 2>/dev/null)" || {
      err "Can't connect to GitHub."
      return 3
    }

  # Parse response via temp file (avoids shell quoting nightmares)
  local tmp_json
  tmp_json="$(mktemp)"
  echo "${resp}" > "${tmp_json}"

  DEVICE_CODE="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('device_code',''))" 2>/dev/null)"
  USER_CODE="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('user_code',''))" 2>/dev/null)"
  VERIFICATION_URI="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('verification_uri',''))" 2>/dev/null)"
  INTERVAL="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('interval','5'))" 2>/dev/null)"
  rm -f "${tmp_json}"

  if [[ -z "${DEVICE_CODE}" ]] || [[ -z "${USER_CODE}" ]]; then
    err "GitHub returned unexpected response."
    return 3
  fi

  ok "Got device grant from GitHub"

  # Auto-open browser
  local open_cmd=""
  if command -v open >/dev/null 2>&1; then
    open_cmd="open"           # macOS
  elif command -v xdg-open >/dev/null 2>&1; then
    open_cmd="xdg-open"       # Linux
  elif command -v start >/dev/null 2>&1; then
    open_cmd="start"          # Windows
  fi

  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  🔐 BA-kit cần xác nhận tài khoản GitHub của bạn."
  echo ""
  echo "  Mã xác nhận: ${USER_CODE}"
  echo ""
  echo "  Trình duyệt sẽ tự động mở..."
  echo "  Nếu không, hãy mở: ${VERIFICATION_URI}"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  if [[ -n "${open_cmd}" ]]; then
    "${open_cmd}" "${VERIFICATION_URI}" >/dev/null 2>&1 || true
  fi

  return 0
}

# ── Step 2: Poll for access token ────────────────────────────────────

poll_for_token() {
  local elapsed=0
  local interval="${INTERVAL:-5}"

  while [[ ${elapsed} -lt ${POLL_TIMEOUT} ]]; do
    sleep "${interval}"
    elapsed=$((elapsed + interval))

    local resp
    resp="$(curl -s -X POST "${GITHUB_ACCESS_TOKEN_URL}" \
      -H "Accept: application/json" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -H "User-Agent: ba-kit-license/1.0" \
      --data-urlencode "client_id=${GITHUB_CLIENT_ID}" \
      --data-urlencode "device_code=${DEVICE_CODE}" \
      --data-urlencode "grant_type=urn:ietf:params:oauth:grant-type:device_code" 2>/dev/null)" || continue

    local tmp_json error
    tmp_json="$(mktemp)"
    echo "${resp}" > "${tmp_json}"
    error="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('error',''))" 2>/dev/null || echo "")"

    case "${error}" in
      "authorization_pending")
        rm -f "${tmp_json}"
        continue
        ;;
      "slow_down")
        interval=$((interval + 5))
        rm -f "${tmp_json}"
        continue
        ;;
      "expired_token")
        rm -f "${tmp_json}"
        err "Mã xác nhận đã hết hạn. Vui lòng thử lại."
        return 3
        ;;
      "access_denied")
        rm -f "${tmp_json}"
        err "Bạn đã từ chối cấp quyền trên GitHub."
        return 2
        ;;
      "")
        ACCESS_TOKEN="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('access_token',''))" 2>/dev/null)"
        rm -f "${tmp_json}"
        if [[ -n "${ACCESS_TOKEN}" ]]; then
          ok "Đã xác nhận GitHub thành công"
          return 0
        fi
        ;;
      *)
        if [[ -n "${error}" ]]; then
          rm -f "${tmp_json}"
          err "GitHub báo lỗi: ${error}"
          return 3
        fi
        ;;
    esac
  done

  err "Hết thời gian chờ xác nhận."
  return 3
}

# ── Step 3: Register with license server ─────────────────────────────

register_with_server() {
  local install_id="$1"
  local github_token="$2"

  log "Verifying GitHub access with license server..."

  # Build JSON payload via temp file — token passed via stdin, not argv
  local payload_file
  payload_file="$(mktemp)"
  echo -n "${github_token}" | python3 -c "
import json, sys
token = sys.stdin.read().strip()
with open('${payload_file}', 'w') as f:
    json.dump({'install_id': '${install_id}', 'github_token': token}, f)
"

  local resp
  resp="$(curl -s -X POST "${LICENSE_SERVER}/register" \
    -H "Content-Type: application/json" \
    -H "User-Agent: ba-kit-license/1.0" \
    -d "@${payload_file}" 2>/dev/null)" || {
      rm -f "${payload_file}"
      err "Can't connect to license server: ${LICENSE_SERVER}"
      return 3
    }
  rm -f "${payload_file}"

  local tmp_json status
  tmp_json="$(mktemp)"
  echo "${resp}" > "${tmp_json}"
  status="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('status','error'))" 2>/dev/null || echo "error")"

  case "${status}" in
    ok)
      local github_user
      github_user="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('github_user','unknown'))" 2>/dev/null)"
      rm -f "${tmp_json}"
      ok "Đã kết nối với máy chủ bản quyền (tài khoản @${github_user})"

      save_license "${install_id}" "${github_user}" "${github_token}"
      register_with_enterprise "${install_id}" "${github_user}"
      return 0
      ;;
    denied)
      local reason github_user
      reason="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('reason','unknown'))" 2>/dev/null)"
      github_user="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('github_user','unknown'))" 2>/dev/null)"
      rm -f "${tmp_json}"
      echo ""
      echo "═══════════════════════════════════════════════════════════════"
      echo "  ⛔️  Không được cấp quyền"
      echo ""
      echo "  Tài khoản GitHub @${github_user} chưa được cấp quyền"
      echo "  truy cập vào kho mã nguồn BA-kit (bakit-org/bakit)."
      echo ""
      echo "  Lý do: ${reason}"
      echo ""
      echo "  Để dùng BA-kit, bạn cần quyền cộng tác viên tại:"
      echo "  https://github.com/bakit-org/bakit"
      echo ""
      echo "  Liên hệ quản lý dự án để được cấp quyền."
      echo "═══════════════════════════════════════════════════════════════"
      echo ""
      return 2
      ;;
    *)
      err "Máy chủ bản quyền trả về phản hồi không mong đợi."
      rm -f "${tmp_json}"
      return 3
      ;;
  esac
}

# ── Step 4: Save license file ────────────────────────────────────────

save_license() {
  local install_id="$1"
  local github_user="$2"
  local github_token="$3"

  mkdir -p "${LICENSE_DIR}"
  chmod 700 "${LICENSE_DIR}"

  # Obfuscate token — pass via stdin, never on command line
  local token_obfuscated
  token_obfuscated="$(echo -n "${github_token}" | python3 -c "
import sys, base64
print(base64.b64encode(sys.stdin.read().encode()).decode())
")"

  local now
  now="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  # Build license JSON with optional org fields
  python3 -c "
import json, pathlib, os
lic = {
    'install_id': '${install_id}',
    'github_user': '${github_user}',
    'token_obfuscated': '${token_obfuscated}',
    'registered_at': '${now}',
    'last_validated': None,
    'last_verified': '${now}',
    'offline_count': 0,
    'server_url': '${LICENSE_SERVER}'
}
org_url = os.environ.get('ORG_URL', '')
org_token = os.environ.get('ORG_TOKEN', '')
if org_url:
    lic['org_url'] = org_url
if org_token:
    lic['org_token'] = org_token
pathlib.Path('${LICENSE_FILE}').write_text(json.dumps(lic, indent=2))
"

  chmod 600 "${LICENSE_FILE}"
  ok "Đã lưu thông tin bản quyền"
}

# ── Step 5: Register with enterprise server (nếu có) ────────────────

register_with_enterprise() {
  local install_id="$1"
  local github_user="$2"

  local org_url="${ORG_URL:-}"
  local org_token="${ORG_TOKEN:-}"

  if [[ -z "${org_url}" ]] || [[ -z "${org_token}" ]]; then
    return 0  # Không có thông tin doanh nghiệp, bỏ qua
  fi

  # Chuẩn hóa URL (bỏ trailing slash)
  org_url="${org_url%/}"

  log "Đang kết nối với máy chủ doanh nghiệp..."

  local payload_file
  payload_file="$(mktemp)"
  echo -n "${org_token}" | python3 -c "
import json, sys
token = sys.stdin.read().strip()
with open('${payload_file}', 'w') as f:
    json.dump({'install_id': '${install_id}', 'github_user': '${github_user}', 'org_token': token}, f)
"

  local resp
  resp="$(curl -s -X POST "${org_url}/org-heartbeat" \
    -H "Content-Type: application/json" \
    -H "User-Agent: ba-kit-license/1.0" \
    -d "@${payload_file}" 2>/dev/null)" || {
      rm -f "${payload_file}"
      err "Không kết nối được với máy chủ doanh nghiệp: ${org_url}"
      err "Bản quyền cá nhân đã được kích hoạt. Liên hệ quản lý để kiểm tra."
      return 0  # Không chặn — central registration đã thành công
    }
  rm -f "${payload_file}"

  local tmp_json status
  tmp_json="$(mktemp)"
  echo "${resp}" > "${tmp_json}"

  # Guard: check valid JSON (worker crash returns HTML like "error code: 1101")
  if ! python3 -c "import json; json.load(open('${tmp_json}'))" 2>/dev/null; then
    local raw_preview
    raw_preview="$(head -c 200 "${tmp_json}")"
    rm -f "${tmp_json}"
    err "Máy chủ doanh nghiệp không phản hồi đúng định dạng (có thể đang khởi động lại)."
    err "Phản hồi thực tế: ${raw_preview}"
    err "Bản quyền cá nhân đã được kích hoạt. Thử lại sau vài giây."
    return 0
  fi

  status="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('status','error'))" 2>/dev/null || echo "error")"

  case "${status}" in
    ok)
      rm -f "${tmp_json}"
      ok "Đã kết nối với máy chủ doanh nghiệp"
      ;;
    *)
      local reason
      reason="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('reason', d.get('error', 'unknown')))" 2>/dev/null || echo "unknown")"
      rm -f "${tmp_json}"
      err "Máy chủ doanh nghiệp từ chối: ${reason}"
      if [[ "${reason}" == "invalid_org_token" ]]; then
        err "Mã doanh nghiệp không đúng. Kiểm tra lại mã do quản lý cấp."
      fi
      err "Bản quyền cá nhân đã được kích hoạt. Liên hệ quản lý để kiểm tra."
      ;;
  esac

  return 0
}

# ── Main ─────────────────────────────────────────────────────────────

main() {
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  BA-kit — Kích hoạt bản quyền"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  check_prereqs

  # Check existing license
  if [[ -f "${LICENSE_FILE}" ]]; then
    local existing_user
    existing_user="$(python3 -c "import json,pathlib; print(json.loads(pathlib.Path('${LICENSE_FILE}').read_text()).get('github_user',''))" 2>/dev/null || echo "")"
    if [[ -n "${existing_user}" ]]; then
      echo "Đã đăng ký với tài khoản @${existing_user}."
      echo ""
      read -r -p "  Đăng ký lại? [c/K] " REPLY
      if [[ ! "${REPLY}" =~ ^[Cc]$ ]]; then
        echo "  Đã bỏ qua. Giữ thông tin bản quyền hiện tại."
        echo ""
        return 0
      fi
      echo ""
    fi
  fi

  local install_id
  install_id="$(generate_install_id)"

  # GitHub Device Flow
  request_device_code || return $?
  poll_for_token || return $?

  # Register
  register_with_server "${install_id}" "${ACCESS_TOKEN}" || return $?

  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  🎉  Kích hoạt thành công!"
  echo "  BA-kit sẽ tự động kiểm tra bản quyền khi bạn dùng."
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  return 0
}

main "$@"
