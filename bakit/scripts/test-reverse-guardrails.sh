#!/usr/bin/env bash
# test-reverse-guardrails.sh
#
# Smoke tests for reverse guardrail scripts:
#   - py_compile all reverse-*.py
#   - invalid input exits 1
#   - valid minimal preflight exits 0

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

ok() {
  printf '  OK: %s\n' "$1"
}

printf 'Reverse guardrail smoke tests\n\n'

for script in "${ROOT_DIR}"/scripts/reverse-*.py; do
  python3 -m py_compile "${script}"
done
ok "py_compile passes for reverse-*.py"

INVALID_REPO="${TMP_DIR}/invalid-repo"
mkdir -p "${INVALID_REPO}"
set +e
python3 "${ROOT_DIR}/scripts/reverse-preflight.py" \
  --repo "${INVALID_REPO}" \
  --slug test-project \
  --date 20260424 >"${TMP_DIR}/invalid.json" 2>"${TMP_DIR}/invalid.stderr"
invalid_status=$?
set -e
if [ "${invalid_status}" -ne 1 ]; then
  fail "reverse-preflight invalid input exited ${invalid_status}, expected 1"
fi
invalid_block_code="$(python3 - "${TMP_DIR}/invalid.json" <<'PY'
import json
import sys
print(json.loads(open(sys.argv[1], encoding="utf-8").read()).get("block_code", ""))
PY
)"
if [ "${invalid_block_code}" != "REVERSE_CONTRACT_INVALID" ]; then
  fail "reverse-preflight invalid input block_code=${invalid_block_code}, expected REVERSE_CONTRACT_INVALID"
fi
ok "reverse-preflight invalid input exits 1"

PROJECT_ROOT="${ROOT_DIR}/plans/test-project-20260424"
mkdir -p "${PROJECT_ROOT}/00_reverse"
cat >"${PROJECT_ROOT}/00_reverse/reverse-baseline-lock.json" <<'EOF'
{
  "documented_commit": "8aca3a5",
  "scan_timestamp": "2026-05-15T14:48:00Z",
  "focus_selection": ["api"],
  "locked_files": ["README.md"]
}
EOF

if ! python3 "${ROOT_DIR}/scripts/reverse-preflight.py" \
  --repo "${ROOT_DIR}" \
  --slug test-project \
  --date 20260424 >/dev/null 2>"${TMP_DIR}/valid.stderr"; then
  cat "${TMP_DIR}/valid.stderr" >&2 || true
  fail "reverse-preflight valid minimal input should exit 0"
fi
ok "reverse-preflight valid minimal input exits 0"
rm -rf "${PROJECT_ROOT}"

printf '\nReverse guardrail smoke tests passed.\n'
