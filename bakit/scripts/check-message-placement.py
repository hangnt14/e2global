#!/usr/bin/env python3
"""Validate Message Placement table in screen canon files.

Usage:
    python3 scripts/check-message-placement.py ascii-screen/ [--json]
    python3 scripts/check-message-placement.py screen.md [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

MSG_RE = re.compile(r"\bMSG-(?:ERR|SUC|WRN|INF)-\d{2}\b")
SURFACE_ENUM = {"inline", "toast", "banner", "modal"}
INLINE_POSITION_RE = re.compile(r"(Dưới|Trên)\s+field\s+\S+", re.IGNORECASE)
TOAST_POSITION_VALUES = {"Góc phải dưới", "Góc phải trên", "Giữa trên", "Góc trái dưới"}
BANNER_POSITION_VALUES = {"Trên cùng màn hình", "Dưới cùng màn hình"}
DISMISS_PATTERNS = [
    r"Tự tắt sau \d+s", r"User ấn X", r"User ấn nút hành động",
    r"Không tắt đến khi", r"—",
]


def split_row(line: str) -> list[str]:
    return [cell.replace(r"\|", "|").strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def extract_msg_codes(text: str) -> set[str]:
    """Extract all MSG-* codes from Behaviour Rules, Validation Rules, and Message Placement."""
    return set(MSG_RE.findall(text))


def parse_message_placement(text: str) -> list[dict[str, str]]:
    """Parse the ## Message Placement table."""
    start = text.find("## Message Placement")
    if start == -1:
        return []
    next_heading = text.find("\n## ", start + 1)
    section = text[start:next_heading if next_heading != -1 else len(text)]

    rows: list[dict[str, str]] = []
    headers: list[str] = []
    for line in section.splitlines():
        if not line.startswith("|") or is_separator(line):
            continue
        cells = split_row(line)
        if not headers:
            headers = [c.lower().replace(" ", "_") for c in cells]
            continue
        if len(cells) >= 5:
            row = dict(zip(headers, cells + [""] * (len(headers) - len(cells))))
            rows.append(row)
    return rows


def extract_ascii_msg_codes(text: str) -> set[str]:
    """Extract MSG-* codes from ASCII wireframe code blocks and Message Zones legends."""
    codes = set()
    # Find all code blocks
    for block in re.finditer(r"```[\s\S]*?```", text):
        codes.update(MSG_RE.findall(block.group(0)))
    # Also find in Message Zones legend (outside code blocks)
    zones_start = text.find("Message Zones:")
    if zones_start != -1:
        zones_end = text.find("\n\n", zones_start)
        zones_text = text[zones_start:zones_end if zones_end != -1 else len(text)]
        codes.update(MSG_RE.findall(zones_text))
    return codes


def check_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    issues: list[dict[str, Any]] = []

    # Collect MSG codes from behaviour/validation rules
    fields_start = text.find("## Fields")
    placement_start = text.find("## Message Placement")
    fields_section = text[fields_start:placement_start if placement_start != -1 else len(text)] if fields_start != -1 else ""
    referenced_codes = extract_msg_codes(fields_section)

    if not referenced_codes:
        return {"path": str(path), "issues": []}

    # Parse message placement table
    placement_rows = parse_message_placement(text)
    placed_codes = {row.get("message_code", "").strip() for row in placement_rows if row.get("message_code", "").strip()}

    # Check 1: every referenced MSG-* must be in placement table
    for code in sorted(referenced_codes):
        if code not in placed_codes:
            # Accept full match like "MSG-ERR-01"
            if not any(code in pc for pc in placed_codes):
                issues.append({
                    "severity": "BLOCK", "code": "msg_not_placed",
                    "message": f"{code} referenced in Fields but missing from ## Message Placement table.",
                })

    # Check 2: every placed MSG must have valid surface
    for row in placement_rows:
        code = row.get("message_code", "").strip()
        surface = row.get("surface", "").strip().lower()
        position = row.get("position", "").strip()
        dismiss = row.get("dismiss", "").strip()

        if surface not in SURFACE_ENUM:
            issues.append({
                "severity": "BLOCK", "code": "invalid_surface",
                "message": f"{code}: surface '{surface}' invalid. Must be: {', '.join(sorted(SURFACE_ENUM))}",
            })

        # Check position format by surface
        if surface == "inline" and not INLINE_POSITION_RE.search(position):
            issues.append({
                "severity": "BLOCK", "code": "invalid_inline_position",
                "message": f"{code}: inline position must be 'Dưới field X' or 'Trên field X'. Got: '{position}'",
            })
        elif surface == "toast" and position not in TOAST_POSITION_VALUES:
            issues.append({
                "severity": "WARN", "code": "unusual_toast_position",
                "message": f"{code}: toast position '{position}' not in standard values: {', '.join(sorted(TOAST_POSITION_VALUES))}",
            })
        elif surface == "banner" and position not in BANNER_POSITION_VALUES:
            issues.append({
                "severity": "WARN", "code": "unusual_banner_position",
                "message": f"{code}: banner position '{position}' not in standard values: {', '.join(sorted(BANNER_POSITION_VALUES))}",
            })

        # Check dismiss
        if surface in {"toast", "banner", "modal"} and dismiss == "—":
            issues.append({
                "severity": "BLOCK", "code": "missing_dismiss",
                "message": f"{code}: {surface} must have a dismiss behavior (e.g., 'Tự tắt sau 5s', 'User ấn X')",
            })
        if surface == "toast" and dismiss != "—" and not re.search(r"\d+s", dismiss) and "User" not in dismiss:
            issues.append({
                "severity": "WARN", "code": "unclear_dismiss",
                "message": f"{code}: toast dismiss unclear. Specify time (e.g., 'Tự tắt sau 3s') or manual ('User ấn X')",
            })

    # Check 3: MSG codes in placement must appear in ASCII wireframe
    ascii_codes = extract_ascii_msg_codes(text)
    for code in sorted(placed_codes):
        if code not in ascii_codes:
            issues.append({
                "severity": "BLOCK", "code": "msg_not_in_wireframe",
                "message": f"{code} in ## Message Placement but not found in ASCII wireframe or Message Zones legend.",
            })

    # Check 3.5: inline messages must have ▼ marker near their field in wireframe
    wireframe_start = text.find("```")
    wireframe_end = text.rfind("```")
    wireframe_text = text[wireframe_start:wireframe_end] if wireframe_start >= 0 and wireframe_end > wireframe_start else ""
    for row in placement_rows:
        code = row.get("message_code", "").strip()
        surface = row.get("surface", "").strip().lower()
        if surface == "inline" and f"▼ {code}" not in wireframe_text:
            issues.append({
                "severity": "WARN", "code": "inline_msg_no_marker",
                "message": f"{code}: inline message should have '▼ {code}' marker in ASCII wireframe next to the field.",
            })

    # Check 3.6: Message Zones legend should exist
    if "Message Zones:" not in text:
        issues.append({
            "severity": "WARN", "code": "missing_message_zones",
            "message": "ASCII wireframe should include a 'Message Zones:' legend listing all message positions.",
        })

    # Check 4: dead placement (in table but not referenced)
    for code in sorted(placed_codes - referenced_codes):
        issues.append({
            "severity": "WARN", "code": "dead_message_placement",
            "message": f"{code} in ## Message Placement but not referenced in Fields (Behaviour/Validation).",
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
        output = {
            "files_checked": files_checked,
            "files_with_issues": len(failing),
            "results": failing,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return
    if not failing:
        print(f"OK: {files_checked} screen files — all Message Placements compliant")
        return
    for result in failing:
        print(f"\n{result['path']}:")
        for item in result["issues"]:
            print(f"  [{item['severity']}] [{item['code']}] {item['message']}")
    block_count = sum(1 for r in failing for i in r["issues"] if i["severity"] == "BLOCK")
    warn_count = sum(1 for r in failing for i in r["issues"] if i["severity"] == "WARN")
    print(f"\nBLOCK: {block_count}, WARN: {warn_count} — {len(failing)}/{files_checked} files with issues")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate screen Message Placement")
    parser.add_argument("path", nargs="+", help="Screen canon file(s) or directory")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    args = parser.parse_args()

    try:
        files = collect_files(args.path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not files:
        print("No screen files found", file=sys.stderr)
        return 2

    results = [check_file(f) for f in files]
    emit_report(results, len(files), args.json)

    has_blocks = any(
        i["severity"] == "BLOCK" for r in results for i in r["issues"]
    )
    return 1 if has_blocks else 0


if __name__ == "__main__":
    sys.exit(main())
