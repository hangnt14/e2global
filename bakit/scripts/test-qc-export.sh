#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${SCRIPT_DIR}/.." && pwd)"
FIXTURE_SRC="${REPO}/tests/qc-export"
EXPORT_SCRIPT="${REPO}/scripts/qc-export.py"
TMPDIR="$(mktemp -d)"
PASS=0
FAIL=0

cleanup() { rm -rf "${TMPDIR}"; }
trap cleanup EXIT

ok() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

# Copy fixture to temp dir so export output never lands in tracked repo
FIXTURE="${TMPDIR}/fixture"
cp -r "${FIXTURE_SRC}" "${FIXTURE}"

echo "=== ba-qc-export tests ==="
echo ""

# Test 1: happy path — export creates expected files
echo "[test 1] Happy path export"
python3 "${EXPORT_SCRIPT}" \
  --slug test-proj \
  --date 260529-2100 \
  --module payment \
  --repo "${FIXTURE}" >/dev/null 2>&1 || { fail "export command failed"; }

OUTDIR="${FIXTURE}/plans/test-proj-260529-2100/04_compiled/qc-kit/docs/BA"

[[ -f "${OUTDIR}/Common rule/common-rules.md" ]] && ok "common-rules.md exists" || fail "common-rules.md missing"
[[ -f "${OUTDIR}/Common rule/message-list.md" ]] && ok "message-list.md exists" || fail "message-list.md missing"
[[ -f "${OUTDIR}/payment/UC-checkout.md" ]] && ok "UC-checkout.md exists" || fail "UC-checkout.md missing"
[[ -f "${OUTDIR}/payment/UC-refund.md" ]] && ok "UC-refund.md exists" || fail "UC-refund.md missing"

# Test 2: exactly six top-level ## headings in exported UC (no extra ## headings)
echo ""
echo "[test 2] Six top-level ## headings"
for heading in "1. Use Case Description" "2. Screen Description" \
  "3. Validation Summary" "4. Cross-References" "5. Open Questions" "6. Changelog"; do
  grep -q "^## ${heading}" "${OUTDIR}/payment/UC-checkout.md" && \
    ok "heading '${heading}' present" || fail "heading '${heading}' missing"
done
# Verify exactly 6 total ## headings (counts all, not just numbered)
TOTAL_H2=$(grep -c '^## ' "${OUTDIR}/payment/UC-checkout.md" || true)
[[ "${TOTAL_H2}" -eq 6 ]] && ok "exactly 6 total ## headings (found ${TOTAL_H2})" \
  || fail "expected 6 total ## headings, found ${TOTAL_H2}"

# Test 3: source links present (as bold label, not ## heading)
echo ""
echo "[test 3] Source links"
grep -q "BA-kit Source Links" "${OUTDIR}/payment/UC-checkout.md" && \
  ok "source links present" || fail "source links missing"
# Must NOT be a ## heading
grep -q '^## BA-kit Source Links' "${OUTDIR}/payment/UC-checkout.md" && \
  fail "source links should not be a ## heading" || ok "source links not a ## heading"
# Source UC Path must be resolved (not N/A)
grep -q 'Source UC Path.*N/A' "${OUTDIR}/payment/UC-checkout.md" && \
  fail "source UC path is N/A" || ok "source UC path resolved"

# Test 4: disclaimer present
echo ""
echo "[test 4] Disclaimer"
grep -q "one-way handoff" "${OUTDIR}/payment/UC-checkout.md" && \
  ok "disclaimer present" || fail "disclaimer missing"

# Test 5: functional integration for UC with cross-function table
echo ""
echo "[test 5] Functional Integration"
grep -q "Functional Integration" "${OUTDIR}/payment/UC-checkout.md" && \
  ok "Functional Integration in UC-checkout" || fail "Functional Integration missing in UC-checkout"

# Test 6: UC without cross-function should still include the section
echo ""
echo "[test 6] Functional Integration section always present"
grep -q "Functional Integration" "${OUTDIR}/payment/UC-refund.md" && \
  ok "Functional Integration section exists" || fail "Functional Integration missing"

# Test 7: summary JSON
echo ""
echo "[test 7] Summary JSON"
SUMMARY="${FIXTURE}/plans/test-proj-260529-2100/04_compiled/qc-kit/qc-export-summary.json"
[[ -f "${SUMMARY}" ]] && ok "summary JSON exists" || { fail "summary JSON missing"; }
python3 -c "
import json
s = json.load(open('${SUMMARY}'))
assert s['uc_count'] == 2, 'expected 2 UCs'
assert len(s['usecases']) == 2, 'expected 2 usecase entries'
for u in s['usecases']:
    assert u.get('validation_errors') is not None, f'missing validation_errors in {u[\"uc_slug\"]}'
    assert u['validation_errors'] == [], f'unexpected validation errors in {u[\"uc_slug\"]}: {u[\"validation_errors\"]}'
" 2>/dev/null && ok "summary JSON valid (no validation errors)" || fail "summary JSON invalid or has validation errors"

# Test 8: missing module fails gracefully
echo ""
echo "[test 8] Missing module"
python3 "${EXPORT_SCRIPT}" \
  --slug test-proj \
  --date 260529-2100 \
  --module nonexistent \
  --repo "${FIXTURE}" >/dev/null 2>&1 && fail "should have failed" || ok "fails on missing module"

# Test 9: output stays under 04_compiled/qc-kit
echo ""
echo "[test 9] Default output location"
echo "${OUTDIR}" | grep -q "04_compiled/qc-kit" && ok "output in 04_compiled/qc-kit" || fail "output outside expected dir"

# Test 10: --usecase-list flag
echo ""
echo "[test 10] Usecase list flag"
python3 "${EXPORT_SCRIPT}" \
  --slug test-proj \
  --date 260529-2100 \
  --module payment \
  --repo "${FIXTURE}" \
  --usecase-list >/dev/null 2>&1
[[ -f "${OUTDIR}/payment/usecase-list.md" ]] && ok "usecase-list.md created" || fail "usecase-list.md missing"

# Test 11: external output
echo ""
echo "[test 11] External output"
python3 "${EXPORT_SCRIPT}" \
  --slug test-proj \
  --date 260529-2100 \
  --module payment \
  --repo "${FIXTURE}" \
  --external-output "${TMPDIR}/qc-out" >/dev/null 2>&1
[[ -f "${TMPDIR}/qc-out/docs/BA/payment/UC-checkout.md" ]] && \
  ok "external output works" || fail "external output failed"

# Test 12: check-write-scope boundary-aware matching — allows qc-kit but not sibling
echo ""
echo "[test 12] Write-scope boundary-aware path matching"
python3 "${REPO}/scripts/check-write-scope.py" --command qc-export \
  "plans/test-proj-260529-2100/04_compiled/qc-kit" >/dev/null 2>&1 \
  && ok "guard allows 04_compiled/qc-kit" || fail "guard blocked 04_compiled/qc-kit"
python3 "${REPO}/scripts/check-write-scope.py" --command qc-export \
  "plans/test-proj-260529-2100/04_compiled/qc-kit-backup" >/dev/null 2>&1 \
  && fail "guard should block sibling qc-kit-backup" || ok "guard blocks sibling qc-kit-backup"

# Test 13: guard blocks write to forbidden paths
echo ""
echo "[test 13] Guard blocks write to module internals"
python3 "${REPO}/scripts/check-write-scope.py" --command qc-export \
  "plans/test-proj-260529-2100/03_modules/payment/usecases" >/dev/null 2>&1 \
  && fail "should have blocked internal path" || ok "guard blocks write to 03_modules"

# Test 14: happy path through ba-kit wrapper (F#3)
echo ""
echo "[test 14] Happy path through ba-kit wrapper"
MINI_REPO="${TMPDIR}/mini-repo"
cp -r "${FIXTURE_SRC}" "${MINI_REPO}"
cp -r "${REPO}/scripts" "${MINI_REPO}/"
rm -rf "${MINI_REPO}/plans/test-proj-260529-2100/04_compiled"
BA_KIT_SOURCE_REPO="${MINI_REPO}" "${REPO}/scripts/ba-kit" qc-export \
  --slug test-proj --date 260529-2100 --module payment >/dev/null 2>&1 \
  || fail "ba-kit wrapper qc-export failed"
MINI_OUT="${MINI_REPO}/plans/test-proj-260529-2100/04_compiled/qc-kit/docs/BA"
[[ -f "${MINI_OUT}/payment/UC-checkout.md" ]] && ok "wrapper: UC-checkout.md exists" || fail "wrapper: UC-checkout.md missing"
[[ -f "${MINI_OUT}/payment/UC-refund.md" ]] && ok "wrapper: UC-refund.md exists" || fail "wrapper: UC-refund.md missing"

# Test 15: valid wrapper --external-output works and writes to resolved external dir
echo ""
echo "[test 15] ba-kit wrapper valid --external-output"
WRAP_EXT="${TMPDIR}/wrapper-qc-out"
BA_KIT_SOURCE_REPO="${MINI_REPO}" "${REPO}/scripts/ba-kit" qc-export \
  --slug test-proj --date 260529-2100 --module payment \
  --external-output "${WRAP_EXT}" >/dev/null 2>&1 \
  || fail "wrapper external-output failed"
[[ -f "${WRAP_EXT}/docs/BA/payment/UC-checkout.md" ]] && ok "wrapper external: UC-checkout.md exists" || fail "wrapper external: UC-checkout.md missing"
[[ -f "${WRAP_EXT}/docs/BA/payment/UC-refund.md" ]] && ok "wrapper external: UC-refund.md exists" || fail "wrapper external: UC-refund.md missing"

# Test 16: relative --external-output inside repo is blocked (F#1 regression)
echo ""
echo "[test 16] ba-kit blocks relative internal --external-output"
pushd "${TMPDIR}" >/dev/null
BA_KIT_SOURCE_REPO="${MINI_REPO}" "${REPO}/scripts/ba-kit" qc-export \
  --slug test-proj --date 260529-2100 --module payment \
  --external-output "plans/test-proj-260529-2100/03_modules/payment/usecases" >/dev/null 2>&1 \
  && fail "should block relative internal external-output" || ok "blocks relative internal external-output"
popd >/dev/null

# Test 17: --external-output . (exact repo root) is blocked (F#1 regression)
echo ""
echo "[test 17] ba-kit blocks --external-output . (repo root)"
pushd "${MINI_REPO}" >/dev/null
BA_KIT_SOURCE_REPO="${MINI_REPO}" "${REPO}/scripts/ba-kit" qc-export \
  --slug test-proj --date 260529-2100 --module payment \
  --external-output . >/dev/null 2>&1 \
  && fail "should block repo-root external-output" || ok "blocks repo-root external-output"
popd >/dev/null

# Test 18: direct script blocks internal --external-output (guard now self-resolves)
echo ""
echo "[test 18] Direct script blocks internal external-output"
python3 "${EXPORT_SCRIPT}" \
  --slug test-proj --date 260529-2100 --module payment \
  --repo "${FIXTURE}" \
  --external-output "${FIXTURE}/plans/test-proj-260529-2100/03_modules/payment/usecases" \
  >/dev/null 2>&1 && fail "direct: should block internal path" || ok "direct: blocks internal path"

# Test 19: direct script blocks repo-root external-output
echo ""
echo "[test 19] Direct script blocks repo-root external-output"
python3 "${EXPORT_SCRIPT}" \
  --slug test-proj --date 260529-2100 --module payment \
  --repo "${FIXTURE}" \
  --external-output "${FIXTURE}" \
  >/dev/null 2>&1 && fail "direct: should block repo root" || ok "direct: blocks repo root"

echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="
exit $((FAIL > 0 ? 1 : 0))
