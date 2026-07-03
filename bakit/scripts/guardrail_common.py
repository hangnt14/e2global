#!/usr/bin/env python3
"""Shared helpers for runtime hard guardrail scripts."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SECTION_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

INDEX_TABLE_HEADERS = {
    "backbone_index": "Section Index",
    "stories_index": "Story Index",
    "srs_index": "SRS Index",
    "userstories_index": "Story Index",
    "usecases_index": "Use Case Index",
    "ascii_screen_index": "Screen Index",
}

INDEX_SOURCE_KEYS = {
    "backbone_index": "backbone",
    "stories_index": "stories",
    "srs_index": "srs",
    "userstories_index": "userstories_root",
    "usecases_index": "usecases_root",
    "ascii_screen_index": "ascii_screen_root",
}

COMMAND_POLICIES = {
    "frd": {
        "guardrail_mode": "index-first",
        "required_indexes": ["backbone_index"],
        "required_reads": ["core/contract.yaml", "core/contract-behavior.md", "backbone_index", "plan"],
        "deny_reads": ["backbone"],
        "action_guardrail": {
            "required": True,
            "navigation_source": "backbone_index",
            "packet_scope": "per-action",
            "reason": "consult backbone_index before broader backbone reads",
        },
        "project_home_override": False,
    },
    "stories": {
        "guardrail_mode": "index-first",
        "required_indexes": ["backbone_index"],
        "required_reads": ["core/contract.yaml", "core/contract-behavior.md", "backbone_index", "plan", "frd"],
        "deny_reads": ["backbone"],
        "action_guardrail": {
            "required": True,
            "navigation_source": "backbone_index",
            "packet_scope": "per-action",
            "reason": "consult backbone_index before broader backbone reads",
        },
        "project_home_override": False,
    },
    "srs": {
        "guardrail_mode": "index-first",
        "required_indexes": ["backbone_index", "userstories_index"],
        "required_reads": ["core/contract.yaml", "core/contract-behavior.md", "backbone_index", "userstories_index"],
        "deny_reads": ["backbone"],
        "action_guardrail": {
            "required": True,
            "navigation_source": "backbone_index",
            "packet_scope": "per-action",
            "reason": "consult backbone_index before broader backbone reads; validate backbone alignment before writing module artifacts",
        },
        "project_home_override": False,
    },
    "package": {
        "guardrail_mode": "index-first",
        "required_indexes": ["backbone_index", "userstories_index", "usecases_index", "ascii_screen_index"],
        "required_reads": ["core/contract.yaml", "core/contract-behavior.md", "backbone_index", "userstories_index", "usecases_index", "ascii_screen_index", "memory_index", "project_memory"],
        "deny_reads": ["source_summary", "source_chunk_index", "intake", "backbone", "memory_log"],
        "action_guardrail": {
            "required": True,
            "navigation_source": "backbone_index",
            "packet_scope": "per-action",
            "reason": "consult backbone_index before broader backbone discovery",
        },
        "project_home_override": False,
    },
    "status": {
        "guardrail_mode": "canonical-state-first",
        "required_indexes": [],
        "required_reads": ["core/contract.yaml", "core/contract-behavior.md", "project_home", "memory_index", "project_memory"],
        "deny_reads": [],
        "action_guardrail": {
            "required": False,
            "navigation_source": "",
            "packet_scope": "",
            "reason": "",
        },
        "project_home_override": True,
    },
    "next": {
        "guardrail_mode": "canonical-state-first",
        "required_indexes": [],
        "required_reads": ["core/contract.yaml", "core/contract-behavior.md", "project_home", "memory_index", "project_memory"],
        "deny_reads": [],
        "action_guardrail": {
            "required": False,
            "navigation_source": "",
            "packet_scope": "",
            "reason": "",
        },
        "project_home_override": True,
    },
}

REQUIRED_METADATA_FIELDS = {
    "index_type",
    "source_artifact",
    "source_hash",
    "generated_at",
    "generated_by_command",
    "validated_at",
    "validated_by",
    "stale_status",
}

INDEX_VALIDATION_RULES = {
    "backbone_index": {
        "required_columns": ["Section", "Anchor / Heading", "Trace IDs", "Module / Feature", "Short Summary"],
        "required_row_fields": ["Anchor / Heading", "Trace IDs", "Module / Feature"],
        "target_field": "Anchor / Heading",
        "id_fields": ["Trace IDs"],
        "coverage_patterns": [
            r"\b(?:BG|ACT|PORTAL|F|FR|NFR|EP|R|SCR|MEM)-[A-Za-z0-9-]+\b",
            r"\bA\d+\b",
        ],
        "action_guardrail": {
            "required": True,
            "navigation_source": "backbone_index",
            "packet_scope": "per-action",
            "reason": "consult backbone_index before broader backbone reads",
        },
    },
    "stories_index": {
        "required_columns": ["Epic / Story ID", "Feature / FR", "Acceptance Criteria Count", "Screen IDs", "Path / Heading"],
        "required_row_fields": ["Epic / Story ID", "Feature / FR", "Acceptance Criteria Count", "Path / Heading"],
        "target_field": "Path / Heading",
        "id_fields": ["Epic / Story ID", "Feature / FR", "Screen IDs"],
        "coverage_patterns": [r"\b(?:US|FR|SCR)-[A-Za-z0-9-]+\b"],
        "count_fields": ["Acceptance Criteria Count"],
        "action_guardrail": {
            "required": True,
            "navigation_source": "backbone_index",
            "packet_scope": "per-action",
            "reason": "re-enter through backbone_index before broader downstream action context",
        },
    },
    "srs_index": {
        "required_columns": ["Group", "UC / SCR / Rule / Message IDs", "Screen / Flow", "Path / Heading", "Dependency"],
        "required_row_fields": ["Group", "UC / SCR / Rule / Message IDs", "Path / Heading", "Dependency"],
        "target_field": "Path / Heading",
        "id_fields": ["UC / SCR / Rule / Message IDs", "Dependency"],
        "coverage_patterns": [r"\b(?:UC|SCR|CR|MSG|FR|NFR)-[A-Za-z0-9-]+\b"],
        "action_guardrail": {
            "required": True,
            "navigation_source": "backbone_index",
            "packet_scope": "per-action",
            "reason": "re-enter through backbone_index before broad backbone-backed downstream action context",
        },
    },
    "userstories_index": {
        "required_columns": ["Story ID", "File", "Actor", "Feature / FR", "Acceptance Criteria Count", "Linked Use Cases", "Linked Screens", "Source Backbone IDs", "Stale Status"],
        "required_row_fields": ["Story ID", "File", "Actor", "Feature / FR", "Acceptance Criteria Count"],
        "target_field": "File",
        "id_fields": ["Story ID", "Feature / FR", "Linked Use Cases", "Linked Screens", "Source Backbone IDs"],
        "coverage_patterns": [r"\b(?:US|FR|UC|SCR)-[A-Za-z0-9-]+\b"],
        "count_fields": ["Acceptance Criteria Count"],
        "action_guardrail": {
            "required": True,
            "navigation_source": "backbone_index",
            "packet_scope": "per-action",
            "reason": "re-enter through backbone_index before broader downstream action context",
        },
    },
    "usecases_index": {
        "required_columns": ["UC ID", "File", "Actor", "Trigger", "Linked Stories", "Linked Screens", "Source Backbone IDs", "Stale Status"],
        "required_row_fields": ["UC ID", "File", "Actor", "Trigger"],
        "target_field": "File",
        "id_fields": ["UC ID", "Linked Stories", "Linked Screens", "Source Backbone IDs"],
        "coverage_patterns": [r"\b(?:UC|US|SCR)-[A-Za-z0-9-]+\b"],
        "action_guardrail": {
            "required": True,
            "navigation_source": "backbone_index",
            "packet_scope": "per-action",
            "reason": "re-enter through backbone_index before broader downstream action context",
        },
    },
    "ascii_screen_index": {
        "required_columns": ["Screen ID", "File", "Portal ID", "Nav Schema ID", "Actor", "Linked UCs", "Linked Stories", "ASCII Status", "Stale Status"],
        "required_row_fields": ["Screen ID", "File", "Portal ID", "Nav Schema ID", "Actor"],
        "target_field": "File",
        "id_fields": ["Screen ID", "Linked UCs", "Linked Stories"],
        "coverage_patterns": [r"\b(?:SCR|UC|US)-[A-Za-z0-9-]+\b"],
        "action_guardrail": {
            "required": True,
            "navigation_source": "backbone_index",
            "packet_scope": "per-action",
            "reason": "re-enter through backbone_index before broader downstream action context",
        },
    },
}

STALENESS_PRECEDENCE = {
    "current": 0,
    "stale": 1,
    "unknown": 2,
    "missing": 3,
    "contradictory": 4,
}


def load_contract(repo: Path) -> dict[str, Any]:
    # Try ~/.claude/core/ first (installed BA-kit contract), then {repo}/core/
    home_contract = Path.home() / ".claude" / "core" / "contract.yaml"
    if home_contract.exists():
        return json.loads(home_contract.read_text(encoding="utf-8"))
    p = repo / "core" / "contract.yaml"
    if not p.exists():
        sys.exit(f"Contract not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def render_path(template: str, *, slug: str, date: str, module: str = "", option: str = "*", group: str = "*", source_hash: str = "*") -> str:
    return (
        template.replace("{slug}", slug)
        .replace("{date}", date)
        .replace("{module_slug}", module)
        .replace("{option}", option)
        .replace("{group}", group)
        .replace("{source_hash}", source_hash)
    )


def strip_code(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        value = value[1:-1]
    return value.strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_source_hash(path: Path) -> str:
    """Compute SHA-256 hash of source artifact.

    For files: hash of file contents.
    For directories: combined hash of all *.md files within.
    """
    if path.is_dir():
        source_files = sorted(f for f in path.glob("*.md") if f.name != "index.md")
        if not source_files:
            return ""
        combined = "".join(sha256_file(sf) for sf in source_files)
        return hashlib.sha256(combined.encode()).hexdigest()
    return sha256_file(path)


def parse_markdown_table(lines: list[str], start_index: int) -> tuple[list[str], list[dict[str, str]], int]:
    header_cells = [cell.strip() for cell in lines[start_index].strip().strip("|").split("|")]
    rows: list[dict[str, str]] = []
    i = start_index + 2
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(header_cells):
            break
        rows.append(dict(zip(header_cells, cells)))
        i += 1
    return header_cells, rows, i


def find_heading(lines: list[str], target_heading: str) -> int | None:
    normalized = normalize_heading(target_heading)
    for idx, line in enumerate(lines):
        match = SECTION_RE.match(line.strip())
        if match and normalize_heading(match.group(2)) == normalized:
            return idx
    return None


def normalize_heading(value: str) -> str:
    return re.sub(r"\s+", " ", strip_code(value).lower()).strip()

def split_list_tokens(value: str) -> list[str]:
    if not value.strip():
        return []
    return [
        token
        for token in (strip_code(part) for part in re.split(r"[;,]", value))
        if token
    ]

def extract_id_tokens(text: str, patterns: list[str]) -> set[str]:
    tokens: set[str] = set()
    for pattern in patterns:
        tokens.update(re.findall(pattern, text))
    return tokens


def parse_index_file(index_path: Path) -> dict[str, Any]:
    text = index_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    metadata: dict[str, str] = {}
    table_rows: list[dict[str, str]] = []

    for idx, line in enumerate(lines):
        if line.strip() == "| Field | Value |":
            _, rows, _ = parse_markdown_table(lines, idx)
            metadata = {row["Field"]: strip_code(row["Value"]) for row in rows if "Field" in row and "Value" in row}
            break

    for heading in INDEX_TABLE_HEADERS.values():
        heading_line = f"## {heading}"
        for idx, line in enumerate(lines):
            if line.strip() == heading_line:
                for j in range(idx + 1, len(lines)):
                    if lines[j].strip().startswith("|") and "Field | Value" not in lines[j]:
                        _, rows, _ = parse_markdown_table(lines, j)
                        table_rows = rows
                        return {"metadata": metadata, "rows": table_rows, "text": text}

    return {"metadata": metadata, "rows": table_rows, "text": text}


def expected_source_path(contract: dict[str, Any], *, index_key: str, slug: str, date: str, module: str) -> str:
    source_key = INDEX_SOURCE_KEYS[index_key]
    template = contract["paths"].get(source_key, "")
    if not template:
        return ""
    return render_path(template, slug=slug, date=date, module=module)


def classify_index_state(
    *,
    repo: Path,
    contract: dict[str, Any],
    index_key: str,
    slug: str,
    date: str,
    module: str,
    feature: str = "",
    trace_id: str = "",
    heading: str = "",
    require_extractable: bool = False,
) -> dict[str, Any]:
    index_rel = render_path(contract["paths"][index_key], slug=slug, date=date, module=module)
    index_path = repo / index_rel
    if not index_path.exists():
        return {"state": "missing", "path": index_rel, "reason": "index_missing"}

    parsed = parse_index_file(index_path)
    metadata = parsed["metadata"]
    rows = parsed["rows"]
    missing_fields = sorted(
        field
        for field in REQUIRED_METADATA_FIELDS
        if field not in metadata or not metadata.get(field, "").strip()
    )
    if missing_fields:
        return {
            "state": "contradictory",
            "path": index_rel,
            "reason": f"missing_metadata:{','.join(missing_fields)}",
        }

    expected_source = expected_source_path(contract, index_key=index_key, slug=slug, date=date, module=module)
    if metadata["source_artifact"] != expected_source:
        return {
            "state": "contradictory",
            "path": index_rel,
            "reason": "source_artifact_mismatch",
            "source_artifact": metadata["source_artifact"],
            "expected_source_artifact": expected_source,
        }

    source_path = repo / expected_source
    if not source_path.exists():
        return {
            "state": "contradictory",
            "path": index_rel,
            "reason": "source_artifact_missing",
            "source_artifact": expected_source,
        }

    file_state = metadata["stale_status"].strip().lower()
    if file_state not in {"current", "stale", "unknown"}:
        return {
            "state": "contradictory",
            "path": index_rel,
            "reason": f"invalid_stale_status:{file_state}",
            "source_artifact": expected_source,
        }

    source_hash = compute_source_hash(source_path)
    if metadata["source_hash"] != source_hash:
        return {
            "state": "stale",
            "path": index_rel,
            "reason": "source_hash_mismatch",
            "source_artifact": expected_source,
            "actual_source_hash": source_hash,
        }

    if file_state in {"stale", "unknown"}:
        return {
            "state": file_state,
            "path": index_rel,
            "reason": f"metadata_stale_status:{file_state}",
            "source_artifact": expected_source,
        }

    if not rows:
        return {
            "state": "stale",
            "path": index_rel,
            "reason": "routing_rows_missing",
            "source_artifact": expected_source,
        }

    if not rows_cover_requested_slice(
        index_key=index_key,
        rows=rows,
        module=module,
        feature=feature,
        trace_id=trace_id,
        heading=heading,
    ):
        return {
            "state": "stale",
            "path": index_rel,
            "reason": "routing_coverage_missing",
            "source_artifact": expected_source,
        }

    if require_extractable:
        headings = candidate_index_headings(
            index_key=index_key,
            rows=rows,
            module=module,
            feature=feature,
            heading=heading,
            trace_id=trace_id,
        )
        if not headings:
            return {
                "state": "stale",
                "path": index_rel,
                "reason": "routing_headings_missing",
                "source_artifact": expected_source,
            }

        sections = extract_sections_by_headings(source_path.read_text(encoding="utf-8"), headings)
        if not sections:
            return {
                "state": "stale",
                "path": index_rel,
                "reason": "source_excerpt_missing",
                "source_artifact": expected_source,
            }

    return {
        "state": "current",
        "path": index_rel,
        "reason": "ok",
        "source_artifact": expected_source,
        "rows": rows,
        "metadata": metadata,
    }


def dominant_state(states: list[str]) -> str:
    return max(states, key=lambda value: STALENESS_PRECEDENCE[value])


def coerce_path_entries(
    *,
    repo: Path,
    contract: dict[str, Any],
    slug: str,
    date: str,
    module: str,
    keys: list[str],
) -> list[str]:
    entries: list[str] = []
    for key in keys:
        if key.startswith("core/"):
            entries.append(key)
            continue
        template = contract["paths"].get(key)
        if not template:
            continue
        entries.append(render_path(template, slug=slug, date=date, module=module))
    return entries


def rows_cover_requested_slice(
    *,
    index_key: str,
    rows: list[dict[str, str]],
    module: str,
    feature: str,
    trace_id: str,
    heading: str,
) -> bool:
    filters = [value for value in (module, feature, trace_id, heading) if value]
    if not filters:
        return True

    for row in rows:
        if row_matches_requested_slice(
            index_key=index_key,
            row=row,
            module=module,
            feature=feature,
            trace_id=trace_id,
            heading=heading,
        ):
            return True
    return False

def row_heading(index_key: str, row: dict[str, str]) -> str:
    if index_key == "backbone_index":
        return strip_code(row.get("Anchor / Heading", ""))
    return strip_code(row.get("Path / Heading", ""))

def row_target(index_key: str, row: dict[str, str]) -> str:
    return row_heading(index_key, row)

def row_matches_requested_slice(
    *,
    index_key: str,
    row: dict[str, str],
    module: str,
    feature: str,
    trace_id: str,
    heading: str,
) -> bool:
    haystack = " ".join(strip_code(value).lower() for value in row.values())
    if module and module.lower() not in haystack:
        return False
    if feature and feature.lower() not in haystack:
        return False
    if trace_id and trace_id.lower() not in haystack:
        return False
    if heading and normalize_heading(row_heading(index_key, row)) != normalize_heading(heading):
        return False
    return True

def candidate_index_headings(
    *,
    index_key: str,
    rows: list[dict[str, str]],
    module: str,
    feature: str,
    heading: str,
    trace_id: str,
) -> list[str]:
    headings: list[str] = []
    for row in rows:
        if not row_matches_requested_slice(
            index_key=index_key,
            row=row,
            module=module,
            feature=feature,
            trace_id=trace_id,
            heading=heading,
        ):
            continue
        heading_value = row_heading(index_key, row)
        if heading_value:
            headings.append(heading_value)

    deduped: list[str] = []
    seen = set()
    for item in headings:
        key = normalize_heading(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def extract_sections_by_headings(source_text: str, headings: list[str]) -> list[dict[str, str]]:
    lines = source_text.splitlines()
    matches: list[dict[str, str]] = []
    for heading in headings:
        start = find_heading(lines, heading)
        if start is None:
            continue
        start_match = SECTION_RE.match(lines[start].strip())
        assert start_match is not None
        level = len(start_match.group(1))
        end = len(lines)
        for idx in range(start + 1, len(lines)):
            match = SECTION_RE.match(lines[idx].strip())
            if match and len(match.group(1)) <= level:
                end = idx
                break
        content = "\n".join(lines[start:end]).strip() + "\n"
        matches.append({"heading": heading, "content": content})
    return matches

def rows_have_required_columns(index_key: str, rows: list[dict[str, str]]) -> tuple[bool, list[str]]:
    if index_key not in INDEX_VALIDATION_RULES:
        return True, []
    required_columns = INDEX_VALIDATION_RULES[index_key]["required_columns"]
    present = set(rows[0].keys()) if rows else set()
    missing = [column for column in required_columns if column not in present]
    return not missing, missing

def row_missing_required_fields(index_key: str, row: dict[str, str]) -> list[str]:
    required = INDEX_VALIDATION_RULES.get(index_key, {}).get("required_row_fields", [])
    return [field for field in required if not strip_code(row.get(field, ""))]

def row_ids(index_key: str, row: dict[str, str]) -> set[str]:
    rule = INDEX_VALIDATION_RULES.get(index_key, {})
    ids: set[str] = set()
    for field in rule.get("id_fields", []):
        ids.update(extract_id_tokens(strip_code(row.get(field, "")), rule.get("coverage_patterns", [])))
    return ids

def source_ids(index_key: str, source_text: str) -> set[str]:
    rule = INDEX_VALIDATION_RULES.get(index_key, {})
    return extract_id_tokens(source_text, rule.get("coverage_patterns", []))

def validate_row_target(index_key: str, row: dict[str, str], *, source_path: Path, source_text: str) -> tuple[bool, str]:
    target = row_target(index_key, row)
    if not target:
        return False, "missing_target"
    if target.endswith(".md"):
        target_path = (source_path.parent / target).resolve()
        return target_path.exists(), f"missing_target_file:{target}"
    if find_heading(source_text.splitlines(), target) is None:
        return False, f"missing_target_heading:{target}"
    return True, "ok"

def action_guardrail_for_index(index_key: str) -> dict[str, str | bool]:
    return dict(INDEX_VALIDATION_RULES.get(index_key, {}).get("action_guardrail", {}))


def load_json_input(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_paths(paths: list[str]) -> list[str]:
    return [Path(path).as_posix() for path in paths]


def parse_options_status(plan_text: str) -> str:
    patterns = [
        r"options status\s*[:|]\s*(recommended|in-progress|completed|skipped|not-needed)",
        r"phương án giải pháp\s*\|\s*(recommended|in-progress|completed|skipped|not-needed)\s*\|",
    ]
    for pattern in patterns:
        match = re.search(pattern, plan_text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return ""


def plan_records_selected_option(plan_text: str) -> bool:
    return bool(re.search(r"selected option", plan_text, re.IGNORECASE))

def project_home_conflicts(project_home_text: str, *, expected_next_command: str) -> bool:
    text = project_home_text.lower()
    if not text.strip():
        return False

    mentioned_steps = {
        step
        for step in ("options", "backbone", "stories", "frd", "srs", "wireframes", "package")
        if re.search(rf"\b{step}\b", text)
    }
    if not mentioned_steps:
        return False

    expected_step = ""
    match = re.search(r"ba-start\s+([a-z-]+)", expected_next_command.lower())
    if match:
        expected_step = match.group(1)
        mentioned_steps.discard(expected_step)
    return bool(mentioned_steps)


def build_canonical_state_summary(repo: Path, contract: dict[str, Any], *, slug: str, date: str, module: str, command: str) -> dict[str, str]:
    paths = contract["paths"]
    intake_path = repo / render_path(paths["intake"], slug=slug, date=date, module=module)
    plan_path = repo / render_path(paths["plan"], slug=slug, date=date, module=module)
    backbone_path = repo / render_path(paths["backbone"], slug=slug, date=date, module=module)
    project_home_path = repo / render_path(paths["project_home"], slug=slug, date=date, module=module)

    status = ""
    selected_option = False
    if plan_path.exists():
        plan_text = plan_path.read_text(encoding="utf-8")
        status = parse_options_status(plan_text)
        selected_option = plan_records_selected_option(plan_text)
    project_home_text = project_home_path.read_text(encoding="utf-8") if project_home_path.exists() else ""

    summary = "canonical artifacts unresolved"
    next_command = ""
    visible_warning = ""

    if backbone_path.exists():
        summary = "backbone present"
    elif status in {"recommended", "in-progress"}:
        summary = f"options still {status} from plan.md"
        next_command = f"ba-start options --slug {slug}"
    elif status == "not-needed":
        summary = "options not-needed from plan.md"
        next_command = f"ba-start backbone --slug {slug}"
    elif status == "skipped":
        summary = "options skipped from plan.md"
        next_command = f"ba-start backbone --slug {slug}"
    elif status == "completed" and selected_option:
        summary = "options completed with selected option from plan.md"
        next_command = f"ba-start backbone --slug {slug}"
    elif intake_path.exists():
        summary = "intake present; options ledger unresolved"
        if command == "next":
            next_command = f"ba-start status --slug {slug}"

    if next_command and project_home_conflicts(project_home_text, expected_next_command=next_command):
        visible_warning = "PROJECT_HOME_CONFLICT"

    return {
        "canonical_state_summary": summary,
        "canonical_next_command": next_command,
        "visible_warning": visible_warning,
    }
