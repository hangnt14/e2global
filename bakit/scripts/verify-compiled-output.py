#!/usr/bin/env python3
"""Verify compiled srs.md has no metadata leakage or unfilled placeholders.

Runs as post-compile gate — after compile-srs.py, before md-to-html.py.

Usage:
    python3 scripts/verify-compiled-output.py path/to/srs.md [--json]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL | re.MULTILINE)
UNFILLED_PLACEHOLDER_RE = re.compile(
    r"\[TBD\]|\[Placeholder[^\]]*\]|\[placeholder[^\]]*\]|\[Tên dự án\]|\[Tên module\]|\[Tên portal[^\]]*\]|\[Tên màn hình\]|\[Tên UC\]|\[Project\]|\[Module\]|\[Screen Name\]",
    re.IGNORECASE,
)
INDEX_ONLY_SECTION_RE = re.compile(
    r"^#{2,3}\s+[^\n]+\n\n\|[^\n]+\|\n\|[-\s|]+\|\n(?!\|[^|\n]+\|)",
    re.MULTILINE,
)


def verify(compiled_path: Path) -> dict[str, Any]:
    text = compiled_path.read_text(encoding="utf-8")
    issues: list[dict[str, Any]] = []

    # Check 1: YAML frontmatter leaked from component files
    fm_matches = YAML_FRONTMATTER_RE.findall(text)
    if fm_matches:
        issues.append({
            "severity": "BLOCK",
            "code": "metadata_leaked",
            "message": (
                f"Found {len(fm_matches)} YAML frontmatter block(s) in compiled output. "
                "All component file frontmatter must be stripped during compile."
            ),
        })

    # Check 2: Unfilled placeholders
    ph_matches = UNFILLED_PLACEHOLDER_RE.findall(text)
    unique_ph = sorted(set(ph_matches))
    if unique_ph:
        issues.append({
            "severity": "BLOCK",
            "code": "unfilled_placeholder",
            "message": f"Found {len(unique_ph)} unique unfilled placeholder(s): {unique_ph[:10]}",
        })

    # Check 3: Index-only sections (heading + table header, no data rows)
    empty_sections = INDEX_ONLY_SECTION_RE.findall(text)
    if empty_sections:
        issues.append({
            "severity": "WARN",
            "code": "index_only_section",
            "message": (
                f"Found {len(empty_sections)} section(s) with table header but no data rows. "
                "Section may be index-only — inline full content from canon sources."
            ),
        })

    has_blocks = any(i["severity"] == "BLOCK" for i in issues)
    return {
        "path": str(compiled_path),
        "issues": issues,
        "status": "FAIL" if has_blocks else "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify compiled SRS output")
    parser.add_argument("srs_path", type=Path, help="Path to compiled srs.md")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.srs_path.exists():
        print(f"ERROR: {args.srs_path} not found", file=sys.stderr)
        return 2

    result = verify(args.srs_path)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for issue in result["issues"]:
            print(f"[{issue['severity']}] [{issue['code']}] {issue['message']}")
        print(f"\n{result['status']}: {len(result['issues'])} issue(s)")

    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
