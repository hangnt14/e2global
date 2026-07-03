#!/usr/bin/env python3
"""Validate the BA-kit screen canon markdown contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_FIELDS = {
    "artifact_type",
    "screen_id",
    "screen_name",
    "module_slug",
    "status",
    "screen_type",
    "portal_id",
    "nav_schema_id",
    "expected_active_menu_item",
    "shell_variant",
    "layout_variant",
    "navigation_region_visible",
    "primary_actor",
    "goal",
    "ascii_status",
    "figma_sync_eligible",
    "figma_sync_status",
}

REQUIRED_SECTIONS = [
    "## Purpose",
    "## Entry And Exit",
    "## Regions",
    "## Fields",
    "## Actions",
    "## States",
    "## State Visual Coverage",
    "## Navigation Behavior",
    "## Trace Links",
    "## ASCII Wireframe",
    "## Figma Frame Map",
]

SCREEN_TYPES = {"primary", "primary_overlay", "modal", "drawer", "dialog", "wizard_step"}
ASCII_STATUS = {"missing", "stale", "current"}
FIGMA_STATUS = {"not-run", "eligible", "blocked", "synced", "stale"}
OVERLAY_TYPES = {"primary_overlay", "modal", "drawer", "dialog", "wizard_step"}
FIELD_HEADERS = [
    "field_id", "label", "control_type", "region_id", "display_rules",
    "behaviour_rules", "validation_rules", "rule_codes", "message_codes",
]
INTERACTIVE_CONTROLS = {"text_input", "textarea", "dropdown", "select", "date_picker", "checkbox", "radio", "button", "table"}
PLACEHOLDER_RE = re.compile(r"^\[.*\]$")
CODE_RE = re.compile(r"\b(CR-(?:DIS|BEH|VAL|MIX)-\d{2}|MSG-(?:ERR|WRN|SUC|INF)-\d{2})\b")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def table_rows_after(text: str, heading: str) -> list[list[str]]:
    start = text.find(heading)
    if start == -1:
        return []
    next_heading = text.find("\n## ", start + len(heading))
    section = text[start: next_heading if next_heading != -1 else len(text)]
    rows: list[list[str]] = []
    for line in section.splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(cells)
    return rows[1:]

def table_after(text: str, heading: str) -> tuple[list[str], list[dict[str, str]]]:
    start = text.find(heading)
    if start == -1:
        return [], []
    next_heading = text.find("\n## ", start + len(heading))
    section = text[start: next_heading if next_heading != -1 else len(text)]
    lines = [line for line in section.splitlines() if line.startswith("|") and "---" not in line]
    if len(lines) < 2:
        return [], []
    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    parsed: list[dict[str, str]] = []
    for line in lines[1:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        parsed.append(dict(zip(headers, cells)))
    return headers, parsed


def parse_index_codes(path: Path | None) -> set[str]:
    if not path or not path.is_file():
        return set()
    return set(CODE_RE.findall(path.read_text(encoding="utf-8")))


def is_blank_or_placeholder(value: str) -> bool:
    clean = value.strip()
    return not clean or clean in {"-", "N/A", "[]"} or bool(PLACEHOLDER_RE.match(clean))


def validate_fields_table(text: str, declared_codes: set[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    headers, rows = table_after(text, "## Fields")
    missing_headers = [header for header in FIELD_HEADERS if header not in headers]
    if missing_headers:
        errors.append(f"Fields table missing column(s): {', '.join(missing_headers)}")
        return errors, warnings
    for row in rows:
        field_id = row.get("field_id", "[unknown]")
        control = row.get("control_type", "").strip("` ").lower()
        for key in ("display_rules", "behaviour_rules", "validation_rules"):
            if is_blank_or_placeholder(row.get(key, "")):
                errors.append(f"{field_id}: {key} must be explicit, not blank or placeholder")
        codes = set(CODE_RE.findall(" ".join(row.get(key, "") for key in ("rule_codes", "message_codes"))))
        if declared_codes:
            for code in sorted(codes - declared_codes):
                errors.append(f"{field_id}: {code} is not declared in shared rule/message index")
        validation = row.get("validation_rules", "")
        if "required" in validation.lower() and "MSG-" not in row.get("message_codes", "") and not validation.lower().startswith("n/a:"):
            errors.append(f"{field_id}: required validation must reference a MSG-* code or state N/A with reason")
        if control in INTERACTIVE_CONTROLS and not codes:
            warnings.append(f"{field_id}: interactive field has no CR-* or MSG-* references")
    return errors, warnings


def validate(path: Path, shared_index: Path | None = None) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    errors: list[str] = []
    warnings: list[str] = []

    missing = sorted(REQUIRED_FIELDS - set(frontmatter))
    for field in missing:
        errors.append(f"missing frontmatter field: {field}")

    if frontmatter.get("artifact_type") != "screen-canon":
        errors.append("artifact_type must be screen-canon")
    if frontmatter.get("screen_type") and frontmatter["screen_type"] not in SCREEN_TYPES:
        errors.append(f"invalid screen_type: {frontmatter['screen_type']}")
    if frontmatter.get("ascii_status") and frontmatter["ascii_status"] not in ASCII_STATUS:
        errors.append(f"invalid ascii_status: {frontmatter['ascii_status']}")
    if frontmatter.get("ascii_status") and frontmatter["ascii_status"] != "current":
        errors.append("ascii_status must be current")
    if frontmatter.get("figma_sync_status") and frontmatter["figma_sync_status"] not in FIGMA_STATUS:
        errors.append(f"invalid figma_sync_status: {frontmatter['figma_sync_status']}")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing section: {section}")

    if frontmatter.get("screen_type") in OVERLAY_TYPES and "## Overlay Context" not in text:
        errors.append("overlay screen missing section: ## Overlay Context")

    field_errors, field_warnings = validate_fields_table(text, parse_index_codes(shared_index))
    errors.extend(field_errors)
    warnings.extend(field_warnings)

    state_rows = table_rows_after(text, "## State Visual Coverage")
    state_ids = []
    for row in state_rows:
        if len(row) < 8:
            continue
        state_id, _name, _trigger, _impact, level, ascii_required, figma_required, _parent = row[:8]
        state_ids.append(state_id)
        if level == "L3" and ascii_required != "Yes":
            errors.append(f"{state_id}: L3 state must set ascii_required=Yes")
        if level == "L3" and figma_required != "Yes":
            errors.append(f"{state_id}: L3 state must set figma_required=Yes")
        if level not in {"L1", "L2", "L3"}:
            errors.append(f"{state_id}: invalid visual_level={level}")

    ascii_states = set(re.findall(r"^###\s+(ST-[A-Z0-9-]+)", text, flags=re.MULTILINE))
    frame_rows = table_rows_after(text, "## Figma Frame Map")
    figma_states = {row[0] for row in frame_rows if row}

    for state_id in state_ids:
        if state_id not in ascii_states:
            errors.append(f"{state_id}: no matching ASCII subsection")
        if state_id.startswith("ST-") and state_id not in figma_states:
            warnings.append(f"{state_id}: no matching Figma Frame Map row")

    return {"path": str(path), "errors": errors, "warnings": warnings, "ok": not errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screen", type=Path)
    parser.add_argument("--shared-index", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = validate(args.screen, args.shared_index)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if result["ok"] else "BLOCK"
        print(f"{status}: {result['path']}")
        for error in result["errors"]:
            print(f"BLOCK: {error}")
        for warning in result["warnings"]:
            print(f"WARN: {warning}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
