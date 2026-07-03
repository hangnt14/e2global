#!/usr/bin/env python3
"""Scaffold Antigravity manual certification templates from parity goldens."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SECTION_NAMES = {
    "Behavior Envelope": "behavior_envelope",
    "Guardrail Preflight": "guardrail_preflight",
    "Guardrail Audit": "guardrail_audit",
}


def parse_section_table(markdown: str, heading: str) -> dict[str, str]:
    in_section = False
    values: dict[str, str] = {}

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line == f"## {heading}":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        field, value = cells[0], cells[1]
        if field in {"Field", "---"} or set(field) == {"-"}:
            continue
        values[field] = value

    return values


def parse_expected_sections(markdown: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    for heading, key in SECTION_NAMES.items():
        values = parse_section_table(markdown, heading)
        if values:
            sections[key] = values
    if "behavior_envelope" not in sections:
        raise ValueError("golden file missing Behavior Envelope")
    return sections


def build_template(golden_path: Path) -> dict[str, object]:
    sections = parse_expected_sections(golden_path.read_text(encoding="utf-8"))
    if len(sections) == 1:
        return {key: "" for key in sections["behavior_envelope"]}

    template: dict[str, object] = {}
    for section_name, fields in sections.items():
        template[section_name] = {key: "" for key in fields}
    return template


def fixture_id_from_name(path: Path) -> str:
    match = re.match(r"^(f\d+)", path.stem)
    if not match:
        raise ValueError(f"could not derive fixture id from {path.name}")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold Antigravity certification templates.")
    parser.add_argument("--goldens-dir", default="tests/runtime-parity/goldens")
    parser.add_argument("--output-dir", default="tests/runtime-parity/certifications/antigravity")
    parser.add_argument("fixture_ids", nargs="+", help="Fixture IDs like f21 f22")
    args = parser.parse_args()

    goldens_dir = Path(args.goldens_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: list[str] = []
    for fixture_id in args.fixture_ids:
        candidates = sorted(goldens_dir.glob(f"g{fixture_id[1:]}-*.md"))
        if len(candidates) != 1:
            raise SystemExit(f"{fixture_id}: expected exactly one golden, found {len(candidates)}")
        golden_path = candidates[0]
        template = build_template(golden_path)
        output_path = output_dir / f"{fixture_id}.template.json"
        output_path.write_text(json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        generated.append(output_path.as_posix())

    print("\n".join(generated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
