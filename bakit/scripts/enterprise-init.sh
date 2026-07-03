#!/usr/bin/env bash
# BA-kit Enterprise Init — Guided setup script
# Helps enterprise admin deploy their own BA-kit usage tracking worker.
# Usage: bash enterprise-init.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="${SCRIPT_DIR}/../server/enterprise-template"

# ── Helpers ──────────────────────────────────────────────────────────
log()  { echo "  $*"; }
ok()   { echo "  ✅ $*"; }
err()  { echo "  ❌ $*"; }
info() { echo "  ℹ️  $*"; }

# ── Step 1: Welcome ──────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  🏢  BA-kit Enterprise — Cài đặt máy chủ theo dõi đội nhóm"
echo ""
echo "  Công cụ này giúp bạn theo dõi team dùng BA-kit như thế nào:"
echo "  • Ai đang dùng BA-kit"
echo "  • Dùng kỹ năng nào nhiều nhất"
echo "  • Dùng bao nhiêu token"
echo ""
echo "  Cần khoảng 5-10 phút để cài đặt."
echo "  Bạn không cần biết lập trình — làm theo từng bước là được."
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ── Step 2: Check prerequisites ──────────────────────────────────────

echo "━━━ Bước 1: Kiểm tra công cụ cần thiết ━━━"
echo ""

# Check Node.js
NODE_CMD=""
if command -v node >/dev/null 2>&1; then
  NODE_VERSION="$(node --version 2>/dev/null || echo "unknown")"
  ok "Đã có Node.js (phiên bản ${NODE_VERSION})"
  NODE_CMD="node"
else
  err "Chưa có Node.js"

  # Detect OS for install instructions
  case "$(uname -s)" in
    Darwin)
      echo ""
      echo "  Cài Node.js trên macOS:"
      echo "  1. Mở: https://nodejs.org"
      echo "  2. Tải bản LTS (nút màu xanh bên trái)"
      echo "  3. Mở file vừa tải và làm theo hướng dẫn"
      echo "  4. Đóng và mở lại Terminal"
      echo "  5. Chạy lại lệnh này"
      ;;
    Linux)
      echo ""
      echo "  Cài Node.js trên Linux:"
      echo "  Mở Terminal và chạy:"
      echo "    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -"
      echo "    sudo apt-get install -y nodejs"
      ;;
    *)
      echo ""
      echo "  Vào https://nodejs.org để tải Node.js cho hệ điều hành của bạn."
      ;;
  esac
  echo ""
  echo "  Sau khi cài xong, chạy lại lệnh này."
  exit 1
fi

# Check wrangler
WRANGLER_CMD=""
if command -v wrangler >/dev/null 2>&1; then
  ok "Đã có wrangler CLI"
  WRANGLER_CMD="wrangler"
elif command -v npx >/dev/null 2>&1; then
  ok "Sẽ dùng npx wrangler (không cần cài riêng)"
  WRANGLER_CMD="npx wrangler"
else
  err "Chưa có npx (đi kèm Node.js). Kiểm tra lại Node.js."
  exit 1
fi

echo ""

# ── Step 3: Cloudflare account ───────────────────────────────────────

echo "━━━ Bước 2: Tài khoản Cloudflare (miễn phí) ━━━"
echo ""

if ${WRANGLER_CMD} whoami >/dev/null 2>&1; then
  ok "Đã đăng nhập Cloudflare"
else
  echo "  BA-kit Enterprise chạy trên Cloudflare (miễn phí)."
  echo "  Bạn cần tạo tài khoản Cloudflare để tiếp tục."
  echo ""
  echo "   Mở: https://dash.cloudflare.com/sign-up"
  echo "  (Miễn phí — không cần thẻ tín dụng)"
  echo ""

  read -r -p "  Đã có tài khoản Cloudflare? Nhấn Enter để đăng nhập... " _

  ${WRANGLER_CMD} login || {
    err "Không đăng nhập được Cloudflare."
    echo ""
    echo "  Thử lại bằng cách:"
    echo "    npx wrangler login"
    exit 1
  }

  ok "Đã đăng nhập Cloudflare"
fi

echo ""

# ── Step 4: Generate secrets ─────────────────────────────────────────

echo "━━━ Bước 3: Tạo mã bảo mật ━━━"
echo ""

ORG_TOKEN="$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || python3 -c "import os; print(os.urandom(32).hex())")"
ADMIN_TOKEN="$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || python3 -c "import os; print(os.urandom(32).hex())")"

ok "Đã tạo mã bảo mật"
echo ""
echo "  ⚠️  QUAN TRỌNG: Hãy lưu 2 mã này vào nơi an toàn!"
echo ""
echo "  📋 Mã doanh nghiệp (ORG_TOKEN) — gửi cho thành viên trong team:"
echo "     ${ORG_TOKEN}"
echo ""
echo "  🔑 Mã quản trị (ADMIN_TOKEN) — chỉ bạn giữ, dùng để xem bảng điều khiển:"
echo "     ${ADMIN_TOKEN}"
echo ""

read -r -p "  Đã lưu 2 mã trên? Nhấn Enter để tiếp tục... " _

# ── Step 5: Create D1 database ───────────────────────────────────────

echo ""
echo "━━━ Bước 4: Tạo cơ sở dữ liệu ━━━"
echo ""

cd "${TEMPLATE_DIR}"

D1_OUTPUT="$(${WRANGLER_CMD} d1 create ba-kit-enterprise 2>&1)" || {
  # Database already exists — get ID from list
  D1_OUTPUT="$(${WRANGLER_CMD} d1 list 2>&1)" || {
    err "Không tạo được cơ sở dữ liệu D1 và không lấy được danh sách."
    exit 1
  }
  info "Cơ sở dữ liệu đã tồn tại, dùng lại."
}

D1_ID="$(echo "${D1_OUTPUT}" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)" || true

if [[ -n "${D1_ID}" ]]; then
  ok "Đã tạo cơ sở dữ liệu: ${D1_ID}"

  # Update wrangler.toml with D1 ID
  if [[ "$(uname -s)" == "Darwin" ]]; then
    sed -i '' "s/REPLACE_WITH_YOUR_D1_ID/${D1_ID}/" wrangler.toml
  else
    sed -i "s/REPLACE_WITH_YOUR_D1_ID/${D1_ID}/" wrangler.toml
  fi

  # Run schema on REMOTE database
  ${WRANGLER_CMD} d1 execute ba-kit-enterprise --remote --file=d1-schema.sql 2>&1 || {
    err "Không tạo được bảng dữ liệu. Thử lại sau."
    exit 1
  }
  # Verify tables exist
  local table_count
  table_count="$(${WRANGLER_CMD} d1 execute ba-kit-enterprise --remote --command="SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table'" --json 2>&1 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['results'][0]['cnt'])" 2>/dev/null || echo "0")"
  if [[ "${table_count}" -lt 2 ]]; then
    err "Bảng dữ liệu chưa được tạo (${table_count} bảng). Đang thử lại..."
    ${WRANGLER_CMD} d1 execute ba-kit-enterprise --remote --file=d1-schema.sql 2>&1 || {
      err "Vẫn không tạo được bảng. Liên hệ hỗ trợ."
      exit 1
    }
  fi
  ok "Đã tạo bảng dữ liệu"
else
  err "Không lấy được ID cơ sở dữ liệu. Kiểm tra lại: npx wrangler d1 list"
  exit 1
fi

# ── Step 6: Set secrets ──────────────────────────────────────────────

echo ""
echo "━━━ Bước 5: Lưu mã bảo mật lên Cloudflare ━━━"

printf '%s' "${ORG_TOKEN}" | ${WRANGLER_CMD} secret put ORG_TOKEN 2>&1 || {
  err "Không lưu được ORG_TOKEN"
  exit 1
}
ok "Đã lưu mã doanh nghiệp (ORG_TOKEN)"

printf '%s' "${ADMIN_TOKEN}" | ${WRANGLER_CMD} secret put ADMIN_TOKEN 2>&1 || {
  err "Không lưu được ADMIN_TOKEN"
  exit 1
}
ok "Đã lưu mã quản trị (ADMIN_TOKEN)"

# ── Step 7: Deploy ───────────────────────────────────────────────────

echo ""
echo "━━━ Bước 6: Đưa máy chủ lên mạng ━━━"

DEPLOY_OUTPUT="$(${WRANGLER_CMD} deploy 2>&1)" || {
  err "Không triển khai được."
  echo "  Kết quả: ${DEPLOY_OUTPUT}"
  echo "  Thử lại: cd server/enterprise-template && npx wrangler deploy"
  exit 1
}

WORKER_URL="$(echo "${DEPLOY_OUTPUT}" | grep -oE 'https://[a-zA-Z0-9.-]+\.workers\.dev' | head -1)" || true

# Warm-up: ensure worker is ready (prevent cold-start crash)
if [[ -n "${WORKER_URL}" ]]; then
  curl -s -m 10 "${WORKER_URL}/org-heartbeat" -H "Content-Type: application/json" \
    -d "{\"install_id\":\"warmup\",\"github_user\":\"_\",\"org_token\":\"${ORG_TOKEN}\",\"skill\":\"_\"}" >/dev/null 2>&1 || true
  sleep 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  🎉  Cài đặt thành công!"
echo ""
if [[ -n "${WORKER_URL}" ]]; then
  echo "  📊 Bảng điều khiển: ${WORKER_URL}/admin"
  echo "     (đăng nhập bằng Mã quản trị ở trên)"
  echo ""
  echo "  📡 Địa chỉ máy chủ: ${WORKER_URL}"
  echo "     (gửi địa chỉ này + Mã doanh nghiệp cho thành viên)"
fi
echo ""
echo "  📋 Thông tin cần gửi cho thành viên trong team:"
echo "     • Mã doanh nghiệp: ${ORG_TOKEN}"
echo "     • Địa chỉ máy chủ: ${WORKER_URL:-<xem ở trên>}"
echo ""
echo "  Mỗi thành viên nhập 2 thông tin này khi cài BA-kit."
echo ""
echo "  🔑 Mã quản trị (chỉ bạn giữ):"
echo "     ${ADMIN_TOKEN}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
