#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LICENSE_FILE="${ROOT_DIR}/LICENSE"
README_FILE="${ROOT_DIR}/README.md"
CHECKLIST_FILE="${ROOT_DIR}/docs/maintainer-release-checklist.md"
PLACEHOLDER_PATTERN='TODO|placeholder|example'
MIT_PATTERN='MIT License|Permission is hereby granted, free of charge|deal in the Software without restriction'
CHECKLIST_LICENSE_VERIFY_PATTERN='verify [`"]?LICENSE[`"]? is the BA-kit Commercial License and does not contain MIT wording'
CHECKLIST_ACCESS_PATTERN='verify repo access for any legal entity that purchased or was granted access (is granted as |is )?read-only unless an exception is approved'
CHECKLIST_ENTITY_SCOPE_PATTERN='verify customer use rights are limited to a single legal entity'
CHECKLIST_ACCESS_APPROVAL_PATTERN='verify any affiliate, contractor, or client access request has a separate written commercial approval'
CHECKLIST_COMMERCIAL_AGREEMENT_PATTERN='verify the active order form, invoice, or MSA does not conflict with the root [`"]?LICENSE[`"]?'
CHECKLIST_README_PARITY_PATTERN='verify README licensing language matches the current commercial model before each release or sales handoff'
LICENSE_ENTITY_SCOPE_PATTERN='licensed to (a )?single legal entity|licensed to one legal entity|for use by (a )?single legal entity|for use by one legal entity|(single|one) legal entity only|"Licensee" means the single legal entity that purchased or was granted access'
LICENSE_REDISTRIBUTION_PATTERN='do not redistribute|may not redistribute|must not redistribute|redistribution (is )?prohibited|not for redistribution|no redistribution rights|redistribute,.*available to any third party'
README_ENTITY_SCOPE_PATTERN='single legal entity that purchased or was granted access'
README_INTERNAL_USE_PATTERN='use, privately fork, and internally customize BA-kit only within|internally customize BA-kit only within'

normalized_blocks() {
  awk '
    function normalize(text) {
      gsub(/[[:space:]]+/, " ", text)
      sub(/^ /, "", text)
      sub(/ $/, "", text)
      return text
    }

    function flush_block() {
      if (block != "") {
        print normalize(block)
        block = ""
        block_lines = 0
      }
    }

    function is_table_row(line) {
      return line ~ /^[[:space:]]*\|.*\|[[:space:]]*$/
    }

    function is_list_item(line) {
      return line ~ /^[[:space:]]*([-*+]|[0-9]+\.)[[:space:]]+/
    }

    function is_fence(line) {
      return line ~ /^[[:space:]]*(```|~~~)/
    }

    function is_heading(line) {
      return line ~ /^[[:space:]]*#{1,6}[[:space:]]+/
    }

    function is_thematic_break(line) {
      return line ~ /^[[:space:]]{0,3}([-*_][[:space:]]*){3,}$/
    }

    function is_setext_underline(line) {
      return line ~ /^[[:space:]]*(=+|-+)[[:space:]]*$/
    }

    function is_image_only(line) {
      return line ~ /^[[:space:]]*!\[[^][]*\]\([^()]*\)[[:space:]]*$/
    }

    function starts_comment(line) {
      return line ~ /^[[:space:]]*<!--/
    }

    function is_block_boundary(line) {
      return is_table_row(line) || is_list_item(line) || is_fence(line) || starts_comment(line) || is_heading(line) || is_thematic_break(line)
    }

    {
      line = $0
      gsub(/\r/, "", line)

      if (in_comment) {
        if (line ~ /-->/) {
          in_comment = 0
        }
        next
      }

      if (is_fence(line)) {
        flush_block()
        in_fence = !in_fence
        next
      }

      if (in_fence) {
        next
      }

      if (starts_comment(line)) {
        flush_block()
        if (line !~ /-->/) {
          in_comment = 1
        }
        next
      }

      if (line ~ /^[[:space:]]*>/) {
        flush_block()
        in_blockquote = 1
        next
      }

      if (in_blockquote) {
        if (line ~ /^[[:space:]]*$/) {
          in_blockquote = 0
        } else if (is_block_boundary(line)) {
          in_blockquote = 0
        } else {
          next
        }
      }

      if (block_lines == 1 && is_setext_underline(line)) {
        block = ""
        block_lines = 0
        next
      }

      if (is_table_row(line)) {
        flush_block()
        print normalize(line)
        next
      }

      if (line ~ /^[[:space:]]*$/) {
        flush_block()
        next
      }

      if (is_image_only(line)) {
        flush_block()
        next
      }

      if (is_list_item(line)) {
        flush_block()
        block = line
        block_lines = 1
        next
      }

      if (block == "") {
        block = line
        block_lines = 1
      } else {
        block = block " " line
        block_lines++
      }
    }

    END {
      flush_block()
    }
  ' "$1"
}

block_is_usable() {
  local block="$1"
  ! printf '%s\n' "${block}" | grep -Eqi "${PLACEHOLDER_PATTERN}"
}

has_match() {
  local file="$1"
  local pattern="$2"
  local block

  while IFS= read -r block; do
    if block_is_usable "${block}" &&
      printf '%s\n' "${block}" | grep -Eqi "${pattern}"; then
      return 0
    fi
  done < <(normalized_blocks "${file}")

  return 1
}

require_match() {
  local file="$1"
  local description="$2"
  local pattern="$3"

  if has_match "${file}" "${pattern}"; then
    return 0
  fi

  echo "FAIL: ${description}" >&2
  exit 1
}

has_mit_wording() {
  grep -Eqi "${MIT_PATTERN}" "$1"
}

assert_match() {
  local file="$1"
  local pattern="$2"
  local description="$3"

  if ! has_match "${file}" "${pattern}"; then
    echo "SELF-TEST FAIL: ${description}" >&2
    exit 1
  fi
}

assert_no_match() {
  local file="$1"
  local pattern="$2"
  local description="$3"

  if has_match "${file}" "${pattern}"; then
    echo "SELF-TEST FAIL: ${description}" >&2
    exit 1
  fi
}

assert_mit_wording() {
  local file="$1"
  local description="$2"

  if ! has_mit_wording "${file}"; then
    echo "SELF-TEST FAIL: ${description}" >&2
    exit 1
  fi
}

assert_run_checks_fail() {
  local license_file="$1"
  local readme_file="$2"
  local checklist_file="$3"
  local expected_message="$4"
  local output_file

  output_file="$(mktemp)"

  if (
    LICENSE_FILE="${license_file}"
    README_FILE="${readme_file}"
    CHECKLIST_FILE="${checklist_file}"
    run_checks
  ) >"${output_file}" 2>&1; then
    rm -f "${output_file}"
    echo "SELF-TEST FAIL: ${expected_message}" >&2
    exit 1
  fi

  if ! grep -Fq "${expected_message}" "${output_file}"; then
    cat "${output_file}" >&2
    rm -f "${output_file}"
    echo "SELF-TEST FAIL: expected failure output to contain: ${expected_message}" >&2
    exit 1
  fi

  rm -f "${output_file}"
}

run_self_test() {
  local tmp_dir
  local wrapped_file
  local table_file
  local bullets_file
  local mit_file
  local placeholder_file
  local fenced_file
  local blockquote_file
  local lazy_blockquote_file
  local comment_file
  local setext_file
  local image_file
  local approved_scope_file
  local approved_redistribution_file
  local approved_checklist_file
  local legacy_checklist_file
  local legacy_access_checklist_file
  local approved_readme_file
  local valid_readme_file
  local weak_readme_entity_file
  local weak_readme_internal_file
  local readme_mit_file
  local checklist_mit_file
  local valid_license_file

  tmp_dir="$(mktemp -d)"
  wrapped_file="${tmp_dir}/wrapped.txt"
  table_file="${tmp_dir}/table.md"
  bullets_file="${tmp_dir}/bullets.md"
  mit_file="${tmp_dir}/mit.txt"
  placeholder_file="${tmp_dir}/placeholder.md"
  fenced_file="${tmp_dir}/fenced.md"
  blockquote_file="${tmp_dir}/blockquote.md"
  lazy_blockquote_file="${tmp_dir}/lazy-blockquote.md"
  comment_file="${tmp_dir}/comment.md"
  setext_file="${tmp_dir}/setext.md"
  image_file="${tmp_dir}/image.md"
  approved_scope_file="${tmp_dir}/approved-scope.txt"
  approved_redistribution_file="${tmp_dir}/approved-redistribution.txt"
  approved_checklist_file="${tmp_dir}/approved-checklist.md"
  legacy_checklist_file="${tmp_dir}/legacy-checklist.md"
  legacy_access_checklist_file="${tmp_dir}/legacy-access-checklist.md"
  approved_readme_file="${tmp_dir}/approved-readme.md"
  valid_readme_file="${tmp_dir}/valid-readme.md"
  weak_readme_entity_file="${tmp_dir}/weak-readme-entity.md"
  weak_readme_internal_file="${tmp_dir}/weak-readme-internal.md"
  readme_mit_file="${tmp_dir}/readme-mit.md"
  checklist_mit_file="${tmp_dir}/checklist-mit.md"
  valid_license_file="${tmp_dir}/valid-license.txt"
  trap 'rm -rf "'"${tmp_dir}"'"' RETURN

  cat >"${wrapped_file}" <<'EOF'
This Commercial
License is granted
for use by a
single legal entity only.
EOF

  cat >"${table_file}" <<'EOF'
| Check | Status | Evidence |
| --- | --- | --- |
| Repository access restriction | PASS | verify repo access for any legal entity that purchased or was granted access is read-only unless an exception is approved |
EOF

  cat >"${bullets_file}" <<'EOF'
- verify repo access for any legal entity that purchased or was granted access is read-only
- unless an exception is approved
EOF

  cat >"${mit_file}" <<'EOF'
Permission is hereby granted, free of charge, to any person obtaining a copy
EOF

  cat >"${placeholder_file}" <<'EOF'
TODO: Commercial License
placeholder: verify the Commercial License
example: read-only access to this repository does not grant redistribution rights
EOF

  cat >"${fenced_file}" <<'EOF'
```md
Commercial License
read-only access to this repository does not grant redistribution rights
verify the Commercial License
```
EOF

  cat >"${blockquote_file}" <<'EOF'
> Commercial License
> read-only access to this repository does not grant redistribution rights
EOF

  cat >"${lazy_blockquote_file}" <<'EOF'
> Commercial License
read-only access to this repository does not grant redistribution rights
verify the Commercial License

Ordinary prose starts here.
EOF

  cat >"${comment_file}" <<'EOF'
<!--
Commercial License
verify the Commercial License
read-only access to this repository does not grant redistribution rights
-->
EOF

  cat >"${setext_file}" <<'EOF'
Commercial License
------------------

read-only access to this repository does not grant redistribution rights
===========================================================
EOF

  cat >"${image_file}" <<'EOF'
![Commercial License](license.png)
![read-only access to this repository does not grant redistribution rights](evidence.png)
EOF

  cat >"${approved_scope_file}" <<'EOF'
"Licensee" means the single legal entity that purchased or was granted access
to the Software under this license.
EOF

  cat >"${approved_redistribution_file}" <<'EOF'
- redistribute, publish, disclose, transmit, or otherwise make the Software
  available to any third party;
EOF

  cat >"${approved_checklist_file}" <<'EOF'
- verify `LICENSE` is the BA-kit Commercial License and does not contain MIT wording
- verify repo access for any legal entity that purchased or was granted access is read-only unless an exception is approved
- verify customer use rights are limited to a single legal entity
- verify any affiliate, contractor, or client access request has a separate written commercial approval
- verify the active order form, invoice, or MSA does not conflict with the root `LICENSE`
- verify README licensing language matches the current commercial model before each release or sales handoff
EOF

  cat >"${legacy_checklist_file}" <<'EOF'
- verify the Commercial License
- licensed to one legal entity
- signed order form
EOF

  cat >"${legacy_access_checklist_file}" <<'EOF'
- verify `LICENSE` is the BA-kit Commercial License and does not contain MIT wording
- verify repo access for paid customers is granted as read-only unless an exception is approved
- verify customer use rights are limited to a single legal entity
- verify any affiliate, contractor, or client access request has a separate written commercial approval
- verify the active order form, invoice, or MSA does not conflict with the root `LICENSE`
- verify README licensing language matches the current commercial model before each release or sales handoff
EOF

  cat >"${approved_readme_file}" <<'EOF'
BA-kit is distributed under a commercial proprietary source-available license.
Access to this repository does not grant redistribution rights. Customers may
use, privately fork, and internally customize BA-kit only within the single
legal entity that purchased or was granted access, subject to the terms in
`LICENSE` and any applicable order form or MSA.
EOF

  cat >"${valid_readme_file}" <<'EOF'
BA-kit is distributed under a commercial proprietary source-available license.
This commercial proprietary license is provided on a source-available basis.

Access to this repository does not grant redistribution rights. Customers may
use, privately fork, and internally customize BA-kit only within the single
legal entity that purchased or was granted access, subject to the terms in
`LICENSE` and any applicable order form or MSA.
EOF

  cat >"${weak_readme_entity_file}" <<'EOF'
BA-kit is distributed under a commercial proprietary source-available license.
Access to this repository does not grant redistribution rights. Customers may
use, privately fork, and internally customize BA-kit only within the single
legal entity that purchased the license, subject to the terms in `LICENSE`.
EOF

  cat >"${weak_readme_internal_file}" <<'EOF'
BA-kit is distributed under a commercial proprietary source-available license.
Access to this repository does not grant redistribution rights. Customers may
adapt BA-kit for business operations only within the single legal entity that
purchased or was granted access, subject to the terms in `LICENSE`.
EOF

  cat >"${readme_mit_file}" <<'EOF'
BA-kit is distributed under a commercial proprietary source-available license.
Permission is hereby granted, free of charge, to any person obtaining a copy.
EOF

  cat >"${checklist_mit_file}" <<'EOF'
- verify `LICENSE` is the BA-kit Commercial License and does not contain MIT wording
- Permission is hereby granted, free of charge, to any person obtaining a copy
EOF

  cat >"${valid_license_file}" <<'EOF'
BA-kit Commercial License

"Licensee" means the single legal entity that purchased or was granted access
to the Software under this license.

You may not redistribute the Software or otherwise make it available to any
third party.
EOF

  assert_match "${wrapped_file}" 'Commercial License' "wrapped paragraphs should normalize into one block"
  assert_match "${wrapped_file}" "${LICENSE_ENTITY_SCOPE_PATTERN}" "wrapped licensing scope clause should match after normalization"
  assert_match "${approved_scope_file}" "${LICENSE_ENTITY_SCOPE_PATTERN}" "approved LICENSE scope clause should match after normalization"
  assert_match "${approved_redistribution_file}" "${LICENSE_REDISTRIBUTION_PATTERN}" "approved redistribution restriction should match after normalization"
  assert_match "${approved_checklist_file}" "${CHECKLIST_LICENSE_VERIFY_PATTERN}" "approved checklist wording should satisfy Commercial License verification"
  assert_match "${approved_checklist_file}" "${CHECKLIST_ACCESS_PATTERN}" "approved checklist wording should satisfy repository access verification"
  assert_match "${approved_checklist_file}" "${CHECKLIST_ENTITY_SCOPE_PATTERN}" "approved checklist wording should satisfy single legal entity verification"
  assert_match "${approved_checklist_file}" "${CHECKLIST_ACCESS_APPROVAL_PATTERN}" "approved checklist wording should satisfy affiliate access approval verification"
  assert_match "${approved_checklist_file}" "${CHECKLIST_COMMERCIAL_AGREEMENT_PATTERN}" "approved checklist wording should satisfy order form, invoice, or MSA verification"
  assert_match "${approved_checklist_file}" "${CHECKLIST_README_PARITY_PATTERN}" "approved checklist wording should satisfy README licensing parity verification"
  assert_match "${approved_readme_file}" "${README_ENTITY_SCOPE_PATTERN}" "approved README wording should satisfy single legal entity scope verification"
  assert_match "${approved_readme_file}" "${README_INTERNAL_USE_PATTERN}" "approved README wording should satisfy internal-only customization verification"
  assert_match "${table_file}" "${CHECKLIST_ACCESS_PATTERN}" "table rows should remain self-contained blocks"
  assert_no_match "${bullets_file}" "${CHECKLIST_ACCESS_PATTERN}" "adjacent bullets must not combine into one block"
  assert_no_match "${legacy_checklist_file}" "${CHECKLIST_LICENSE_VERIFY_PATTERN}" "legacy Commercial License shorthand must not satisfy checklist verification"
  assert_no_match "${legacy_access_checklist_file}" "${CHECKLIST_ACCESS_PATTERN}" "legacy paid-customer access wording must not satisfy checklist verification"
  assert_no_match "${legacy_checklist_file}" "${CHECKLIST_ENTITY_SCOPE_PATTERN}" "legacy single-entity shorthand must not satisfy checklist verification"
  assert_no_match "${legacy_checklist_file}" "${CHECKLIST_COMMERCIAL_AGREEMENT_PATTERN}" "legacy agreement shorthand must not satisfy checklist verification"
  assert_no_match "${legacy_checklist_file}" "${CHECKLIST_README_PARITY_PATTERN}" "missing README parity bullet must not satisfy checklist verification"
  assert_no_match "${weak_readme_entity_file}" "${README_ENTITY_SCOPE_PATTERN}" "weakened README entity scope must not satisfy verification"
  assert_no_match "${weak_readme_internal_file}" "${README_INTERNAL_USE_PATTERN}" "weakened README internal-use scope must not satisfy verification"
  assert_mit_wording "${mit_file}" "MIT leftover wording should be detected"
  assert_no_match "${placeholder_file}" 'Commercial License' "placeholder markers must not satisfy positive checks"
  assert_no_match "${placeholder_file}" "${CHECKLIST_ACCESS_PATTERN}" "placeholder checklist text must not satisfy redistribution checks"
  assert_no_match "${fenced_file}" 'Commercial License|commercial proprietary license' "fenced code blocks must not satisfy README license checks"
  assert_no_match "${fenced_file}" "${CHECKLIST_ACCESS_PATTERN}" "fenced code blocks must not satisfy checklist redistribution checks"
  assert_no_match "${blockquote_file}" 'Commercial License|commercial proprietary license' "blockquote lines must not satisfy README license checks"
  assert_no_match "${blockquote_file}" "${CHECKLIST_ACCESS_PATTERN}" "blockquote lines must not satisfy checklist redistribution checks"
  assert_no_match "${lazy_blockquote_file}" 'Commercial License|commercial proprietary license' "lazy blockquote continuation must not satisfy README license checks"
  assert_no_match "${lazy_blockquote_file}" "${CHECKLIST_ACCESS_PATTERN}" "lazy blockquote continuation must not satisfy checklist redistribution checks"
  assert_no_match "${comment_file}" 'Commercial License|commercial proprietary license' "HTML comments must not satisfy README license checks"
  assert_no_match "${comment_file}" "${CHECKLIST_ACCESS_PATTERN}" "HTML comments must not satisfy checklist redistribution checks"
  assert_no_match "${setext_file}" 'Commercial License|commercial proprietary license' "setext headings must not satisfy README license checks"
  assert_no_match "${setext_file}" "${CHECKLIST_ACCESS_PATTERN}" "setext headings must not satisfy checklist redistribution checks"
  assert_no_match "${image_file}" 'Commercial License|commercial proprietary license' "image-only markdown lines must not satisfy README license checks"
  assert_no_match "${image_file}" "${CHECKLIST_ACCESS_PATTERN}" "image-only markdown lines must not satisfy checklist redistribution checks"
  assert_mit_wording "${readme_mit_file}" "MIT leftover wording in README should be detected"
  assert_mit_wording "${checklist_mit_file}" "MIT leftover wording in checklist should be detected"
  assert_run_checks_fail "${valid_license_file}" "${valid_readme_file}" "${legacy_access_checklist_file}" "FAIL: Release checklist must cover repository read-only access controls with no redistribution rights"
  assert_run_checks_fail "${valid_license_file}" "${readme_mit_file}" "${approved_checklist_file}" "FAIL: README still contains MIT wording"
  assert_run_checks_fail "${valid_license_file}" "${approved_readme_file}" "${checklist_mit_file}" "FAIL: Release checklist still contains MIT wording"

  trap - RETURN
  rm -rf "${tmp_dir}"
  echo "PASS: self-test"
}

run_checks() {
  if has_mit_wording "${LICENSE_FILE}"; then
    echo "FAIL: LICENSE still contains MIT wording" >&2
    exit 1
  fi

  if has_mit_wording "${README_FILE}"; then
    echo "FAIL: README still contains MIT wording" >&2
    exit 1
  fi

  if has_mit_wording "${CHECKLIST_FILE}"; then
    echo "FAIL: Release checklist still contains MIT wording" >&2
    exit 1
  fi

  require_match "${LICENSE_FILE}" \
    "LICENSE must mention commercial licensing terms" \
    'Commercial License|commercial proprietary license'

  require_match "${LICENSE_FILE}" \
    "LICENSE must restrict usage to a single legal entity" \
    "${LICENSE_ENTITY_SCOPE_PATTERN}"

  require_match "${LICENSE_FILE}" \
    "LICENSE must include redistribution restrictions" \
    "${LICENSE_REDISTRIBUTION_PATTERN}"

  require_match "${README_FILE}" \
    "README must identify the commercial or proprietary license model" \
    'Commercial License|commercial proprietary license'

  require_match "${README_FILE}" \
    "README must state that repository access does not grant redistribution rights" \
    'read-only access to (this )?repository does not grant redistribution rights|access to this repository does not grant redistribution rights|repository access does not grant redistribution rights'

  require_match "${README_FILE}" \
    "README must limit customer use to the single legal entity that purchased or was granted access" \
    "${README_ENTITY_SCOPE_PATTERN}"

  require_match "${README_FILE}" \
    "README must limit customer use to internal-only use and customization scope" \
    "${README_INTERNAL_USE_PATTERN}"

  require_match "${CHECKLIST_FILE}" \
    "Release checklist must verify the Commercial License before release" \
    "${CHECKLIST_LICENSE_VERIFY_PATTERN}"

  require_match "${CHECKLIST_FILE}" \
    "Release checklist must cover repository read-only access controls with no redistribution rights" \
    "${CHECKLIST_ACCESS_PATTERN}"

  require_match "${CHECKLIST_FILE}" \
    "Release checklist must verify single legal entity licensing scope" \
    "${CHECKLIST_ENTITY_SCOPE_PATTERN}"

  require_match "${CHECKLIST_FILE}" \
    "Release checklist must require separate written approval for affiliate, contractor, or client access" \
    "${CHECKLIST_ACCESS_APPROVAL_PATTERN}"

  require_match "${CHECKLIST_FILE}" \
    "Release checklist must reference commercial agreement validation" \
    "${CHECKLIST_COMMERCIAL_AGREEMENT_PATTERN}"

  require_match "${CHECKLIST_FILE}" \
    "Release checklist must verify README licensing language parity before release or sales handoff" \
    "${CHECKLIST_README_PARITY_PATTERN}"

  echo "PASS: commercial licensing docs are consistent"
}

if [[ "${1:-}" == "--self-test" ]]; then
  run_self_test
  exit 0
fi

run_checks
