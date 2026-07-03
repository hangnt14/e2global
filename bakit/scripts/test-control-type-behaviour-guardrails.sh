#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/ba-kit-guardrails.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

cd "${ROOT_DIR}"

echo "1/6 py_compile"
python3 -m py_compile \
  scripts/check-control-type-compliance.py \
  scripts/check-message-placement.py \
  scripts/validate-cr-coverage.py \
  scripts/check-terminology-consistency.py \
  scripts/check-freshness.py \
  scripts/verify-compiled-output.py \
  scripts/compile-srs.py \
  scripts/md-to-html.py \
  scripts/doctor-srs.py

echo "2/6 CR coverage full-code extraction"
cat > "${TMP_DIR}/common-rules.md" <<'EOF'
| Code | Type | Rule Statement | Applies To (Pattern) | Edge Cases | Scope | Owner |
|---|---|---|---|---|---|---|
| CR-VAL-01 | VAL | Email format | Email | Empty email: show error. | All | @ba |
EOF
cat > "${TMP_DIR}/SCR-01.md" <<'EOF'
# SCR-01

## Fields

| Field ID | Field Name | Control Type | Display Rules | Behaviour Rules | Validation Rules |
|---|---|---|---|---|---|
| SCR-01-F01 | Email | `text_input` | Label: Email | (default) | CR-VAL-01 -> MSG-ERR-01 inline |

## States

Empty email: show error.
EOF
python3 scripts/validate-cr-coverage.py "${TMP_DIR}/SCR-01.md" --common-rules "${TMP_DIR}/common-rules.md" --json > "${TMP_DIR}/cr.json"
python3 - "${TMP_DIR}/cr.json" <<'PY'
import json, sys
data = json.loads(open(sys.argv[1], encoding="utf-8").read())
codes = [issue["code"] for result in data["results"] for issue in result["issues"]]
bad = {"missing_cr_reference", "undeclared_cr"} & set(codes)
if bad:
    raise SystemExit(f"unexpected CR extraction issue(s): {sorted(bad)}")
PY

echo "3/6 freshness supports compile-srs source_hashes receipts"
REPO_FIXTURE="${TMP_DIR}/repo"
mkdir -p "${REPO_FIXTURE}/core" "${REPO_FIXTURE}/plans/demo-260609-1500/03_modules/auth/srs"
cp core/contract.yaml "${REPO_FIXTURE}/core/contract.yaml"
printf 'hello\n' > "${REPO_FIXTURE}/plans/demo-260609-1500/03_modules/auth/srs/spec.md"
SPEC_HASH="$(python3 - "${REPO_FIXTURE}/plans/demo-260609-1500/03_modules/auth/srs/spec.md" <<'PY'
import hashlib, pathlib, sys
print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())
PY
)"
cat > "${REPO_FIXTURE}/plans/demo-260609-1500/03_modules/auth/srs-compile-receipt.json" <<EOF
{
  "source_hashes": {
    "srs/spec.md": "${SPEC_HASH}"
  }
}
EOF
python3 scripts/check-freshness.py --repo "${REPO_FIXTURE}" --slug demo --date 260609-1500 --module auth --json > "${TMP_DIR}/freshness.json"
python3 - "${TMP_DIR}/freshness.json" <<'PY'
import json, sys
data = json.loads(open(sys.argv[1], encoding="utf-8").read())
if data["status"] != "FRESH":
    raise SystemExit(f"expected FRESH, got {data}")
PY

echo "4/6 control type library edge cases parsed"
python3 - <<'PY'
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location("ct", "scripts/check-control-type-compliance.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
library = mod.load_library(Path("templates/control-type-library-template.md"))
edge_cases = library["text_input"].get("edge_cases", [])
if not edge_cases:
    raise SystemExit("text_input edge cases were not parsed")
PY

echo "5/6 DocsEngine wrapper and hook/installer syntax"
cat > "${TMP_DIR}/doc.md" <<'EOF'
# Demo

## Section

Content.
EOF
python3 scripts/md-to-html.py "${TMP_DIR}/doc.md" --output "${TMP_DIR}/doc.html" --docsengine >/dev/null
grep -q "material-symbols-outlined" "${TMP_DIR}/doc.html"
grep -q "data-artifact-type" "${TMP_DIR}/doc.html"
bash -n scripts/install-claude-code-ba-kit.sh
bash -n scripts/install-codex-ba-kit.sh
bash -n scripts/install-antigravity-ba-kit.sh
bash -n scripts/hooks/postwrite-guardrail.sh
python3 - <<'PY'
from pathlib import Path

checks = {
    "scripts/install-claude-code-ba-kit.sh": 'BA_KIT_HOOK_HOME=\\"{pathlib.Path.home()}/.claude/ba-kit\\" bash \\"{hooks_dir}/postwrite-guardrail.sh\\"',
    "scripts/install-codex-ba-kit.sh": 'BA_KIT_HOOK_HOME=\\"{pathlib.Path.home()}/.codex/ba-kit\\" bash \\"{hooks_dir}/postwrite-guardrail.sh\\"',
}
for path, expected in checks.items():
    text = Path(path).read_text(encoding="utf-8")
    if expected not in text:
        raise SystemExit(f"{path} does not pin BA_KIT_HOOK_HOME for postwrite hook")
PY
mkdir -p "${TMP_DIR}/hook-repo/module/ascii-screen"
cat > "${TMP_DIR}/hook-repo/module/ascii-screen/SCR-01.md" <<'EOF'
# SCR-01

## Fields

| Field ID | Field Name | Control Type | Display Rules | Behaviour Rules | Validation Rules |
|---|---|---|---|---|---|
| SCR-01-F01 | Email | `unknown_control` | Label: Email | (default) | - |

## Behaviour Notes

Navigate to SCR-02 after success.
EOF
printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "${TMP_DIR}/hook-repo/module/ascii-screen/SCR-01.md" \
  | BA_KIT_HOOK_HOME="${ROOT_DIR}" bash scripts/hooks/postwrite-guardrail.sh > "${TMP_DIR}/postwrite-hook.out"
grep -q "SCREEN CT:" "${TMP_DIR}/postwrite-hook.out"
grep -q "REF: SCR-02 referenced" "${TMP_DIR}/postwrite-hook.out"
if grep -q "SCR-01-F01 referenced" "${TMP_DIR}/postwrite-hook.out"; then
  echo "postwrite hook incorrectly treats field IDs as screen references" >&2
  cat "${TMP_DIR}/postwrite-hook.out" >&2
  exit 1
fi

echo "6/6 compile-srs gate integration"
COMPILE_REPO="${TMP_DIR}/compile-repo"
mkdir -p \
  "${COMPILE_REPO}/core" \
  "${COMPILE_REPO}/templates" \
  "${COMPILE_REPO}/plans/demo-260609-1500/02_backbone" \
  "${COMPILE_REPO}/plans/demo-260609-1500/03_modules/auth/srs" \
  "${COMPILE_REPO}/plans/demo-260609-1500/03_modules/auth/usecases" \
  "${COMPILE_REPO}/plans/demo-260609-1500/03_modules/auth/ascii-screen"
cp core/contract.yaml "${COMPILE_REPO}/core/contract.yaml"
cp templates/srs-template.md "${COMPILE_REPO}/templates/srs-template.md"
cp -R templates/html "${COMPILE_REPO}/templates/html"
cp templates/control-type-library-template.md "${COMPILE_REPO}/plans/demo-260609-1500/02_backbone/control-type-library.md"
cat > "${COMPILE_REPO}/plans/demo-260609-1500/02_backbone/common-rules.md" <<'EOF'
| code | type | rule_statement | applies_to | edge_cases | owner | status | source | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CR-VAL-01 | VAL | Email required | Email | Email trống: hiện lỗi. | Lead BA | active | test | — |
EOF
cat > "${COMPILE_REPO}/plans/demo-260609-1500/03_modules/auth/srs/spec.md" <<'EOF'
## Yêu cầu chức năng
| Mã (ID) | Yêu cầu (Requirement) | Ưu tiên (Priority) | Nguồn (Source) | Tiêu chí chấp nhận (Acceptance Criteria) |
| --- | --- | --- | --- | --- |
| FR-auth-001 | User điền email để đăng nhập | Must | test | Email hợp lệ được chấp nhận |
EOF
cat > "${COMPILE_REPO}/plans/demo-260609-1500/03_modules/auth/usecases/index.md" <<'EOF'
| ID | File |
|---|---|
| UC-login | usecases/uc-login.md |
EOF
cat > "${COMPILE_REPO}/plans/demo-260609-1500/03_modules/auth/usecases/uc-login.md" <<'EOF'
# UC-login: Đăng nhập
**Mã UC (Use Case ID):** UC-login
**Tác nhân chính (Primary Actor):** User
**Điều kiện tiên quyết (Preconditions):** User mở màn hình đăng nhập
**Hậu điều kiện (Postconditions):** User đăng nhập thành công
EOF
cat > "${COMPILE_REPO}/plans/demo-260609-1500/03_modules/auth/ascii-screen/index.md" <<'EOF'
| ID | File |
|---|---|
| SCR-01 | ascii-screen/SCR-01.md |
EOF
cat > "${COMPILE_REPO}/plans/demo-260609-1500/03_modules/auth/ascii-screen/SCR-01.md" <<'EOF'
# SCR-01: Đăng nhập

## Fields

| Field ID | Field Name | Control Type | Display Rules | Behaviour Rules | Validation Rules |
|---|---|---|---|---|---|
| SCR-01-F01 | Email | `text_input` | Label: Email | (default) | CR-VAL-01 -> MSG-ERR-01 inline |

## Control States

| Control | State | Condition |
|---------|-------|-----------|
| Email | error | Email trống |

## Message Placement

| Message Code | Surface | Trigger Condition | Position | Dismiss |
|---|---|---|---|---|
| MSG-ERR-01 | inline | Email trống | Dưới field Email | — |

## States

| State ID | Name | Description |
|---|---|---|
| SCR-01-DEFAULT | Default | Email trống |

## ASCII Wireframe

```text
+------------------+
| Email [        ] |
| ▼ MSG-ERR-01    |
+------------------+
```

Message Zones:
  Inline: dưới field Email (MSG-ERR-01)
EOF
python3 scripts/compile-srs.py --repo "${COMPILE_REPO}" --slug demo --date 260609-1500 --module auth >/dev/null
grep -q "material-symbols-outlined" "${COMPILE_REPO}/plans/demo-260609-1500/04_compiled/auth/compiled-srs.html"
python3 scripts/check-freshness.py --repo "${COMPILE_REPO}" --slug demo --date 260609-1500 --module auth --json > "${TMP_DIR}/compile-freshness.json"
python3 - "${TMP_DIR}/compile-freshness.json" <<'PY'
import json, sys
data = json.loads(open(sys.argv[1], encoding="utf-8").read())
if data["status"] != "FRESH":
    raise SystemExit(f"compiled receipt should be FRESH, got {data}")
PY
set +e
python3 scripts/doctor-srs.py "${COMPILE_REPO}/plans/demo-260609-1500/03_modules/auth" --repo "${COMPILE_REPO}" --json > "${TMP_DIR}/doctor.json"
set -e
python3 - "${TMP_DIR}/doctor.json" <<'PY'
import json, sys
data = json.loads(open(sys.argv[1], encoding="utf-8").read())
cmds = "\n".join(check["cmd"] for check in data["checks"])
required = [
    "check-control-type-compliance.py",
    "check-message-placement.py",
    "validate-cr-coverage.py",
    "check-terminology-consistency.py",
    "check-freshness.py",
]
missing = [item for item in required if item not in cmds]
if missing:
    raise SystemExit(f"doctor-srs did not invoke new guardrails: {missing}")
PY

echo "Control type behaviour guardrail smoke test passed"
