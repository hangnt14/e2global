#!/usr/bin/env python3
"""Validate BA-kit navigation schema consistency across core artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NavSchema:
    portal_id: str
    nav_schema_id: str
    allowed_items: tuple[str, ...]


@dataclass(frozen=True)
class ScreenNav:
    source: Path
    line: int
    screen_id: str
    portal_id: str
    nav_schema_id: str
    expected_active_item: str
    nav_visible: str


def split_markdown_row(line: str) -> list[str]:
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip() for cell in value.split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_markdown_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def iter_markdown_tables(path: Path) -> list[tuple[int, list[str], list[tuple[int, list[str]]]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    tables: list[tuple[int, list[str], list[tuple[int, list[str]]]]] = []
    index = 0
    while index < len(lines) - 1:
        if "|" not in lines[index] or "|" not in lines[index + 1]:
            index += 1
            continue
        if not is_table_separator(lines[index + 1]):
            index += 1
            continue

        header_line = index + 1
        headers = split_markdown_row(lines[index])
        rows: list[tuple[int, list[str]]] = []
        index += 2
        while index < len(lines) and "|" in lines[index] and lines[index].strip().startswith("|"):
            rows.append((index + 1, split_markdown_row(lines[index])))
            index += 1
        tables.append((header_line, headers, rows))
    return tables


def key(header: str) -> str:
    normalized = header.lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def find_column(headers: list[str], *needles: str) -> int | None:
    normalized_headers = [key(header) for header in headers]
    for needle in needles:
        normalized_needle = key(needle)
        for index, header in enumerate(normalized_headers):
            if normalized_needle in header:
                return index
    return None


def cell(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return re.sub(r"\s+", " ", row[index].strip())


def split_top_level_commas(value: str) -> list[str]:
    items: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(value):
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char == "," and depth == 0:
            items.append(value[start:index].strip())
            start = index + 1
    items.append(value[start:].strip())
    return [item for item in items if item]


def clean_menu_value(value: str) -> str:
    value = re.sub(r"<br\s*/?>", ",", value, flags=re.IGNORECASE)
    value = value.replace("<br>", ",")
    value = re.sub(r"(^|,)\s*-\s*", r"\1", value)
    return value.strip()


def expand_menu_items(value: str) -> tuple[str, ...]:
    value = clean_menu_value(value)
    allowed: list[str] = []
    for item in split_top_level_commas(value):
        nested = re.fullmatch(r"(.+?)\s*\((.+)\)", item)
        if nested:
            parent = nested.group(1).strip()
            children = split_top_level_commas(nested.group(2))
            allowed.append(parent)
            allowed.extend(f"{parent} > {child.strip()}" for child in children if child.strip())
            continue
        allowed.append(item.strip())
    return tuple(dict.fromkeys(item for item in allowed if item))


def comparable(value: str) -> str:
    value = value.strip().strip("[]")
    value = re.sub(r"\s*>\s*", " > ", value)
    value = re.sub(r"\s+", " ", value)
    return value.casefold()


def is_empty_active(value: str) -> bool:
    return comparable(value) in {"", "n/a", "na", "none", "khong ap dung"}


def is_visible(value: str) -> bool:
    return comparable(value) in {"yes", "y", "true", "co"}


def load_nav_schemas(path: Path) -> dict[tuple[str, str], NavSchema]:
    schemas: dict[tuple[str, str], NavSchema] = {}
    for _, headers, rows in iter_markdown_tables(path):
        portal_index = find_column(headers, "Portal ID")
        nav_index = find_column(headers, "Nav Schema ID")
        menu_index = find_column(headers, "Menu Item List", "Menu chinh", "Sitemap")
        if portal_index is None or nav_index is None or menu_index is None:
            continue
        for _, row in rows:
            portal_id = cell(row, portal_index)
            nav_schema_id = cell(row, nav_index)
            menu_value = cell(row, menu_index)
            if not portal_id or not nav_schema_id or not menu_value:
                continue
            schemas[(comparable(portal_id), comparable(nav_schema_id))] = NavSchema(
                portal_id=portal_id,
                nav_schema_id=nav_schema_id,
                allowed_items=expand_menu_items(menu_value),
            )
    return schemas


def load_screen_nav_from_field_value(path: Path) -> ScreenNav | None:
    """Parse a Field | Value overview table from an ascii-screen/*.md file."""
    fields: dict[str, str] = {}
    for _, headers, rows in iter_markdown_tables(path):
        # Detect Field | Value table
        field_index = find_column(headers, "Field")
        value_index = find_column(headers, "Value")
        if field_index is None or value_index is None:
            continue
        for _, row in rows:
            field_name = cell(row, field_index)
            field_value = cell(row, value_index)
            if field_name:
                fields[key(field_name)] = field_value

    portal_id = fields.get("portal id", "")
    nav_schema_id = fields.get("nav schema id", "")
    active_item = fields.get("expected active menu item", "")
    nav_visible = fields.get("navigation region visible", "")

    if not portal_id or not nav_schema_id:
        return None

    # Derive screen_id from frontmatter or filename
    screen_id = path.stem.upper()
    text = path.read_text(encoding="utf-8")
    fm_match = re.search(r"^screen_id:\s*[\"']?([^\"'\n]+)[\"']?", text, re.MULTILINE)
    if fm_match:
        screen_id = fm_match.group(1).strip()

    return ScreenNav(
        source=path,
        line=1,
        screen_id=screen_id,
        portal_id=portal_id,
        nav_schema_id=nav_schema_id,
        expected_active_item=active_item,
        nav_visible=nav_visible,
    )


def load_screen_nav(path: Path) -> list[ScreenNav]:
    screens: list[ScreenNav] = []
    for _, headers, rows in iter_markdown_tables(path):
        screen_index = find_column(headers, "Screen ID", "Ma")
        portal_index = find_column(headers, "Portal ID")
        nav_index = find_column(headers, "Nav Schema ID")
        active_index = find_column(headers, "Expected Active Menu Item")
        visible_index = find_column(headers, "Navigation Region Visible")
        if (
            screen_index is None
            or portal_index is None
            or nav_index is None
            or active_index is None
        ):
            continue
        for line, row in rows:
            screens.append(
                ScreenNav(
                    source=path,
                    line=line,
                    screen_id=cell(row, screen_index),
                    portal_id=cell(row, portal_index),
                    nav_schema_id=cell(row, nav_index),
                    expected_active_item=cell(row, active_index),
                    nav_visible=cell(row, visible_index),
                )
            )

    # Fallback: try Field | Value overview table (ascii-screen/*.md format)
    if not screens:
        fv = load_screen_nav_from_field_value(path)
        if fv is not None:
            screens.append(fv)

    return screens


def validate(design: Path, screen_contracts: list[Path]) -> list[str]:
    errors: list[str] = []
    schemas = load_nav_schemas(design)
    if not schemas:
        return [f"NAV_SCHEMA_MISSING: no navigation schema table found in {design}"]

    screens: list[ScreenNav] = []
    for path in screen_contracts:
        screens.extend(load_screen_nav(path))
    if not screens:
        return ["SCREEN_CONTRACT_MISSING: no Screen Contract Plus navigation rows found"]

    for screen in screens:
        schema_key = (comparable(screen.portal_id), comparable(screen.nav_schema_id))
        schema = schemas.get(schema_key)
        location = f"{screen.source}:{screen.line} {screen.screen_id}".strip()
        if schema is None:
            errors.append(
                "NAV_SCHEMA_MISMATCH: "
                f"{location} uses {screen.portal_id}/{screen.nav_schema_id}, "
                "but DESIGN.md does not define that portal/schema pair"
            )
            continue

        active_item = screen.expected_active_item
        if is_empty_active(active_item):
            if is_visible(screen.nav_visible):
                errors.append(
                    "MENU_ACTIVE_MISSING: "
                    f"{location} has visible navigation but no Expected Active Menu Item"
                )
            continue

        allowed = {comparable(item) for item in schema.allowed_items}
        if comparable(active_item) not in allowed:
            errors.append(
                "MENU_SCHEMA_MISMATCH: "
                f"{location} expects active menu '{active_item}', "
                f"but {screen.portal_id}/{screen.nav_schema_id} allows "
                f"{', '.join(schema.allowed_items)}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate BA-kit navigation schema consistency."
    )
    parser.add_argument("--design", required=True, type=Path, help="Path to DESIGN.md")
    parser.add_argument(
        "--screen-contract",
        required=True,
        action="append",
        type=Path,
        help="Path to an SRS Group C or assembled SRS markdown file. Repeatable.",
    )
    args = parser.parse_args()

    missing = [str(path) for path in [args.design, *args.screen_contract] if not path.exists()]
    if missing:
        for path in missing:
            print(f"INPUT_MISSING: {path}", file=sys.stderr)
        return 2

    errors = validate(args.design, args.screen_contract)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Navigation consistency validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
