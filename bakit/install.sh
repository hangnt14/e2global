#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_HOME="${HOME}/.claude"
SKILLS_TARGET="${TARGET_HOME}/skills"
RULES_TARGET="${TARGET_HOME}/rules/ba-kit"
AGENTS_TARGET="${TARGET_HOME}/agents"
TEMPLATES_TARGET="${TARGET_HOME}/templates"
CORE_SOURCE="${ROOT_DIR}/core"
CORE_TARGET="${TARGET_HOME}/ba-kit"
# Antigravity targets
AGY_HOME="${HOME}/.gemini/antigravity"
AGY_SKILLS_TARGET="${AGY_HOME}/skills"
AGY_RULES_TARGET="${AGY_HOME}/rules/ba-kit"
AGY_AGENTS_TARGET="${AGY_HOME}/agents"
AGY_TEMPLATES_TARGET="${AGY_HOME}/templates"
AGY_CORE_TARGET="${AGY_HOME}/ba-kit"
LOCAL_BIN_TARGET="${HOME}/.local/bin"
STATE_TARGET="${HOME}/.local/share/ba-kit/installations"
STALE_TEMPLATE_FILES=(
  "wireframe-input-template.md"
  "wireframe-map-template.md"
)
STALE_CORE_PATHS=(
  "references"
)
MANAGED_SKILL_DIRS=(
  "ba-*"
  "brainstorm"
  "reverse-web"
  "qc-uc-review"
)

# ── python3 bootstrap (cross-platform) ───────────────────────────────
# On macOS/Linux, python3 is the system Python 3 binary.
# On Windows (Git Bash), python3 may resolve to a non-functional
# Microsoft Store stub. This ensures python3 always points to a real
# Python 3 interpreter so generated hooks and scripts work correctly.
bootstrap_python3() {
  # Already a working python3? Nothing to do.
  if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
    return 0
  fi

  local real_python=""
  # Try common candidates
  for _c in python py python3.12 python3.13 python3.14; do
    if command -v "${_c}" >/dev/null 2>&1 && "${_c}" --version >/dev/null 2>&1; then
      real_python="${_c}"
      break
    fi
  done

  # Scan Windows Python install paths as last resort
  if [[ -z "${real_python}" ]]; then
    for _p in /c/Python313/python /c/Python312/python /c/Python314/python; do
      if [[ -x "${_p}" ]]; then
        real_python="${_p}"
        break
      fi
    done
  fi

  if [[ -z "${real_python}" ]]; then
    echo "WARNING: python3 not found and no real Python detected." >&2
    echo "BA-kit hooks requiring Python will not function." >&2
    return 1
  fi

  mkdir -p "${HOME}/bin"
  local wrapper="${HOME}/bin/python3"
  cat > "${wrapper}" <<WRAPEOF
#!/usr/bin/env bash
# BA-kit python3 bootstrap wrapper
exec ${real_python} "\$@"
WRAPEOF
  chmod +x "${wrapper}"

  # Verify the wrapper works
  if ! "${wrapper}" --version >/dev/null 2>&1; then
    echo "WARNING: python3 wrapper created but non-functional." >&2
    rm -f "${wrapper}"
    return 1
  fi

  echo "Bootstrap: created python3 → ${real_python}"
  return 0
}

cleanup_managed_skill_dirs() {
  local pattern path

  mkdir -p "${SKILLS_TARGET}"
  shopt -s nullglob
  for pattern in "${MANAGED_SKILL_DIRS[@]}"; do
    for path in "${SKILLS_TARGET}"/${pattern}; do
      [[ -e "${path}" ]] || continue
      rm -rf "${path}"
    done
  done
  shopt -u nullglob
}

cleanup_managed_agent_files() {
  local agent_path

  mkdir -p "${AGENTS_TARGET}"
  shopt -s nullglob
  for agent_path in "${ROOT_DIR}"/agents/*; do
    [[ -f "${agent_path}" ]] || continue
    rm -f "${AGENTS_TARGET}/$(basename "${agent_path}")"
  done
  shopt -u nullglob
}

cleanup_managed_template_files() {
  local template_path

  mkdir -p "${TEMPLATES_TARGET}"
  shopt -s nullglob
  for template_path in "${ROOT_DIR}"/templates/*; do
    [[ -f "${template_path}" ]] || continue
    rm -f "${TEMPLATES_TARGET}/$(basename "${template_path}")"
  done
  shopt -u nullglob
}

cleanup_previous_install() {
  cleanup_managed_skill_dirs
  cleanup_managed_agent_files
  cleanup_managed_template_files
  # Preserve license file across cleanup
  local license_backup=""
  local license_file="${HOME}/.claude/ba-kit/.license"
  if [[ -f "${license_file}" ]]; then
    license_backup="$(cat "${license_file}")"
  fi
  rm -rf "${RULES_TARGET}" "${CORE_TARGET}"
  rm -rf "${TARGET_HOME}/core"
  if [[ -n "${license_backup}" ]]; then
    mkdir -p "$(dirname "${license_file}")"
    echo "${license_backup}" > "${license_file}"
    chmod 600 "${license_file}"
  fi
}

cleanup_previous_agy_install() {
  local target_home="$1"
  rm -rf "${target_home}/rules/ba-kit" "${target_home}/ba-kit"
  rm -rf "${target_home}/skills"/ba-* 2>/dev/null || true
  rm -rf "${target_home}/skills"/brainstorm 2>/dev/null || true
  rm -rf "${target_home}/skills"/reverse-web 2>/dev/null || true
  rm -rf "${target_home}/skills"/qc-uc-review 2>/dev/null || true
  rm -rf "${target_home}/core"
  for agent_path in "${ROOT_DIR}"/agents/*; do
    [[ -f "${agent_path}" ]] || continue
    rm -f "${target_home}/agents/$(basename "${agent_path}")"
  done
  for template_path in "${ROOT_DIR}"/templates/*; do
    [[ -f "${template_path}" ]] || continue
    rm -f "${target_home}/templates/$(basename "${template_path}")"
  done
}

detect_antigravity() {
  [[ -d "${AGY_HOME}" ]] && return 0
  [[ -d "${HOME}/.gemini" ]] && return 0
  command -v agy >/dev/null 2>&1 && return 0
  return 1
}

copy_tree() {
  local source_dir="$1"
  local target_dir="$2"

  mkdir -p "$target_dir"
  cp -R "${source_dir}/." "$target_dir/"
}

remove_stale_templates() {
  local target_dir="$1"
  local file_name

  for file_name in "${STALE_TEMPLATE_FILES[@]}"; do
    rm -f "${target_dir}/${file_name}"
  done
}

remove_stale_core_paths() {
  local target_dir="$1"
  local path_name

  for path_name in "${STALE_CORE_PATHS[@]}"; do
    rm -rf "${target_dir}/${path_name}"
  done
}

install_cli() {
  local temp_target
  mkdir -p "${LOCAL_BIN_TARGET}"
  temp_target="$(mktemp "${LOCAL_BIN_TARGET}/ba-kit.tmp.XXXXXX")"
  cp "${ROOT_DIR}/scripts/ba-kit" "${temp_target}"
  chmod +x "${temp_target}"
  mv "${temp_target}" "${LOCAL_BIN_TARGET}/ba-kit"
}

write_manifest() {
  mkdir -p "${STATE_TARGET}"
  cat > "${STATE_TARGET}/claude.env" <<EOF
BA_KIT_RUNTIME=claude
BA_KIT_SOURCE_REPO=${ROOT_DIR}
BA_KIT_INSTALLED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BA_KIT_INSTALLER=install.sh
EOF
}

echo "Installing BA-kit from: ${ROOT_DIR}"
mkdir -p "${TARGET_HOME}"
cleanup_previous_install

mkdir -p "${SKILLS_TARGET}"
for skill_dir in "${ROOT_DIR}"/skills/*; do
  if [[ -d "${skill_dir}" ]]; then
    copy_tree "${skill_dir}" "${SKILLS_TARGET}/$(basename "${skill_dir}")"
  fi
done
copy_tree "${ROOT_DIR}/rules" "${RULES_TARGET}"
copy_tree "${ROOT_DIR}/agents" "${AGENTS_TARGET}"
copy_tree "${ROOT_DIR}/templates" "${TEMPLATES_TARGET}"
remove_stale_templates "${TEMPLATES_TARGET}"
copy_tree "${CORE_SOURCE}" "${CORE_TARGET}"
remove_stale_core_paths "${CORE_TARGET}"
ln -sfn ba-kit "${TARGET_HOME}/core"
install_cli

mkdir -p "${ROOT_DIR}/docs" "${ROOT_DIR}/templates" "${ROOT_DIR}/designs"

echo "Installed skills to ${SKILLS_TARGET}"
echo "Installed rules to ${RULES_TARGET}"
echo "Installed agents to ${AGENTS_TARGET}"
echo "Installed templates to ${TEMPLATES_TARGET}"
echo "Installed BA core to ${CORE_TARGET}"
echo "Installed update CLI to ${LOCAL_BIN_TARGET}/ba-kit"

bootstrap_python3

if [[ -f "${ROOT_DIR}/scripts/install-claude-code-ba-kit.sh" ]]; then
  echo ""
  echo "Executing Claude Code guardrail installation..."
  if bash "${ROOT_DIR}/scripts/install-claude-code-ba-kit.sh"; then
    echo ""
    echo "BA-kit Claude Code installation complete (core + guardrails)."
  else
    rc=$?
    echo "" >&2
    echo "WARNING: Guardrail installation failed (exit code ${rc})." >&2
    echo "BA-kit Claude Code core installed successfully, but guardrail hooks may be incomplete." >&2
    echo "Re-run ./install.sh or check scripts/install-claude-code-ba-kit.sh for errors." >&2
  fi
else
  echo ""
  echo "BA-kit Claude Code installation complete."
fi

# ── Antigravity installation ──────────────────────────────────────────

if detect_antigravity && [[ -f "${ROOT_DIR}/scripts/install-antigravity-ba-kit.sh" ]]; then
  echo ""
  echo "Antigravity detected. Installing BA-kit for active Antigravity runtimes..."
  
  ACTIVE_AGY_HOMES=()
  for dir in "${HOME}/.gemini/antigravity-cli" "${HOME}/.gemini/antigravity" "${HOME}/.gemini/antigravity-ide"; do
    if [[ -d "${dir}" ]]; then
      ACTIVE_AGY_HOMES+=("${dir}")
    fi
  done
  if [[ ${#ACTIVE_AGY_HOMES[@]} -eq 0 ]]; then
    ACTIVE_AGY_HOMES+=("${HOME}/.gemini/antigravity")
  fi

  for target_home in "${ACTIVE_AGY_HOMES[@]}"; do
    echo "Installing assets for Antigravity home: ${target_home}"
    cleanup_previous_agy_install "${target_home}"

    mkdir -p "${target_home}/skills"
    for skill_dir in "${ROOT_DIR}"/skills/*; do
      if [[ -d "${skill_dir}" ]]; then
        copy_tree "${skill_dir}" "${target_home}/skills/$(basename "${skill_dir}")"
      fi
    done
    copy_tree "${ROOT_DIR}/rules" "${target_home}/rules/ba-kit"
    copy_tree "${ROOT_DIR}/agents" "${target_home}/agents"
    copy_tree "${ROOT_DIR}/templates" "${target_home}/templates"
    remove_stale_templates "${target_home}/templates"
    copy_tree "${CORE_SOURCE}" "${target_home}/ba-kit"
    remove_stale_core_paths "${target_home}/ba-kit"
    ln -sfn ba-kit "${target_home}/core"

    echo "Installed BA-kit assets to ${target_home}"
  done

  if bash "${ROOT_DIR}/scripts/install-antigravity-ba-kit.sh"; then
    echo ""
    echo "BA-kit Antigravity installation complete."
  else
    rc=$?
    echo "" >&2
    echo "WARNING: Antigravity guardrail installation failed (exit code ${rc})." >&2
  fi
fi

write_manifest
echo ""
echo "BA-kit installation complete."

# ── License registration ────────────────────────────────────────────
LICENSE_FILE="${HOME}/.claude/ba-kit/.license"
LICENSE_REGISTER_SCRIPT="${ROOT_DIR}/scripts/license-register.sh"
if [[ -f "${LICENSE_REGISTER_SCRIPT}" ]]; then
  # ── Check existing license (skip prompts on update) ──────────────────
  existing_user=""
  existing_install_id=""
  if [[ -f "${LICENSE_FILE}" ]]; then
    existing_user="$(python3 -c "import json,pathlib; print(json.loads(pathlib.Path('${LICENSE_FILE}').read_text()).get('github_user',''))" 2>/dev/null || echo "")"
    existing_install_id="$(python3 -c "import json,pathlib; print(json.loads(pathlib.Path('${LICENSE_FILE}').read_text()).get('install_id',''))" 2>/dev/null || echo "")"
  fi

  if [[ -n "${existing_user}" ]]; then
    # ── Detect incomplete license (has github_user but missing install_id) ─
    if [[ -z "${existing_install_id}" ]]; then
      echo ""
      echo "═══════════════════════════════════════════════════════════════"
      echo "  ⚠️  BA-kit chưa được kích hoạt đầy đủ"
      echo "  Tài khoản: @${existing_user}"
      echo "  Thiếu install_id — cần đăng ký lại để hoàn tất."
      echo "═══════════════════════════════════════════════════════════════"
      echo ""

      # Carry forward existing org_token/org_url so user doesn't re-enter them
      saved_org_token="$(python3 -c "import json,pathlib; print(json.loads(pathlib.Path('${LICENSE_FILE}').read_text()).get('org_token',''))" 2>/dev/null || echo "")"
      saved_org_url="$(python3 -c "import json,pathlib; print(json.loads(pathlib.Path('${LICENSE_FILE}').read_text()).get('org_url',''))" 2>/dev/null || echo "")"
      rm -f "${LICENSE_FILE}"

      if [[ -n "${saved_org_token}" ]] && [[ -n "${saved_org_url}" ]]; then
        ORG_TOKEN="${saved_org_token}" ORG_URL="${saved_org_url}" bash "${LICENSE_REGISTER_SCRIPT}" || true
      else
        bash "${LICENSE_REGISTER_SCRIPT}" || true
      fi
    else
      echo ""
      echo "═══════════════════════════════════════════════════════════════"
      echo "  ✅  BA-kit đã được kích hoạt"
      echo "  Tài khoản: @${existing_user}"
      echo "═══════════════════════════════════════════════════════════════"
      echo ""

      read -r -p "  Cập nhật lại thông tin doanh nghiệp? [c/K] " UPDATE_ORG
      if [[ "${UPDATE_ORG}" =~ ^[Cc]$ ]]; then
        echo ""
        read -r -p "  Nhập mã doanh nghiệp (do quản lý cấp): " ORG_TOKEN_INPUT
        read -r -p "  Nhập địa chỉ máy chủ doanh nghiệp (ví dụ: https://ba.congty.com): " ORG_URL_INPUT
        if [[ -n "${ORG_TOKEN_INPUT}" ]] && [[ -n "${ORG_URL_INPUT}" ]]; then
          python3 -c "
import json, pathlib
lic = json.loads(pathlib.Path('${LICENSE_FILE}').read_text())
lic['org_token'] = '${ORG_TOKEN_INPUT}'
lic['org_url'] = '${ORG_URL_INPUT}'
pathlib.Path('${LICENSE_FILE}').write_text(json.dumps(lic, indent=2))
"
          echo "  ✅ Đã cập nhật thông tin doanh nghiệp."
        else
          echo "  ⚠️  Thiếu thông tin, giữ nguyên."
        fi
      fi
    fi
  else
  # ── First-time license registration ──────────────────────────────────
  echo ""
  echo "═══════════════════════════════════════════════════════════════"
  echo "  🔐  Kích hoạt bản quyền BA-kit"
  echo ""
  echo "  BA-kit cần xác nhận bạn có quyền truy cập vào"
  echo "  kho mã nguồn BA-kit (bakit-org/bakit) qua GitHub."
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  read -r -p "  Kích hoạt ngay bây giờ? [C/k] " REPLY
  if [[ "${REPLY}" =~ ^[Kk]$ ]]; then
    echo ""
    echo "  ⚠️  Bỏ qua kích hoạt. BA-kit sẽ hoạt động thử trong 7 ngày."
    echo "  Sau đó bạn cần kích hoạt để tiếp tục dùng."
    echo "  Để kích hoạt sau: mở terminal và chạy lệnh:"
    echo "    ba-kit reauth"
    echo ""
  else
    # ── Enterprise config prompt ────────────────────────────────────
    echo ""
    echo "  ───────────────────────────────────────────────────────────"
    echo "  Bạn có làm việc trong doanh nghiệp/tổ chức không?"
    echo ""
    echo "  Nếu có, quản lý dự án sẽ cấp cho bạn:"
    echo "    • Mã doanh nghiệp (mã DN)"
    echo "    • Địa chỉ máy chủ doanh nghiệp"
    echo ""
    echo "  Nếu bạn là BA độc lập (không thuộc tổ chức nào),"
    echo "  chọn 'k' để bỏ qua bước này."
    echo "  ───────────────────────────────────────────────────────────"
    echo ""
    read -r -p "  Bạn có mã doanh nghiệp không? [c/K] " HAS_ORG

    org_url=""
    org_token=""

    if [[ "${HAS_ORG}" =~ ^[Cc]$ ]]; then
      echo ""
      read -r -p "  Nhập mã doanh nghiệp (do quản lý cấp): " ORG_TOKEN_INPUT
      read -r -p "  Nhập địa chỉ máy chủ doanh nghiệp (ví dụ: https://ba.congty.com): " ORG_URL_INPUT

      if [[ -n "${ORG_TOKEN_INPUT}" ]]; then
        org_token="${ORG_TOKEN_INPUT}"
      fi
      if [[ -n "${ORG_URL_INPUT}" ]]; then
        org_url="${ORG_URL_INPUT}"
      fi

      if [[ -n "${org_token}" ]] && [[ -n "${org_url}" ]]; then
        echo ""
        echo "  ✅ Đã nhận thông tin doanh nghiệp."
      else
        echo ""
        echo "  ⚠️  Thiếu thông tin. Tiếp tục với tư cách BA độc lập."
        org_url=""
        org_token=""
      fi
    fi

    # ── Run registration ───────────────────────────────────────────
    echo ""
    echo "  ───────────────────────────────────────────────────────────"
    echo "  Bắt đầu kích hoạt bản quyền..."
    echo "  ───────────────────────────────────────────────────────────"
    echo ""

    if [[ -n "${org_url}" ]] && [[ -n "${org_token}" ]]; then
      ORG_TOKEN="${org_token}" ORG_URL="${org_url}" bash "${LICENSE_REGISTER_SCRIPT}" || {
        rc=$?
        echo ""
        if [[ ${rc} -eq 2 ]]; then
          echo "  ❌  Tài khoản GitHub của bạn chưa được cấp quyền truy cập"
          echo "  vào kho mã nguồn BA-kit (bakit-org/bakit)."
          echo "  Liên hệ quản lý dự án để được cấp quyền."
          echo "  Sau đó chạy lại lệnh: ba-kit reauth"
        else
          echo "  ⚠️  Kích hoạt chưa hoàn tất."
          echo "  BA-kit sẽ hoạt động thử. Chạy lại lệnh sau:"
          echo "    ba-kit reauth"
        fi
        echo ""
      }
    else
      bash "${LICENSE_REGISTER_SCRIPT}" || {
        rc=$?
        echo ""
        if [[ ${rc} -eq 2 ]]; then
          echo "  ❌  Tài khoản GitHub của bạn chưa được cấp quyền truy cập"
          echo "  vào kho mã nguồn BA-kit (bakit-org/bakit)."
          echo "  Liên hệ quản lý dự án để được cấp quyền."
          echo "  Sau đó chạy lại lệnh: ba-kit reauth"
        else
          echo "  ⚠️  Kích hoạt chưa hoàn tất."
          echo "  BA-kit sẽ hoạt động thử. Chạy lại lệnh sau:"
          echo "    ba-kit reauth"
        fi
        echo ""
      }
    fi
  fi
  fi  # end first-time else block
fi

