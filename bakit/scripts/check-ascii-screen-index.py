#!/usr/bin/env python3
"""Validate ascii-screen/index.md for a module against the new folder-based canon."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from guardrail_common import (
    classify_index_state,
    load_contract,
    render_path,
    strip_code,
)

ASCII_WIREFRAME_SECTION_RE = re.compile(r"^##\s+ASCII Wireframe", re.IGNORECASE)
ASCII_STATUS_RE = re.compile(r"ascii_status\s*:\s*(\w+)", re.IGNORECASE)


def check_ascii_coverage(screen_path: Path) -> tuple[bool, str]:
    """Return (has_ascii, ascii_status) for a screen file."""
    if not screen_path.exists():
        return False, "missing"
    text = screen_path.read_text(encoding="utf-8")
    has_section = bool(ASCII_WIREFRAME_SECTION_RE.search(text))
    status_match = ASCII_STATUS_RE.search(text)
    status = status_match.group(1).lower() if status_match else "unknown"
    return has_section, status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", help="Write JSON result to this path")
    parser.add_argument("--require-ascii-current", action="store_true",
                        help="Fail if any screen has ascii_status != current")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    contract = load_contract(repo)

    result = classify_index_state(
        repo=repo,
        contract=contract,
        index_key="ascii_screen_index",
        slug=args.slug,
        date=args.date,
        module=args.module,
    )

    ascii_issues: list[dict] = []
    if result["state"] == "current" and "rows" in result:
        module_root = repo / render_path(
            contract["paths"]["module_root"],
            slug=args.slug,
            date=args.date,
            module=args.module,
        )
        for row in result["rows"]:
            file_val = strip_code(row.get("File", ""))
            screen_id = strip_code(row.get("Screen ID", ""))
            if not file_val:
                continue
            screen_path = (module_root / file_val).resolve()
            has_ascii, ascii_status = check_ascii_coverage(screen_path)
            if not screen_path.exists():
                ascii_issues.append({"screen_id": screen_id, "file": file_val, "issue": "file_missing"})
            elif not has_ascii:
                ascii_issues.append({"screen_id": screen_id, "file": file_val, "issue": "ascii_wireframe_section_missing"})
            elif args.require_ascii_current and ascii_status != "current":
                ascii_issues.append({"screen_id": screen_id, "file": file_val, "issue": f"ascii_status_{ascii_status}"})

    if ascii_issues:
        result["state"] = "stale"
        result["reason"] = "ascii_coverage_issues"
        result["ascii_issues"] = ascii_issues

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)

    if result["state"] == "current":
        return 0
    print(
        f"ASCII_SCREEN_INDEX_FAIL: state={result['state']} reason={result.get('reason', '')}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
