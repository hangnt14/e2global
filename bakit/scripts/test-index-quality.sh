#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

printf 'Index quality smoke: %s\n' "${TMP_DIR}"

mkdir -p "${TMP_DIR}/core"
cp "${ROOT_DIR}/core/contract.yaml" "${TMP_DIR}/core/contract.yaml"
cp "${ROOT_DIR}/core/contract-behavior.md" "${TMP_DIR}/core/contract-behavior.md"

PROJECT_ROOT="${TMP_DIR}/plans/smoke-project-20260424"
mkdir -p "${PROJECT_ROOT}/02_backbone"

cat > "${PROJECT_ROOT}/02_backbone/backbone.md" <<'EOF'
# Backbone

## Authentication Scope

| FR ID | Requirement |
| --- | --- |
| FR-01 | User can sign in |
| FR-02 | User can reset password |

## Actors

| Actor ID | Role |
| --- | --- |
| ACT-01 | End User |
EOF

SOURCE_HASH="$(python3 - "${PROJECT_ROOT}/02_backbone/backbone.md" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
)"

write_index() {
  local stale_status="$1"
  local validated_at="$2"
  local validated_by="$3"
  local trace_ids="$4"

  cat > "${PROJECT_ROOT}/02_backbone/backbone-index.md" <<EOF
# Chỉ mục backbone (Backbone Index)

## Metadata

| Field | Value |
| --- | --- |
| index_type | backbone |
| source_artifact | \`plans/smoke-project-20260424/02_backbone/backbone.md\` |
| source_hash | \`${SOURCE_HASH}\` |
| generated_at | \`2026-05-15T09:00:00Z\` |
| generated_by_command | \`ba-start backbone\` |
| validated_at | \`${validated_at}\` |
| validated_by | \`${validated_by}\` |
| stale_status | ${stale_status} |
| coverage_summary | \`auth coverage\` |

## Section Index

| Section | Anchor / Heading | Trace IDs | Module / Feature | Short Summary |
| --- | --- | --- | --- | --- |
| Auth Scope | Authentication Scope | ${trace_ids} | auth-flow/login | Login and password reset |
| Actors | Actors | ACT-01 | auth-flow/login | Supported actors |
EOF
}

write_index "current" "" "" "FR-01"
PREFLIGHT_BLOCK="${TMP_DIR}/preflight-block.json"
python3 "${ROOT_DIR}/scripts/guardrail-preflight.py" \
  --repo "${TMP_DIR}" \
  --command frd \
  --slug smoke-project \
  --date 20260424 \
  --module auth-flow \
  --output "${PREFLIGHT_BLOCK}" >/dev/null

python3 - "${PREFLIGHT_BLOCK}" <<'PY' || fail "unvalidated current index was not blocked"
import json
import pathlib
import sys

data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
index_state = data.get("indexes", {}).get("backbone_index", {})
if data.get("status") != "block":
    raise SystemExit(f"expected block, got {data.get('status')}")
if index_state.get("reason") != "missing_metadata:validated_at,validated_by":
    raise SystemExit(f"unexpected reason: {index_state.get('reason')}")
refresh_command = data.get("refresh_command", "")
if "validate-index-quality.py" not in refresh_command:
    raise SystemExit(f"expected validator refresh command, got {refresh_command}")
PY
printf '  OK: consumer guardrail blocks current index without validation metadata\n'

write_index "unknown" "" "" "FR-01, FR-02"
VALIDATION_JSON="${TMP_DIR}/validation.json"
python3 "${ROOT_DIR}/scripts/validate-index-quality.py" \
  --repo "${TMP_DIR}" \
  --index-key backbone_index \
  --slug smoke-project \
  --date 20260424 \
  --writeback \
  --output "${VALIDATION_JSON}" >/dev/null

python3 - "${VALIDATION_JSON}" "${PROJECT_ROOT}/02_backbone/backbone-index.md" <<'PY' || fail "validator did not promote valid index"
import json
import pathlib
import sys

data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
index_text = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
if data.get("status") not in {"warn", "pass"}:
    raise SystemExit(f"expected warn/pass, got {data.get('status')}")
if data.get("suggested_stale_status") != "current":
    raise SystemExit(f"expected suggested current, got {data.get('suggested_stale_status')}")
if "| stale_status | `current` |" not in index_text:
    raise SystemExit("writeback did not set stale_status=current")
if "| validated_by | `scripts/validate-index-quality.py` |" not in index_text:
    raise SystemExit("writeback did not stamp validated_by")
PY
printf '  OK: validator can upgrade unknown index to current with writeback\n'

PREFLIGHT_OK="${TMP_DIR}/preflight-ok.json"
python3 "${ROOT_DIR}/scripts/guardrail-preflight.py" \
  --repo "${TMP_DIR}" \
  --command frd \
  --slug smoke-project \
  --date 20260424 \
  --module auth-flow \
  --output "${PREFLIGHT_OK}" >/dev/null

python3 - "${PREFLIGHT_OK}" <<'PY' || fail "validated current index did not unlock frd"
import json
import pathlib
import sys

data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if data.get("status") != "ok":
    raise SystemExit(f"expected ok, got {data.get('status')}")
action_guardrail = data.get("action_guardrail", {})
if not action_guardrail.get("required"):
    raise SystemExit("expected per-action backbone guardrail")
if action_guardrail.get("navigation_source") != "backbone_index":
    raise SystemExit(f"unexpected navigation source: {action_guardrail.get('navigation_source')}")
PY
printf '  OK: validated index unlocks frd and emits per-action backbone guardrail\n'

write_index "unknown" "" "" "FR-01"
NEGATIVE_JSON="${TMP_DIR}/validation-negative.json"
if python3 "${ROOT_DIR}/scripts/validate-index-quality.py" \
  --repo "${TMP_DIR}" \
  --index-key backbone_index \
  --slug smoke-project \
  --date 20260424 \
  --writeback \
  --output "${NEGATIVE_JSON}" >/dev/null; then
  fail "validator unexpectedly passed incomplete coverage"
fi

python3 - "${NEGATIVE_JSON}" "${PROJECT_ROOT}/02_backbone/backbone-index.md" <<'PY' || fail "validator did not report missing source coverage"
import json
import pathlib
import sys

data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
index_text = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
codes = {item["code"] for item in data.get("issues", [])}
if data.get("status") != "fail":
    raise SystemExit(f"expected fail, got {data.get('status')}")
if "source_coverage_missing" not in codes:
    raise SystemExit(f"missing source_coverage_missing issue: {sorted(codes)}")
if "| validated_by | `scripts/validate-index-quality.py` |" in index_text:
    raise SystemExit("failed validation must not stamp validated_by")
if "| stale_status | `stale` |" not in index_text:
    raise SystemExit("failed validation did not write stale_status=stale")
PY
printf '  OK: validator fails when source IDs are not fully covered\n'

printf 'Index quality smoke passed.\n'
