#!/usr/bin/env python3
"""Validate screen canon Behaviour Rules format and structure."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
TECHNICAL_PATTERNS = [
    r"\b(POST|GET|PUT|DELETE|PATCH)\s+/",
    r"\b/api/",
    r"\b(endpoint|API|fetch|axios|http)\b",
    r"\.(post|get|put|delete|patch)\(",
    r"\b(showModal|navigate|push)\(",
    r"\bset(State|Disabled|Loading)\(",
    r"\b(dispatch|useMutation|useQuery)\(",
    r"\brouter\.",
    r"\bredirect\(",
]
BUSINESS_PATTERNS = [
    r"\bSCR-[A-Z0-9]+(?:-[A-Z0-9]+)*\b",
    r"\bMSG-(ERR|SUC|WRN|INF)(?:-[A-Z0-9]+)*-\d{2,3}\b",
    r"\b(open|close|navigate|display|show|hide|enable|disable)\b",
    r"\b(modal|dialog|drawer|overlay|toast|banner|popup)\b",
    r"\b(mở|đóng|hiển thị|bật|tắt|vào|quay về|điền|ấn|giới hạn|lưu|validate)\b",
    r"^\(default\)",  # Inherits from Control Type Library
]
REQUIRED_SECTIONS = ["## Fields", "## User Actions", "## States", "## ASCII Wireframe"]
REQUIRED_COLUMNS = ["Field ID", "Field Name", "Control Type", "Display Rules", "Behaviour Rules", "Validation Rules"]
FORBIDDEN_COLUMNS = {"Type"}
NAVIGATION_TERMS = (
    "navigate",
    "navigation",
    "redirect",
    "go to",
    "open screen",
    "chuyển màn",
    "chuyển sang",
    "đi tới",
    "đến màn",
    "vào màn",
    "mở màn",
)
FEEDBACK_TERMS = ("toast", "banner", "inline", "feedback", "lỗi", "thông báo")
MSG_RE = re.compile(r"\bMSG-(ERR|SUC|WRN|INF)(?:-[A-Z0-9]+)*-\d{2,3}\b")
SCREEN_ID_RE = re.compile(r"\bSCR-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")

def issue(code: str, message: str, field: str | None = None, line: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"severity": "error", "code": code, "message": message}
    if field:
        result["field"] = field
    if line:
        result["line"] = line
    return result

def split_row(line: str) -> list[str]:
    return [cell.replace(r"\|", "|").strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]

def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)

def has_business_signal(text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in BUSINESS_PATTERNS)

def check_behaviour(cells: list[str], columns: list[str], line_number: int) -> list[dict[str, Any]]:
    field_name = cells[0] if cells else "?"
    behaviour_index = columns.index("Behaviour Rules")
    if behaviour_index >= len(cells):
        return [issue("missing_behaviour_cell", "Fields table row is missing the Behaviour Rules cell.", field_name, line_number)]

    behaviour = cells[behaviour_index].strip()
    if not behaviour or behaviour in {"-", "—"}:
        return [
            issue(
                "empty_behaviour",
                "Behaviour Rules must describe user-visible behaviour in business language. Use '(default)' to inherit from Control Type Library.",
                field_name,
                line_number,
            )
        ]

    # Skip validation for inherited default behaviour
    if behaviour.startswith("(default)"):
        return []

    issues: list[dict[str, Any]] = []
    for pattern in TECHNICAL_PATTERNS:
        match = re.search(pattern, behaviour, re.IGNORECASE)
        if not match:
            continue
        issues.append(
            issue(
                "technical_language",
                f"Behaviour Rules contains technical language '{match.group(0)}'. "
                "Use business language with SCR-IDs, MSG-* codes, overlay actions, or feedback.",
                field_name,
                line_number,
            )
        )
        break

    lower_behaviour = behaviour.lower()
    if any(term in lower_behaviour for term in NAVIGATION_TERMS) and not SCREEN_ID_RE.search(behaviour):
        issues.append(
            issue(
                "missing_screen_reference",
                "Navigation behaviour must reference the target SCR-* screen ID.",
                field_name,
                line_number,
            )
        )
    if any(term in lower_behaviour for term in FEEDBACK_TERMS) and not MSG_RE.search(behaviour):
        issues.append(
            issue(
                "missing_message_code",
                "User-visible feedback in Behaviour Rules must reference a MSG-* code.",
                field_name,
                line_number,
            )
        )
    if not has_business_signal(behaviour):
        issues.append(
            issue(
                "missing_business_language",
                "Behaviour Rules must include business-language actions, SCR-* targets, "
                "MSG-* feedback, overlay actions, or visible state changes.",
                field_name,
                line_number,
            )
        )
    return issues

def check_header(columns: list[str], line_number: int) -> list[dict[str, Any]]:
    issues = [
        issue("extra_column", f"Forbidden extra column in Fields table: {column}", line=line_number)
        for column in columns
        if column in FORBIDDEN_COLUMNS
    ]
    issues += [
        issue("missing_column", f"Missing required column in Fields table: {column}", line=line_number)
        for column in REQUIRED_COLUMNS
        if column not in columns
    ]
    return issues

def check_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    issues = [issue("missing_section", f"Missing required section: {section}") for section in REQUIRED_SECTIONS if section not in text]
    in_fields = False
    columns: list[str] | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped == "## Fields":
            in_fields = True
            continue
        if in_fields and stripped.startswith("#") and stripped != "## Fields":
            break
        if not in_fields or not stripped.startswith("|") or is_separator(stripped):
            continue

        cells = split_row(stripped)
        if columns is None:
            columns = cells
            issues += check_header(columns, line_number)
            continue
        if len(cells) != len(columns):
            issues.append(
                issue(
                    "column_count_mismatch",
                    f"Fields table row has {len(cells)} cells but header has {len(columns)}.",
                    cells[0] if cells else None,
                    line_number,
                )
            )
        if "Behaviour Rules" in columns:
            issues += check_behaviour(cells, columns, line_number)

    if "## Fields" in text and columns is None:
        issues.append(issue("missing_fields_table", "Missing Fields table under ## Fields."))
    return {"path": str(path), "issues": issues}

def collect_files(raw_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        if path.is_dir():
            files += sorted(item for item in path.glob("*.md") if item.name != "index.md")
        elif path.is_file() and path.name != "index.md":
            files.append(path)
        elif not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
    return files

def emit_report(results: list[dict[str, Any]], files_checked: int, as_json: bool) -> None:
    failing = [result for result in results if result["issues"]]
    if as_json:
        print(json.dumps({"files_checked": files_checked, "files_with_issues": len(failing), "results": failing}, indent=2, ensure_ascii=False))
        return
    if not failing:
        print(f"OK: {files_checked} screen files - all Behaviour Rules compliant")
        return
    for result in failing:
        print(f"\n{result['path']}:")
        for item in result["issues"]:
            location = f" line {item['line']}:" if item.get("line") else ""
            field = f" [{item['field']}]" if item.get("field") else ""
            print(f"  [{item['code']}]{location}{field} {item['message']}")
    print(f"\n{len(failing)}/{files_checked} files with violations")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="+", help="Screen canon file(s) or ascii-screen directory")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    try:
        files = collect_files(args.path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not files:
        print("No screen files found", file=sys.stderr)
        return 2

    results = [check_file(path) for path in files]
    emit_report(results, len(files), args.json)
    return 1 if any(result["issues"] for result in results) else 0

if __name__ == "__main__":
    sys.exit(main())
