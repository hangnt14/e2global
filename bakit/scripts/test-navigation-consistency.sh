#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT
PYTHON_BIN="${PYTHON:-python3}"

DESIGN_DOC="${TMP_DIR}/DESIGN.md"
VALID_SCREEN_CONTRACT="${TMP_DIR}/srs-group-c.valid.md"
INVALID_SCREEN_CONTRACT="${TMP_DIR}/srs-group-c.invalid.md"

cat >"${DESIGN_DOC}" <<'EOF'
# DESIGN.md - Test Project

## 2. Information Architecture (Portals & Navigation)

### 2.2 Navigation Schema

| Portal ID | Nav Schema ID | Navigation Pattern | Menu Item List | Default Landing | Active / Selected Rule | Breadcrumb / Back Rule | Hidden / Contextual Nav Exceptions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PORTAL-ADM | NAV-ADM-01 | Sidebar | Dashboard, Vendor Approvals, Product Approvals, Finance | Dashboard | Highlight item by route prefix | Breadcrumbs from level 2 | Approval modals hide menu |
| PORTAL-VEN | NAV-VEN-01 | Sidebar | Dashboard, Profile & KYC, Products, Orders, Settlements | Dashboard | Highlight item by route prefix | Breadcrumbs from level 2 | Registration wizard hides menu |
EOF

cat >"${VALID_SCREEN_CONTRACT}" <<'EOF'
# Screen Contract Plus

| Screen ID | Screen Name | Classification | Parent Screen | Portal ID | Access Role / Actor | Nav Schema ID | Expected Active Menu Item | Navigation Region Visible | Breadcrumb / Back Behavior | Global vs Local Navigation | Linked Use Cases | Entry / Exit | Key Actions | Required States | Documentation Level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SCR-ADM-PROD-REV | Product Approval | Primary screen | N/A | PORTAL-ADM | Admin | NAV-ADM-01 | Product Approvals | Yes | Breadcrumbs from level 2 | Global sidebar | UC-01 | Menu / Detail | Approve, Reject | Loading, Empty | Detailed |
| SCR-ADM-REJ | Reject Reason Modal | Primary screen | SCR-ADM-PROD-REV | PORTAL-ADM | Admin | NAV-ADM-01 | Product Approvals | No | Close to parent | Local overlay only | UC-01 | Reject / Submit | Submit, Cancel | Error | Detailed |
EOF

cat >"${INVALID_SCREEN_CONTRACT}" <<'EOF'
# Screen Contract Plus

| Screen ID | Screen Name | Classification | Parent Screen | Portal ID | Access Role / Actor | Nav Schema ID | Expected Active Menu Item | Navigation Region Visible | Breadcrumb / Back Behavior | Global vs Local Navigation | Linked Use Cases | Entry / Exit | Key Actions | Required States | Documentation Level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SCR-ADM-PROD-REV | Product Approval | Primary screen | N/A | PORTAL-ADM | Admin | NAV-ADM-01 | Catalog > Approvals | Yes | Breadcrumbs from level 2 | Global sidebar | UC-01 | Menu / Detail | Approve, Reject | Loading, Empty | Detailed |
EOF

"${PYTHON_BIN}" "${ROOT_DIR}/scripts/validate-navigation-consistency.py" \
  --design "${DESIGN_DOC}" \
  --screen-contract "${VALID_SCREEN_CONTRACT}" >/dev/null

if "${PYTHON_BIN}" "${ROOT_DIR}/scripts/validate-navigation-consistency.py" \
  --design "${DESIGN_DOC}" \
  --screen-contract "${INVALID_SCREEN_CONTRACT}" >"${TMP_DIR}/invalid.out" 2>"${TMP_DIR}/invalid.err"; then
  echo "Expected invalid active menu item to fail validation" >&2
  exit 1
fi

if ! grep -q "MENU_SCHEMA_MISMATCH" "${TMP_DIR}/invalid.err"; then
  echo "Expected MENU_SCHEMA_MISMATCH in validation error" >&2
  cat "${TMP_DIR}/invalid.err" >&2
  exit 1
fi

echo "Navigation consistency checks passed."
