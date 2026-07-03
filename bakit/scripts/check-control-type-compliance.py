#!/usr/bin/env python3
"""Validate screen canon Control Type usage against the Control Type Library.

Usage:
    python3 scripts/check-control-type-compliance.py ascii-screen/ [--json]
    python3 scripts/check-control-type-compliance.py screen.md [--library path]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Built-in fallback when library file is missing
BUILTIN_CONTROL_TYPES: dict[str, dict[str, Any]] = {
    "text_input": {"name": "Text Input", "interactive": True, "has_states": True},
    "textarea": {"name": "Text Area", "interactive": True, "has_states": True},
    "button": {"name": "Button", "interactive": True, "has_states": True},
    "button (primary)": {"name": "Button (Primary)", "interactive": True, "has_states": True},
    "button (secondary)": {"name": "Button (Secondary)", "interactive": True, "has_states": True},
    "button (danger)": {"name": "Button (Danger)", "interactive": True, "has_states": True},
    "button (ghost)": {"name": "Button (Ghost)", "interactive": True, "has_states": True},
    "button (icon)": {"name": "Button (Icon)", "interactive": True, "has_states": True},
    "dropdown": {"name": "Dropdown", "interactive": True, "has_states": True},
    "select": {"name": "Select", "interactive": True, "has_states": True},
    "checkbox": {"name": "Checkbox", "interactive": True, "has_states": True},
    "radio": {"name": "Radio Button", "interactive": True, "has_states": True},
    "date_picker": {"name": "Date Picker", "interactive": True, "has_states": True},
    "toggle": {"name": "Toggle", "interactive": True, "has_states": True},
    "table": {"name": "Table", "interactive": True, "has_states": True},
    "file_upload": {"name": "File Upload", "interactive": True, "has_states": True},
    "search": {"name": "Search", "interactive": True, "has_states": True},
    "modal": {"name": "Modal", "interactive": False, "has_states": False, "is_overlay": True},
    "drawer": {"name": "Drawer", "interactive": False, "has_states": False, "is_overlay": True},
    "toast": {"name": "Toast", "interactive": False, "has_states": False},
    "banner": {"name": "Banner", "interactive": False, "has_states": False},
    "pagination": {"name": "Pagination", "interactive": True, "has_states": False},
    "tabs": {"name": "Tabs", "interactive": True, "has_states": True},
    "breadcrumb": {"name": "Breadcrumb", "interactive": True, "has_states": False},
    "stepper": {"name": "Stepper", "interactive": True, "has_states": True},
    "rich_text_editor": {"name": "Rich Text Editor", "interactive": True, "has_states": True},
}

REQUIRED_COLUMNS = ["Field ID", "Field Name", "Control Type", "Display Rules", "Behaviour Rules", "Validation Rules"]
DEFAULT_BEHAVIOUR_RE = re.compile(r"^\(default\)")
OVERRIDE_BEHAVIOUR_RE = re.compile(r"^\*\*Khác default:\*\*")
CT_ID_RE = re.compile(r"`([^`]+)`")


def load_library(library_path: Path | None) -> dict[str, dict[str, Any]]:
    """Load control type definitions from library markdown file.
    Falls back to BUILTIN_CONTROL_TYPES if library not found.
    """
    if library_path and library_path.exists():
        text = library_path.read_text(encoding="utf-8")
        parsed = _parse_library(text)
        if parsed:
            return parsed
    return dict(BUILTIN_CONTROL_TYPES)


def _parse_library(text: str) -> dict[str, dict[str, Any]]:
    """Parse control types from library markdown."""
    result: dict[str, dict[str, Any]] = {}
    sections = re.split(r"^###\s+\d+\.\s+", text, flags=re.MULTILINE)
    for section in sections[1:]:
        m = re.match(r".+?\(`([^`]+)`\)", section)
        if not m:
            continue
        ct_id = m.group(1)
        info: dict[str, Any] = {"name": section.split("\n")[0].split("(`")[0].strip()}
        info["interactive"] = ct_id not in {"modal", "drawer", "toast", "banner"}
        info["has_states"] = "**Default States:**" in section
        info["is_overlay"] = ct_id in {"modal", "drawer", "dialog"}
        info["edge_cases"] = _parse_edge_cases(section)
        result[ct_id] = info
    return result


def _parse_edge_cases(section: str) -> list[str]:
    marker = "**Edge Case cần mô tả thêm:**"
    start = section.find(marker)
    if start == -1:
        return []
    tail = section[start + len(marker):]
    end_markers = [
        idx for idx in (
            tail.find("\n**"),
            tail.find("\n---"),
            tail.find("\n### "),
        )
        if idx != -1
    ]
    block = tail[:min(end_markers)] if end_markers else tail
    edge_cases = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            edge_cases.append(stripped[2:].strip())
    return edge_cases


def split_row(line: str) -> list[str]:
    return [cell.replace(r"\|", "|").strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def is_separator(line: str) -> bool:
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def check_file(path: Path, library: dict[str, dict[str, Any]]) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    issues: list[dict[str, Any]] = []
    in_fields = False
    columns: list[str] = []
    has_control_type_col = False

    for line_num, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped == "## Fields":
            in_fields = True
            continue
        if in_fields and stripped.startswith("#") and not stripped.startswith("###"):
            in_fields = False
            continue
        if not in_fields or not stripped.startswith("|") or is_separator(stripped):
            continue

        cells = split_row(stripped)
        if not columns:
            columns = cells
            missing = [c for c in REQUIRED_COLUMNS if c not in columns]
            if missing:
                issues.append({
                    "severity": "BLOCK", "code": "missing_column",
                    "message": f"Missing required column(s): {', '.join(missing)}",
                    "line": line_num,
                })
            has_control_type_col = "Control Type" in columns
            continue

        if not has_control_type_col or len(cells) < 4:
            continue

        # Map cells to column names
        row = dict(zip(columns, cells + [""] * (len(columns) - len(cells))))
        field_name = row.get("Field Name", "?")
        control_type_raw = row.get("Control Type", "").strip()
        behaviour = row.get("Behaviour Rules", "").strip()
        field_id = row.get("Field ID", "").strip()

        # Extract control_type_id from backtick-quoted value
        ct_match = CT_ID_RE.search(control_type_raw)
        ct_id = ct_match.group(1) if ct_match else control_type_raw

        # Check 1: control_type must be in library
        if ct_id and ct_id not in library:
            issues.append({
                "severity": "BLOCK", "code": "unknown_control_type",
                "message": f"Control Type '{ct_id}' not found in library. Valid types: {', '.join(sorted(library.keys())[:10])}...",
                "field": field_name, "line": line_num,
            })

        # Check 2: interactive control must have Behaviour Rules
        ct_info = library.get(ct_id, {})
        if ct_info.get("interactive") and (not behaviour or behaviour == "-"):
            issues.append({
                "severity": "BLOCK", "code": "missing_behaviour",
                "message": f"Interactive control '{ct_id}' has empty Behaviour Rules. Use '(default)' to inherit from library.",
                "field": field_name, "line": line_num,
            })

        # Check 3: (default) only valid if control_type is in library
        if DEFAULT_BEHAVIOUR_RE.match(behaviour) and ct_id not in library:
            issues.append({
                "severity": "BLOCK", "code": "invalid_default",
                "message": f"Cannot use '(default)' for unknown control type '{ct_id}'.",
                "field": field_name, "line": line_num,
            })

        # Check 4: Field ID format (flexible: supports SCR-LRN-01-F01, SCR-01-F01, etc.)
        if field_id and not re.match(r"^SCR-[A-Z0-9]+(?:-[A-Z0-9]+)*-F\d{2}$", field_id):
            issues.append({
                "severity": "WARN", "code": "field_id_format",
                "message": f"Field ID '{field_id}' does not match expected format SCR-NN-FNN.",
                "field": field_name, "line": line_num,
            })

    # Check 5: button primary in form needs disabled condition
    has_button_primary = "button (primary)" in text or "`button (primary)`" in text
    has_form_fields = bool(re.search(r"\b(text_input|textarea|dropdown|date_picker)\b", text))
    if has_button_primary and has_form_fields:
        if DEFAULT_BEHAVIOUR_RE.search(text) or OVERRIDE_BEHAVIOUR_RE.search(text):
            pass  # default or explicit override — OK
        elif "disabled" not in text.lower() and "bật" not in text.lower():
            issues.append({
                "severity": "BLOCK", "code": "button_primary_no_disabled",
                "message": "Button (primary) in form must declare disabled condition. "
                           "Inherit '(default)' from library or override with explicit conditions.",
            })

    # Check 6: edge cases from library documented but not covered in screen
    screen_lower = text.lower()
    for ct_id, ct_info in library.items():
        if f"`{ct_id}`" not in text:
            continue
        edge_cases = ct_info.get("edge_cases", [])
        for ec in edge_cases:
            keywords = [w for w in re.findall(r"\b\w+\b", ec.lower()) if len(w) > 3]
            if keywords and not any(kw in screen_lower for kw in keywords):
                issues.append({
                    "severity": "WARN", "code": "edge_case_not_covered",
                    "message": f"'{ct_id}' edge case '{ec[:60]}...' not covered in screen.",
                    "field": ct_info.get("name", ct_id),
                })

    # Check 7: custom Behaviour Rules that look like default — suggest using (default)
    for line_num, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|") or is_separator(stripped):
            continue
        cells = split_row(stripped)
        if len(cells) < 6:
            continue
        behaviour = cells[5].strip() if len(cells) > 5 else ""
        if behaviour and behaviour not in {"-", "—"} and not DEFAULT_BEHAVIOUR_RE.match(behaviour) and not OVERRIDE_BEHAVIOUR_RE.match(behaviour):
            # Check if it looks like a default behaviour description
            if any(kw in behaviour.lower() for kw in ["disabled khi", "active khi", "loading khi", "focus", "blur"]):
                ct_val = cells[3].strip() if len(cells) > 3 else ""
                ct_match = CT_ID_RE.search(ct_val)
                ct_id = ct_match.group(1) if ct_match else ""
                if ct_id in library:
                    issues.append({
                        "severity": "WARN", "code": "custom_looks_like_default",
                        "message": f"Behaviour for '{ct_id}' looks like default — consider using '(default)' + override for edge cases only.",
                        "field": cells[1].strip() if len(cells) > 1 else "?",
                        "line": line_num,
                    })

    # Screen-level checks
    is_overlay = any(
        ct_info.get("is_overlay") for ct_id, ct_info in library.items()
        if f"`{ct_id}`" in text
    )
    if is_overlay and "## Overlay Context" not in text:
        issues.append({
            "severity": "BLOCK", "code": "missing_overlay_context",
            "message": "Screen is a modal/drawer but missing ## Overlay Context section.",
        })
    if is_overlay and "### Close Triggers" not in text:
        issues.append({
            "severity": "BLOCK", "code": "missing_close_triggers",
            "message": "Overlay screen must have ### Close Triggers table in ## Overlay Context.",
        })

    # Check: interactive controls should have Control States
    has_interactive = any(
        ct_info.get("interactive")
        for ct_match in re.finditer(r"`([^`]+)`", text)
        if (ct_match.group(1) in library and library[ct_match.group(1)].get("interactive"))
    )
    if has_interactive and "## Control States" not in text:
        issues.append({
            "severity": "WARN", "code": "missing_control_states",
            "message": "Screen has interactive controls but missing ## Control States section.",
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
        print(f"OK: {files_checked} screen files — all Control Types compliant")
        return
    for result in failing:
        print(f"\n{result['path']}:")
        for item in result["issues"]:
            location = f" line {item['line']}:" if item.get("line") else ""
            field = f" [{item['field']}]" if item.get("field") else ""
            print(f"  [{item['severity']}] [{item['code']}]{location}{field} {item['message']}")
    block_count = sum(1 for r in failing for i in r["issues"] if i["severity"] == "BLOCK")
    warn_count = sum(1 for r in failing for i in r["issues"] if i["severity"] == "WARN")
    print(f"\n{f'BLOCK: {block_count}, ' if block_count else ''}WARN: {warn_count} — {len(failing)}/{files_checked} files with issues")


def migrate_file(path: Path, dry_run: bool = False) -> bool:
    """Migrate old 4-column Fields table to new 6-column format.

    Old: | Field Name | Display Rules | Behaviour Rules | Validation Rules |
    New: | Field ID | Field Name | Control Type | Display Rules | Behaviour Rules | Validation Rules |

    Auto-generates Field IDs from screen_id in frontmatter (SCR-NN-FNN format).
    Backups original file as .bak.
    Returns True if migration was applied.
    """
    text = path.read_text(encoding="utf-8")
    if "| Field ID |" in text and "| Control Type |" in text:
        return False  # Already migrated

    # Extract screen_id from frontmatter for Field ID generation
    screen_id = "SCR-00"
    fm_match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if "screen_id:" in line:
                screen_id = line.split(":", 1)[1].strip().strip('"').strip("'")
                break

    lines = text.splitlines()
    new_lines = []
    in_fields = False
    field_count = 0
    migrated = False

    for line in lines:
        stripped = line.strip()

        # Detect old Fields section
        if stripped == "## Fields":
            in_fields = True
            new_lines.append(line)
            continue
        if in_fields and stripped.startswith("#") and not stripped.startswith("###"):
            in_fields = False

        if not in_fields or not stripped.startswith("|") or is_separator(stripped):
            new_lines.append(line)
            continue

        cells = split_row(stripped)
        cell_count = len(cells)

        # Detect old vs new format (4 or 5 column variants)
        old_format = False
        if cell_count in {4, 5} and "Field ID" not in cells and "Control Type" not in cells:
            old_format = True
        elif cell_count == 5 and "Type" in cells and "Control Type" not in cells:
            old_format = True

        if old_format:
            has_type_col = len(cells) == 5 and "Type" in cells
            if has_type_col:
                # 5-column: | Field | Type | Display Rules | Behaviour Rules | Validation Rules |
                old_name = cells[0].strip() if len(cells) > 0 else ""
                old_display = cells[2].strip() if len(cells) > 2 else ""
                old_behaviour = cells[3].strip() if len(cells) > 3 else ""
                old_validation = cells[4].strip() if len(cells) > 4 else ""
            else:
                # 4-column: | Field Name | Display Rules | Behaviour Rules | Validation Rules |
                old_name = cells[0].strip() if len(cells) > 0 else ""
                old_display = cells[1].strip() if len(cells) > 1 else ""
                old_behaviour = cells[2].strip() if len(cells) > 2 else ""
                old_validation = cells[3].strip() if len(cells) > 3 else ""

            if old_name in {"Field Name", "Tên trường", "Trường", "Field"}:
                new_lines.append("| Field ID | Field Name | Control Type | Display Rules | Behaviour Rules | Validation Rules |")
                new_lines.append("| --- | --- | --- | --- | --- | --- |")
                migrated = True
                continue

            # Skip old separator rows — header already emitted above
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue

            # Data row — add Field ID + empty Control Type (BA fills later)
            field_count += 1
            field_id = f"{screen_id}-F{field_count:02d}"
            new_lines.append(f"| {field_id} | {old_name} | _ | {old_display} | {old_behaviour} | {old_validation} |")
            migrated = True
        else:
            new_lines.append(line)

    if not migrated:
        return False

    new_text = "\n".join(new_lines) + "\n"

    if dry_run:
        print(f"[DRY-RUN] Would migrate: {path} ({field_count} fields, screen_id={screen_id})")
        return True

    # Backup
    backup = path.with_suffix(".bak")
    backup.write_text(text, encoding="utf-8")
    path.write_text(new_text, encoding="utf-8")
    print(f"Migrated: {path} ({field_count} fields, screen_id={screen_id}) → .bak saved")
    return True


def auto_fill_file(path: Path, dry_run: bool = False, force_default: bool = False) -> int:
    """Auto-fill missing sections and Behaviour Rules in a migrated screen file.

    Adds:
    - ## User Actions if missing (with placeholder)
    - ## States if missing (with placeholder)
    - Fills empty Behaviour Rules with (default)
    - Adds ## Message Placement stub if MSG-* codes are referenced
    - Adds ## Control States stub if interactive controls present

    Returns number of fixes applied.
    """
    text = path.read_text(encoding="utf-8")
    fixes = 0
    new_text = text

    # Fix 1: Add missing ## User Actions before ## States / ## Validation Rules / ## ASCII Wireframe
    if "## User Actions" not in new_text and "## Actions" not in new_text:
        insert_after = next(
            (h for h in ["## Validation Rules", "## States", "## ASCII Wireframe", "## Overlay Context"]
             if h in new_text), None
        )
        if insert_after:
            screen_id_match = re.search(r"screen_id:\s*\"?([A-Z0-9-]+)\"?", text)
            sid = screen_id_match.group(1) if screen_id_match else "SCR-NN"
            actions_block = f"""\n## User Actions

| Action ID | Label | Control | Trigger | Outcome |
|---|---|---|---|---|
| ACT-{sid.split('-')[-1]}-01 | [Tên hành động] | [button/link] | [cử chỉ] | [kết quả] |

"""
            new_text = new_text.replace(f"\n{insert_after}", f"{actions_block}\n{insert_after}")
            fixes += 1

    # Fix 2: Add missing ## States before ASCII Wireframe
    if "## States" not in new_text:
        screen_id_match = re.search(r"screen_id:\s*\"?([A-Z0-9-]+)\"?", text)
        sid = screen_id_match.group(1) if screen_id_match else "SCR-NN"
        states_block = f"""\n## States

| State ID | Name | Description |
|---|---|---|
| {sid}-DEFAULT | Default | [mô tả trạng thái mặc định] |
| {sid}-EMPTY | Empty | [mô tả trạng thái rỗng] |
| {sid}-ERROR | Error | [mô tả trạng thái lỗi] |

"""
        insert_before = next(
            (h for h in ["## ASCII Wireframe", "## Overlay Context"] if h in new_text), None
        )
        if insert_before:
            new_text = new_text.replace(f"\n{insert_before}", f"{states_block}\n{insert_before}")
            fixes += 1

    # Fix 3: Fill Behaviour Rules with (default)
    lines = new_text.splitlines()
    new_lines = []
    in_fields = False
    for line in lines:
        stripped = line.strip()
        if stripped == "## Fields":
            in_fields = True
            new_lines.append(line)
            continue
        if in_fields and stripped.startswith("#") and not stripped.startswith("###"):
            in_fields = False
            new_lines.append(line)
            continue
        if not in_fields or not stripped.startswith("|") or is_separator(stripped):
            new_lines.append(line)
            continue
        cells = split_row(stripped)
        if len(cells) >= 6:
            # Skip header rows
            if cells[0].strip() in {"Field ID", "Field Name", "Trường"}:
                new_lines.append(line)
                continue
            behaviour = cells[5].strip()
            if not behaviour or behaviour in {"-", "—"}:
                cells[5] = " (default)"
                new_lines.append("| " + " | ".join(cells) + " |")
                fixes += 1
                continue
            elif force_default and behaviour != "(default)":
                cells[5] = " (default)"
                new_lines.append("| " + " | ".join(cells) + " |")
                fixes += 1
                continue
        new_lines.append(line)
    new_text = "\n".join(new_lines) + "\n"

    # Fix 4: Add ## Control States stub if interactive controls exist
    if "## Control States" not in new_text and ("button" in new_text or "checkbox" in new_text or "dropdown" in new_text):
        cs_block = """\n## Control States

| Control | State | Condition |
|---|---|---|
| [Tên nút/field] | disabled | [khi nào] |
| [Tên nút/field] | active | [khi nào] |
| [Tên nút/field] | loading | [khi nào] |

"""
        insert_before = next(
            (h for h in ["## ASCII Wireframe", "## Overlay Context"] if h in new_text), None
        )
        if insert_before:
            new_text = new_text.replace(f"\n{insert_before}", f"{cs_block}\n{insert_before}")
            fixes += 1

    if fixes == 0:
        return 0

    if dry_run:
        print(f"[DRY-RUN] Would auto-fill {fixes} items in: {path}")
        return fixes

    backup = path.with_suffix(".bak2")
    backup.write_text(text, encoding="utf-8")
    path.write_text(new_text, encoding="utf-8")
    print(f"Auto-filled {fixes} items in: {path} → .bak2 saved")
    return fixes


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate screen Control Type usage")
    parser.add_argument("path", nargs="+", help="Screen canon file(s) or directory")
    parser.add_argument("--library", type=Path, help="Path to control-type-library.md")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help="Repo root for template resolution")
    parser.add_argument("--migrate", action="store_true", help="Auto-migrate old 4-column Fields table to new 6-column format")
    parser.add_argument("--auto-fill", action="store_true", help="Auto-fill missing sections + default Behaviour Rules after migrate")
    parser.add_argument("--force-default", action="store_true", help="Replace ALL Behaviour Rules with (default), not just empty ones")
    parser.add_argument("--dry-run", action="store_true", help="Preview migration/fill without writing")
    args = parser.parse_args()

    library_path = args.library
    if not library_path:
        template_path = args.repo / "templates" / "control-type-library-template.md"
        if template_path.exists():
            library_path = template_path

    library = load_library(library_path)

    try:
        files = collect_files(args.path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not files:
        print("No screen files found", file=sys.stderr)
        return 2

    if args.migrate or args.auto_fill:
        migrated = 0
        filled = 0
        for f in files:
            if args.migrate and migrate_file(f, dry_run=args.dry_run):
                migrated += 1
            if args.auto_fill:
                n = auto_fill_file(f, dry_run=args.dry_run, force_default=args.force_default)
                filled += n
        if args.migrate:
            print(f"Migrated {migrated}/{len(files)} screen files" + (" (dry-run)" if args.dry_run else ""))
        if args.auto_fill:
            print(f"Auto-filled {filled} items in {len(files)} screen files" + (" (dry-run)" if args.dry_run else ""))
        return 0

    results = [check_file(f, library) for f in files]
    emit_report(results, len(files), args.json)

    has_blocks = any(
        i["severity"] == "BLOCK" for r in results for i in r["issues"]
    )
    return 1 if has_blocks else 0


if __name__ == "__main__":
    sys.exit(main())
