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

printf 'Guardrail hardening smoke: %s\n' "${TMP_DIR}"

mkdir -p "${TMP_DIR}/core"
cp "${ROOT_DIR}/core/contract.yaml" "${TMP_DIR}/core/contract.yaml"
cp "${ROOT_DIR}/core/contract-behavior.md" "${TMP_DIR}/core/contract-behavior.md"

STATUS_JSON="${TMP_DIR}/status-preflight.json"
python3 "${ROOT_DIR}/scripts/guardrail-preflight.py" \
  --repo "${TMP_DIR}" \
  --command status \
  --slug smoke-project \
  --date 20260424 \
  --output "${STATUS_JSON}" >/dev/null

python3 - "${STATUS_JSON}" <<'PY' || fail "status guardrail scope drifted"
import json
import pathlib
import sys

data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
allow_reads = data.get("allow_reads", [])
action_guardrail = data.get("action_guardrail", {})
required_suffixes = (
    "/PROJECT-HOME.md",
    "/02_backbone/project-memory.md",
    "/02_backbone/project-memory/index.md",
)
blocked_suffixes = (
    "/01_intake/intake.md",
    "/01_intake/plan.md",
    "/02_backbone/backbone.md",
)
for suffix in required_suffixes:
    if not any(path.endswith(suffix) for path in allow_reads):
        raise SystemExit(f"missing required compact read: {suffix}")
for suffix in blocked_suffixes:
    if any(path.endswith(suffix) for path in allow_reads):
        raise SystemExit(f"unexpected broad read allowed: {suffix}")
if action_guardrail.get("required"):
    raise SystemExit("status should not emit a required backbone action guardrail")
if data.get("visible_warning"):
    raise SystemExit(f"expected no project-home conflict warning, got {data.get('visible_warning')}")
PY
printf '  OK: status/next compact allowlist stays narrow\n'

PROJECT_ROOT="${TMP_DIR}/plans/smoke-project-20260424"
mkdir -p "${PROJECT_ROOT}/02_backbone" "${PROJECT_ROOT}/03_modules/auth-flow"

cat > "${PROJECT_ROOT}/02_backbone/backbone.md" <<'EOF'
# Backbone

## Existing Section

The routed section does not exist under the indexed heading.
EOF

SOURCE_HASH="$(python3 - "${PROJECT_ROOT}/02_backbone/backbone.md" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
)"

cat > "${PROJECT_ROOT}/02_backbone/backbone-index.md" <<EOF
# Chỉ mục backbone (Backbone Index)

## Metadata

| Field | Value |
| --- | --- |
| index_type | backbone |
| source_artifact | \`plans/smoke-project-20260424/02_backbone/backbone.md\` |
| source_hash | \`${SOURCE_HASH}\` |
| generated_at | \`2026-05-14T17:30:00Z\` |
| generated_by_command | \`ba-start backbone\` |
| validated_at | \`2026-05-15T08:00:00Z\` |
| validated_by | \`scripts/validate-index-quality.py\` |
| stale_status | current |
| coverage_summary | \`auth-flow coverage\` |

## Section Index

| Section | Anchor / Heading | Trace IDs | Module / Feature | Short Summary |
| --- | --- | --- | --- | --- |
| Auth Flow | Missing Section | FR-01 | auth-flow/login | Login scope |
EOF

FRD_JSON="${TMP_DIR}/frd-preflight.json"
python3 "${ROOT_DIR}/scripts/guardrail-preflight.py" \
  --repo "${TMP_DIR}" \
  --command frd \
  --slug smoke-project \
  --date 20260424 \
  --module auth-flow \
  --output "${FRD_JSON}" >/dev/null

python3 - "${FRD_JSON}" <<'PY' || fail "frd excerpt extractability did not fail closed"
import json
import pathlib
import sys

data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
index_state = data.get("indexes", {}).get("backbone_index", {})
action_guardrail = data.get("action_guardrail", {})
if data.get("status") != "block":
    raise SystemExit(f"expected block status, got {data.get('status')}")
if data.get("reason") != "backbone_index_stale":
    raise SystemExit(f"expected backbone_index_stale, got {data.get('reason')}")
if index_state.get("reason") != "source_excerpt_missing":
    raise SystemExit(f"expected source_excerpt_missing, got {index_state.get('reason')}")
if not action_guardrail.get("required"):
    raise SystemExit("expected per-action backbone guardrail for frd")
if action_guardrail.get("navigation_source") != "backbone_index":
    raise SystemExit(f"expected navigation_source=backbone_index, got {action_guardrail.get('navigation_source')}")
PY
printf '  OK: frd blocks when routed excerpt cannot be extracted\n'

printf 'Guardrail hardening smoke passed.\n'
