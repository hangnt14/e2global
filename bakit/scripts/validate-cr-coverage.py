#!/usr/bin/env python3
"""Validate Common Rules coverage in screen canon files.

Detects missing CR-* references via pattern matching, checks edge case coverage,
finds dead references. Respects <!-- skip-cr:CODE --> override.

Usage:
    python3 scripts/validate-cr-coverage.py ascii-screen/ --common-rules path/to/common-rules.md [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CR_CODE_RE = re.compile(r"\bCR-(?:DIS|BEH|VAL|MIX)-\d{2}\b")
SKIP_CR_RE = re.compile(r"<!--\s*skip-cr:(CR-\w+-\d+)(?:\s+Lý do:\s*(.+?))?\s*-->")
COMMON_RULES_HEADER_ALIASES = {
    "code": ("code",),
    "rule_statement": ("rule_statement", "statement"),
    "applies_to": ("applies_to", "applies_to_(pattern)", "applies_to_pattern"),
    "edge_cases": ("edge_cases", "edge_case"),
}


def _parse_common_rules(path: Path) -> dict[str, dict[str, Any]]:
    """Parse CR definitions from common-rules.md. Returns {code: {statement, applies_to, edge_cases}}."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    result: dict[str, dict[str, Any]] = {}

    in_table = False
    headers: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        if any(c.startswith("---") for c in cells):
            continue
        if not headers:
            headers = [c.lower().replace(" ", "_") for c in cells]
            in_table = True
            continue
        if in_table and len(cells) >= 4:
            row = dict(zip(headers, cells + [""] * (len(headers) - len(cells))))
            code = row.get("code", "").strip()
            if CR_CODE_RE.match(code):
                applies_to = _row_value(row, "applies_to").strip()
                edge_cases_raw = _row_value(row, "edge_cases").strip()
                edge_cases = [e.strip() for e in edge_cases_raw.split(".") if e.strip()] if edge_cases_raw and edge_cases_raw not in {"-", "—"} else []
                result[code] = {
                    "statement": _row_value(row, "rule_statement").strip(),
                    "applies_to": applies_to,
                    "keywords": _extract_keywords(applies_to),
                    "edge_cases": edge_cases,
                }
    return result


def _row_value(row: dict[str, str], canonical: str) -> str:
    for alias in COMMON_RULES_HEADER_ALIASES.get(canonical, (canonical,)):
        if alias in row:
            return row.get(alias, "")
    return ""


def _extract_keywords(applies_to: str) -> list[str]:
    """Extract search keywords from applies_to field. Handles backtick-quoted and comma-separated."""
    keywords = []
    for token in re.findall(r"`([^`]+)`|([^,]+)", applies_to):
        kw = token[0] or token[1]
        kw = kw.strip().lower()
        if kw:
            keywords.append(kw)
    return keywords


def _extract_cr_codes(text: str) -> set[str]:
    return set(CR_CODE_RE.findall(text))


def _extract_skip_cr(text: str) -> set[str]:
    return {m.group(1) for m in SKIP_CR_RE.finditer(text)}


def _check_edge_case_coverage(screen_text: str, edge_cases: list[str]) -> list[str]:
    """Check which edge cases are NOT covered in screen States or Behaviour."""
    uncovered = []
    for ec in edge_cases:
        # Simple keyword check: does any word from the edge case appear in States section?
        keywords = [w for w in re.findall(r"\b\w+\b", ec.lower()) if len(w) > 2]
        if not keywords:
            continue
        states_start = screen_text.find("## States")
        ascii_start = screen_text.find("## ASCII Wireframe")
        states_section = screen_text[states_start:ascii_start if ascii_start != -1 else len(screen_text)] if states_start != -1 else ""
        if not any(kw in states_section.lower() for kw in keywords):
            uncovered.append(ec)
    return uncovered


def check_screen(path: Path, cr_defs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    issues: list[dict[str, Any]] = []
    screen_name = path.stem

    referenced_codes = _extract_cr_codes(text)
    skip_codes = _extract_skip_cr(text)

    # Check 1: Pattern-based missing CR detection
    for cr_code, cr_info in cr_defs.items():
        if cr_code in skip_codes:
            continue
        keywords = cr_info.get("keywords", [])
        if not keywords:
            continue
        matched = [kw for kw in keywords if kw in text.lower()]
        if matched and cr_code not in referenced_codes:
            issues.append({
                "severity": "WARN", "code": "missing_cr_reference",
                "message": (
                    f"Screen matches pattern [{', '.join(matched)}] "
                    f"but missing {cr_code} ({cr_info.get('statement', '')}). "
                    f"Add reference or <!-- skip-cr:{cr_code} Lý do: ... -->"
                ),
            })

    # Check 2: Edge case coverage
    for cr_code in referenced_codes:
        cr_info = cr_defs.get(cr_code, {})
        edge_cases = cr_info.get("edge_cases", [])
        uncovered = _check_edge_case_coverage(text, edge_cases)
        for ec in uncovered:
            issues.append({
                "severity": "WARN", "code": "edge_case_uncovered",
                "message": f"{cr_code} edge case '{ec}' not covered in screen States section.",
            })

    # Check 3: Dead references — CR referenced but no pattern matched in screen
    for cr_code in sorted(referenced_codes - set(skip_codes)):
        if cr_code not in cr_defs:
            issues.append({
                "severity": "WARN", "code": "undeclared_cr",
                "message": f"{cr_code} referenced but not declared in common-rules.md.",
            })
            continue
        cr_info = cr_defs.get(cr_code, {})
        keywords = cr_info.get("keywords", [])
        if keywords and not any(kw in text.lower() for kw in keywords):
            issues.append({
                "severity": "WARN", "code": "dead_reference",
                "message": f"{cr_code} referenced but no matching pattern found in screen. Dead reference?",
            })

    return {"path": str(path), "issues": issues}


def collect_files(raw_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in raw_paths:
        p = Path(raw_path)
        if p.is_dir():
            files += sorted(item for item in p.glob("*.md") if item.name != "index.md")
        elif p.is_file() and p.name != "index.md":
            files.append(p)
    return files


def emit_report(results: list[dict[str, Any]], files_checked: int, as_json: bool) -> None:
    failing = [r for r in results if r["issues"]]
    if as_json:
        print(json.dumps({"files_checked": files_checked, "files_with_issues": len(failing), "results": failing}, indent=2, ensure_ascii=False))
        return
    if not failing:
        print(f"OK: {files_checked} screen files — all CR coverage compliant")
        return
    for result in failing:
        print(f"\n{result['path']}:")
        for item in result["issues"]:
            print(f"  [{item['severity']}] [{item['code']}] {item['message']}")
    warn_count = sum(1 for r in failing for i in r["issues"])
    print(f"\nWARN: {warn_count} — {len(failing)}/{files_checked} files with issues")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CR coverage in screen files")
    parser.add_argument("path", nargs="+", help="Screen canon file(s) or directory")
    parser.add_argument("--common-rules", type=Path, required=True, help="Path to common-rules.md")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cr_defs = _parse_common_rules(args.common_rules)
    if not cr_defs:
        print(f"WARNING: No CR definitions found in {args.common_rules}", file=sys.stderr)

    try:
        files = collect_files(args.path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not files:
        print("No screen files found", file=sys.stderr)
        return 2

    results = [check_screen(f, cr_defs) for f in files]
    emit_report(results, len(files), args.json)
    return 0  # WARN-only, never BLOCK


if __name__ == "__main__":
    sys.exit(main())
