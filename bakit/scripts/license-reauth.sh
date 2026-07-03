#!/usr/bin/env bash
# BA-kit License Re-authentication
# Re-validates or re-registers when token expires or access is revoked.
# Usage: ba-kit reauth
# Exit codes: 0=success, 1=failed, 2=denied, 3=network_error

set -euo pipefail

LICENSE_FILE="${HOME}/.claude/ba-kit/.license"
LICENSE_SERVER="https://license.bakit.ai.vn"
LICENSE_DIR="$(dirname "${LICENSE_FILE}")"
GITHUB_DEVICE_URL="https://github.com/login/device/code"
GITHUB_ACCESS_TOKEN_URL="https://github.com/login/oauth/access_token"
GITHUB_CLIENT_ID="Ov23linHDKO51UHCCaOM"
POLL_INTERVAL=5
POLL_TIMEOUT=300

log()  { echo "  $*" >&2; }
info() { echo "  ℹ️  $*" >&2; }
ok()   { echo "  ✅ $*" >&2; }
err()  { echo "  ❌ $*" >&2; }

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
  python3 -c "
import json, base64, pathlib
lic = json.loads(pathlib.Path('${LICENSE_FILE}').read_text())
print(base64.b64decode(lic['token_obfuscated']).decode())
" 2>/dev/null || echo ""
}

# ── Step 1: Try re-validation ────────────────────────────────────────

try_revalidate() {
  local install_id
  install_id="$(read_license_field "install_id")"
  if [[ -z "${install_id}" ]]; then
    return 1
  fi

  local token
  token="$(deobfuscate_token)"
  if [[ -z "${token}" ]]; then
    err "Không đọc được thông tin bản quyền. Cần đăng ký lại."
    return 1
  fi

  log "Đang kiểm tra bản quyền hiện tại..."

  # Build payload via temp file — token passed via stdin, not argv
  local payload_file resp status
  payload_file="$(mktemp)"
  echo -n "${token}" | python3 -c "
import json, sys
token = sys.stdin.read().strip()
with open('${payload_file}', 'w') as f:
    json.dump({'install_id': '${install_id}', 'github_token': token}, f)
"

  resp="$(curl -s -m 5 -X POST "${LICENSE_SERVER}/validate" \
    -H "Content-Type: application/json" \
    -H "User-Agent: ba-kit-license/1.0" \
    -d "@${payload_file}" 2>/dev/null || echo '{"status":"network_error"}')"
  rm -f "${payload_file}"

  status="$(echo "${resp}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','error'))" 2>/dev/null || echo "error")"

  case "${status}" in
    ok)
      local now_epoch
      now_epoch="$(date +%s)"
      write_license_fields "{\"last_validated\": ${now_epoch}, \"offline_count\": 0}"
      ok "Bản quyền vẫn còn hiệu lực. Không cần đăng ký lại."
      return 0
      ;;
    denied)
      local reason
      reason="$(echo "${resp}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('reason','unknown'))" 2>/dev/null || echo "unknown")"
      case "${reason}" in
        unregistered)
          err "Bản quyền chưa được đăng ký trên máy chủ."
          ;;
        revoked)
          err "Bản quyền đã bị thu hồi."
          ;;
        *)
          err "Bản quyền không còn hiệu lực: ${reason}"
          ;;
      esac
      log "Tiến hành đăng ký lại..."
      return 1
      ;;
    *)
      err "Không kết nối được với máy chủ bản quyền."
      return 1
      ;;
  esac
}

# ── Step 2: GitHub Device Flow ───────────────────────────────────────

request_device_code() {
  log "Đang kết nối với GitHub..."

  local resp
  resp="$(curl -s -X POST "${GITHUB_DEVICE_URL}" \
    -H "Accept: application/json" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "User-Agent: ba-kit-license/1.0" \
    --data-urlencode "client_id=${GITHUB_CLIENT_ID}" \
    --data-urlencode "scope=repo,read:user" 2>/dev/null)" || {
      err "Không kết nối được với GitHub."
      return 3
    }

  local tmp_json
  tmp_json="$(mktemp)"
  echo "${resp}" > "${tmp_json}"

  DEVICE_CODE="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('device_code',''))" 2>/dev/null)"
  USER_CODE="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('user_code',''))" 2>/dev/null)"
  VERIFICATION_URI="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('verification_uri',''))" 2>/dev/null)"
  INTERVAL="$(python3 -c "import json; d=json.load(open('${tmp_json}')); print(d.get('interval','5'))" 2>/dev/null)"
  rm -f "${tmp_json}"

  if [[ -z "${DEVICE_CODE}" ]] || [[ -z "${USER_CODE}" ]]; then
    err "GitHub trả về phản hồi không mong đợi."
    return 3
  fi

  ok "Đã nhận mã xác nhận từ GitHub"

  # Auto-open browser
  local open_cmd=""
  if command -v open >/dev/null 2>&1; then
    open_cmd="open"
  elif command -v xdg-open >/dev/null 2>&1; then
    open_cmd="xdg-open"
  elif command -v start >/dev/null 2>&1; then
    open_cmd="start"
  fi

  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  🔐  Mở trang web sau để xác nhận:"
  echo ""
  echo "  ${VERIFICATION_URI}"
  echo ""
  echo "  Nhập mã: ${USER_CODE}"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  if [[ -n "${open_cmd}" ]]; then
    "${open_cmd}" "${VERIFICATION_URI}" >/dev/null 2>&1 || true
  fi

  return 0
}

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
      "authorization_pending") rm -f "${tmp_json}"; continue ;;
      "slow_down") interval=$((interval + 5)); rm -f "${tmp_json}"; continue ;;
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

# ── Step 3: Register/update with central server ──────────────────────

register_with_server() {
  local install_id="$1"
  local github_token="$2"

  log "Đang cập nhật bản quyền trên máy chủ..."

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
      err "Không kết nối được với máy chủ bản quyền."
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
      ok "Đã cập nhật bản quyền (tài khoản @${github_user})"

      # Update token in existing license file — pass via stdin
      local token_obfuscated now
      token_obfuscated="$(echo -n "${github_token}" | python3 -c "
import sys, base64
print(base64.b64encode(sys.stdin.read().encode()).decode())
")"
      now="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
      write_license_fields "{\"token_obfuscated\": \"${token_obfuscated}\", \"github_user\": \"${github_user}\", \"last_verified\": \"${now}\", \"offline_count\": 0, \"last_validated\": $(date +%s)}"
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
      echo "  Tài khoản @${github_user} chưa được cấp quyền truy cập"
      echo "  vào kho mã nguồn BA-kit (bakit-org/bakit)."
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

# ── Step 4: Re-register with enterprise (nếu có) ─────────────────────

revalidate_enterprise() {
  local install_id="$1"
  local github_user="$2"

  local org_url org_token
  org_url="$(read_license_field "org_url")"
  org_token="$(read_license_field "org_token")"

  if [[ -z "${org_url}" ]] || [[ -z "${org_token}" ]]; then
    return 0  # Không có thông tin doanh nghiệp
  fi

  org_url="${org_url%/}"

  log "Đang kết nối lại với máy chủ doanh nghiệp..."

  local payload_file
  payload_file="$(mktemp)"
  echo -n "${org_token}" | python3 -c "
import json, sys
token = sys.stdin.read().strip()
with open('${payload_file}', 'w') as f:
    json.dump({'install_id': '${install_id}', 'github_user': '${github_user}', 'org_token': token}, f)
"

  local resp
  resp="$(curl -s -m 5 -X POST "${org_url}/org-heartbeat" \
    -H "Content-Type: application/json" \
    -H "User-Agent: ba-kit-license/1.0" \
    -d "@${payload_file}" 2>/dev/null)" || {
      rm -f "${payload_file}"
      err "Không kết nối được với máy chủ doanh nghiệp."
      return 0  # Không chặn
    }
  rm -f "${payload_file}"

  local status
  status="$(echo "${resp}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','error'))" 2>/dev/null || echo "error")"

  if [[ "${status}" == "ok" ]]; then
    ok "Đã kết nối lại với máy chủ doanh nghiệp"
  else
    err "Máy chủ doanh nghiệp từ chối kết nối."
  fi

  return 0
}

# ── Main ─────────────────────────────────────────────────────────────

main() {
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  BA-kit — Kích hoạt lại bản quyền"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  # Kiểm tra prerequisites
  for cmd in curl python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      err "Thiếu lệnh: $cmd"
      exit 3
    fi
  done

  # Check license file exists
  if [[ ! -f "${LICENSE_FILE}" ]]; then
    err "Chưa có thông tin bản quyền."
    log "Vui lòng chạy cài đặt lại hoặc đăng ký mới."
    exit 1
  fi

  # Try re-validation first
  if try_revalidate; then
    echo ""
    return 0
  fi

  # Need to re-register
  local install_id
  install_id="$(read_license_field "install_id")"
  if [[ -z "${install_id}" ]]; then
    install_id="$(python3 -c "import uuid; print(str(uuid.uuid4()))")"
  fi

  # GitHub Device Flow
  request_device_code || exit $?
  poll_for_token || exit $?

  # Register with central server
  register_with_server "${install_id}" "${ACCESS_TOKEN}" || exit $?

  # Re-register with enterprise if applicable
  local github_user
  github_user="$(read_license_field "github_user")"
  revalidate_enterprise "${install_id}" "${github_user}" || true

  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  🎉  Kích hoạt lại thành công!"
  echo "  BA-kit sẽ tự động kiểm tra bản quyền khi bạn dùng."
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  return 0
}

main "$@"
