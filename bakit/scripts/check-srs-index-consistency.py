#!/usr/bin/env python3
"""Validate that SRS index registry paths exist."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PATH_PATTERN = re.compile(r"`(\./[^`]+)`")


def extract_paths(text: str) -> list[str]:
    paths: list[str] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        paths.extend(PATH_PATTERN.findall(line))
    return paths


def validate(index_path: Path) -> dict[str, object]:
    text = index_path.read_text(encoding="utf-8")
    base = index_path.parent
    errors: list[str] = []
    warnings: list[str] = []

    required_sections = [
        "## Screen Registry",
        "## Use Case Registry",
        "## Diagram Registry",
        "## Data Artifact Registry",
        "## Trace Summary",
        "## Validation Status",
    ]
    for section in required_sections:
        if section not in text:
            errors.append(f"missing section: {section}")

    for rel in extract_paths(text):
        target = (base / rel).resolve()
        if not target.exists():
            errors.append(f"missing indexed path: {rel}")

    screen_ids = re.findall(r"\|\s*(SCR-[^|\s]+)\s*\|", text)
    duplicate_screen_ids = sorted({sid for sid in screen_ids if screen_ids.count(sid) > 1})
    for screen_id in duplicate_screen_ids:
        warnings.append(f"duplicate screen id appears in index rows: {screen_id}")

    return {"path": str(index_path), "errors": errors, "warnings": warnings, "ok": not errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = validate(args.index)
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
