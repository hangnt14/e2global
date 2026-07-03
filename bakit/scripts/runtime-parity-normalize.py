#!/usr/bin/env python3
"""Prompt and comparison helpers for BA-kit runtime parity adapters."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SECTION_NAMES = {
    "Behavior Envelope": "behavior_envelope",
    "Guardrail Preflight": "guardrail_preflight",
    "Guardrail Audit": "guardrail_audit",
}

SECTION_ORDER = ["behavior_envelope", "guardrail_preflight", "guardrail_audit"]
MATCHER_SUFFIXES = ("_includes", "_excludes")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
        raise SystemExit("Could not parse Behavior Envelope from golden file")
    return sections


def parse_fixture_runtime_input(markdown: str) -> str:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for raw_line in markdown.splitlines():
        heading_match = re.match(r"^##\s+(.+)$", raw_line)
        if heading_match:
            current = heading_match.group(1).strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(raw_line)

    wanted = ["Scenario", "Input State", "Input Command"]
    missing = [name for name in wanted if name not in sections]
    if missing:
        raise SystemExit(f"Fixture missing sections: {', '.join(missing)}")

    parts = []
    for name in wanted:
        parts.append(f"## {name}\n" + "\n".join(sections[name]).strip())
    return "\n\n".join(parts)


def matcher_base_field(field: str) -> str:
    for suffix in MATCHER_SUFFIXES:
        if field.endswith(suffix):
            return field[: -len(suffix)]
    return field


def build_prompt(fixture_path: Path, golden_path: Path) -> str:
    fixture = read_text(fixture_path)
    golden = read_text(golden_path)
    expected_sections = parse_expected_sections(golden)
    runtime_input = parse_fixture_runtime_input(fixture)
    guardrail_sections = [
        name for name in SECTION_ORDER if name != "behavior_envelope" and name in expected_sections
    ]

    if not guardrail_sections:
        keys = "\n".join(f"- {key}" for key in expected_sections["behavior_envelope"])
        return f"""You are executing a BA-kit runtime parity fixture.

Do not modify files. Use the repository contract only as reference:
- core/contract.yaml
- core/contract-behavior.md
- core/workflows/*.md
- skills/ba-start/SKILL.md and its step files when needed

Return only one JSON object. Do not wrap it in markdown. Do not include commentary.
All values must be strings. Include exactly these keys:
{keys}

Rules:
- Use the exact BA-kit command surface string, including the `ba-start` prefix when applicable.
- Use exact canonical enums from the golden contract:
  - `NONE` for no write target or no fallback code
  - `NOT_REQUIRED` for approval gates that do not block
  - activation levels in uppercase such as `COMPACT`, `BASE`, `MODULAR`, `PROGRAM`
- Compact-mode normalization:
  - if the fixture shows only a flat `project-memory.md` and no shard tree, emit `activation_level=COMPACT`, `fallback_code=NONE`, and use that file as both `source_of_truth_artifact` and `read_scope`
  - emit `COMPACT_FALLBACK` only for degraded compact fallback cases where no valid flat `project-memory.md` exists

Derive the normalized behavior envelope from this fixture input. Do not use the fixture's Expected Outcome section.

{runtime_input}
"""

    prompt_schema: dict[str, list[str]] = {}
    for section_name in SECTION_ORDER:
        section_fields = expected_sections.get(section_name)
        if not section_fields:
            continue
        prompt_keys: list[str] = []
        for field in section_fields:
            base_field = matcher_base_field(field)
            if base_field not in prompt_keys:
                prompt_keys.append(base_field)
        prompt_schema[section_name] = prompt_keys

    schema_text = json.dumps(prompt_schema, indent=2, ensure_ascii=False)
    return f"""You are executing a BA-kit runtime parity fixture.

Do not modify files. Use the repository contract and guardrail scripts only as reference:
- core/contract.yaml
- core/contract-behavior.md
- core/workflows/*.md
- skills/ba-start/SKILL.md and its step files when needed
- docs/runtime-hard-guardrails.md
- scripts/guardrail-preflight.py
- scripts/guardrail-audit.py

Return only one JSON object. Do not wrap it in markdown. Do not include commentary.
Use exactly this section/key shape:
{schema_text}

Rules:
- All leaf values must be strings.
- Use the exact BA-kit command surface string, including the `ba-start` prefix when applicable.
- Use exact canonical enums from the golden contract:
  - `NONE` for no write target or no fallback code
  - `NOT_REQUIRED` for approval gates that do not block
  - activation levels in uppercase such as `COMPACT`, `BASE`, `MODULAR`, `PROGRAM`
- Compact-mode normalization:
  - if the fixture shows only a flat `project-memory.md` and no shard tree, emit `activation_level=COMPACT`, `fallback_code=NONE`, and use that file as both `source_of_truth_artifact` and `read_scope`
  - emit `COMPACT_FALLBACK` only for degraded compact fallback cases where no valid flat `project-memory.md` exists
- For read lists, return comma-separated repo-relative paths in runtime order.
- For `violations` or `warnings`, return compact strings such as `type@path` separated by `; `.

Derive the normalized behavior envelope plus guardrail evidence from this fixture input. Do not use the fixture's Expected Outcome section.

{runtime_input}
"""


def extract_json_object(text: str) -> dict[str, object]:
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            value = json.loads(stripped)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value

    raise SystemExit("Runtime output did not contain a JSON object")


def normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def compact_mapping(value: dict[str, Any]) -> str:
    parts = []
    for key in sorted(value):
        normalized = normalize_scalar(value[key])
        if normalized:
            parts.append(f"{key}={normalized}")
    return ", ".join(parts)


def normalize_list_entry(value: Any) -> str:
    if isinstance(value, dict):
        item_type = normalize_scalar(value.get("type", ""))
        path = normalize_scalar(value.get("path", ""))
        reason = normalize_scalar(value.get("reason", ""))
        if item_type and path:
            return f"{item_type}@{path}"
        if path and reason:
            return f"{path}@{reason}"
        return compact_mapping(value)
    return normalize_scalar(value)


def flatten_section(value: Any, prefix: str = "") -> dict[str, str]:
    flattened: dict[str, str] = {}

    if isinstance(value, dict):
        if prefix:
            flattened[prefix] = compact_mapping(value)
        for key, item in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(flatten_section(item, child_prefix))
        return flattened

    if isinstance(value, list):
        flattened[prefix] = ", ".join(normalize_list_entry(item) for item in value)
        flattened[f"{prefix}.count"] = str(len(value))
        if value and all(isinstance(item, dict) for item in value):
            flattened[f"{prefix}.types"] = ", ".join(
                normalize_scalar(item.get("type", ""))
                for item in value
                if normalize_scalar(item.get("type", ""))
            )
            flattened[f"{prefix}.paths"] = ", ".join(
                normalize_scalar(item.get("path", ""))
                for item in value
                if normalize_scalar(item.get("path", ""))
            )
            flattened[f"{prefix}.reasons"] = ", ".join(
                normalize_scalar(item.get("reason", ""))
                for item in value
                if normalize_scalar(item.get("reason", ""))
            )
        return flattened

    flattened[prefix] = normalize_scalar(value)
    return flattened


def split_csv_like(value: str) -> list[str]:
    normalized = value.replace(";", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def select_actual_section(actual_obj: dict[str, object], section_name: str) -> object:
    nested = actual_obj.get(section_name)
    if isinstance(nested, dict):
        return nested

    if section_name == "behavior_envelope":
        behavior = {
            key: value
            for key, value in actual_obj.items()
            if key not in {"behavior_envelope", "guardrail_preflight", "guardrail_audit"}
        }
        return behavior or {}

    if section_name == "guardrail_preflight":
        if any(key in actual_obj for key in {"indexes", "allow_reads", "deny_reads", "excerpt_plan"}):
            return actual_obj
        return {}

    if section_name == "guardrail_audit":
        if any(key in actual_obj for key in {"actual_reads", "violations", "warnings"}):
            return actual_obj
        return {}

    return {}


def compare_field(field: str, expected_value: str, actual_values: dict[str, str]) -> str | None:
    if field.endswith("_includes"):
        base_field = matcher_base_field(field)
        actual_tokens = set(split_csv_like(actual_values.get(base_field, "")))
        missing = [item for item in split_csv_like(expected_value) if item not in actual_tokens]
        if missing:
            return f"`{base_field}` missing {', '.join(missing)}"
        return None

    if field.endswith("_excludes"):
        base_field = matcher_base_field(field)
        actual_tokens = set(split_csv_like(actual_values.get(base_field, "")))
        present = [item for item in split_csv_like(expected_value) if item in actual_tokens]
        if present:
            return f"`{base_field}` unexpectedly contained {', '.join(present)}"
        return None

    actual_value = actual_values.get(field)
    if actual_value is None:
        return f"missing key `{field}`"
    if actual_value != expected_value:
        return f"`{field}` expected `{expected_value}` but got `{actual_value}`"
    return None


def compare(golden_path: Path, actual_path: Path, runtime: str, fixture_id: str) -> int:
    expected_sections = parse_expected_sections(read_text(golden_path))
    actual_raw = read_text(actual_path)
    actual_obj = extract_json_object(actual_raw)

    diffs: list[str] = []
    for section_name in SECTION_ORDER:
        expected_fields = expected_sections.get(section_name)
        if not expected_fields:
            continue
        actual_section = select_actual_section(actual_obj, section_name)
        flattened_actual = flatten_section(actual_section)
        for field, expected_value in expected_fields.items():
            diff = compare_field(field, expected_value, flattened_actual)
            if diff:
                diffs.append(f"- [{section_name}] {diff}")

    if diffs:
        print(f"  {runtime}: FAIL ({fixture_id})")
        for diff in diffs:
            print(f"    {diff}")
        return 1

    print(f"  {runtime}: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    prompt_parser = subparsers.add_parser("prompt")
    prompt_parser.add_argument("--fixture", required=True, type=Path)
    prompt_parser.add_argument("--golden", required=True, type=Path)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--golden", required=True, type=Path)
    compare_parser.add_argument("--actual", required=True, type=Path)
    compare_parser.add_argument("--runtime", required=True)
    compare_parser.add_argument("--fixture-id", required=True)

    args = parser.parse_args()
    if args.command == "prompt":
        print(build_prompt(args.fixture, args.golden))
        return 0
    if args.command == "compare":
        return compare(args.golden, args.actual, args.runtime, args.fixture_id)
    raise AssertionError(args.command)


if __name__ == "__main__":
    sys.exit(main())
