#!/usr/bin/env python3
"""Validate producer-side quality for BA index artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from guardrail_common import (
    INDEX_TABLE_HEADERS,
    INDEX_VALIDATION_RULES,
    REQUIRED_METADATA_FIELDS,
    action_guardrail_for_index,
    compute_source_hash,
    expected_source_path,
    extract_id_tokens,
    load_contract,
    parse_index_file,
    row_ids,
    row_missing_required_fields,
    row_target,
    rows_have_required_columns,
    sha256_file,
    source_ids,
    split_list_tokens,
    strip_code,
    validate_row_target,
)

VALIDATOR_NAME = "scripts/validate-index-quality.py"
VALID_STALE_STATUS = {"current", "stale", "unknown"}
MIGRATION_METADATA_FIELDS = {"validated_at", "validated_by"}

# Prefixes allowed by backbone_index coverage_patterns (single source of truth: guardrail_common.py)
_ALLOWED_ID_PREFIXES = ["BG", "ACT", "PORTAL", "F", "MOD", "FR", "NFR", "EP", "R", "SCR", "MEM"]
_ALLOWED_ID_PREFIXES_DISPLAY = ", ".join(_ALLOWED_ID_PREFIXES) + ", A{N}"


def _allowed_prefixes_text() -> str:
    return _ALLOWED_ID_PREFIXES_DISPLAY


def issue(severity: str, code: str, message: str, *, row: int | None = None, field: str = "") -> dict[str, Any]:
    data: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if row is not None:
        data["row"] = row
    if field:
        data["field"] = field
    return data


def detect_format_siblings(missing_ids: list[str], indexed_ids: set[str]) -> list[dict[str, str]]:
    """Detect source IDs whose normalized form matches an indexed ID — formatting inconsistency.

    Example: source has FR-1, index has FR-01 — both normalize to prefix=FR num=1.
    Returns list of dicts with keys: missing, indexed, prefix, num.
    """
    import re

    id_pat = re.compile(r"^([A-Z]+)[-]?0*(\d+)$")
    siblings: list[dict[str, str]] = []

    # Build normalized lookup from indexed IDs
    indexed_norm: dict[tuple[str, int], str] = {}
    for iid in indexed_ids:
        m = id_pat.match(iid)
        if m:
            prefix, num = m.groups()
            indexed_norm[(prefix, int(num))] = iid

    for mid in missing_ids:
        m = id_pat.match(mid)
        if not m:
            continue
        prefix, num = m.groups()
        key = (prefix, int(num))
        if key in indexed_norm:
            siblings.append({
                "missing": mid,
                "indexed": indexed_norm[key],
                "prefix": prefix,
                "num": str(key[1]),
            })

    return siblings


def update_metadata_table(index_text: str, updates: dict[str, str]) -> str:
    lines = index_text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == "| Field | Value |":
            start = idx
            break
    if start is None:
        raise ValueError("metadata_table_missing")

    row_start = start + 2
    row_end = row_start
    field_rows: dict[str, int] = {}
    while row_end < len(lines):
        stripped = lines[row_end].strip()
        if not stripped.startswith("|"):
            break
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) >= 2:
            field_rows[cells[0]] = row_end
        row_end += 1

    insert_at = row_end
    for field, value in updates.items():
        rendered = f"| {field} | `{value}` |"
        if field in field_rows:
            lines[field_rows[field]] = rendered
        else:
            lines.insert(insert_at, rendered)
            insert_at += 1

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--index-key", choices=sorted(INDEX_TABLE_HEADERS), required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", default="")
    parser.add_argument("--output", help="Write JSON output to this path as well as stdout")
    parser.add_argument("--writeback", action="store_true", help="Write validator metadata and suggested stale_status back into the index file")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    contract = load_contract(repo)
    index_rel = contract["paths"][args.index_key].replace("{slug}", args.slug).replace("{date}", args.date).replace("{module_slug}", args.module)
    index_path = repo / index_rel

    result: dict[str, Any] = {
        "status": "fail",
        "index_key": args.index_key,
        "index_path": index_rel,
        "source_artifact": "",
        "current_issuable": False,
        "suggested_stale_status": "stale",
        "action_guardrail": action_guardrail_for_index(args.index_key),
        "stats": {
            "row_count": 0,
            "source_id_count": 0,
            "indexed_id_count": 0,
            "missing_source_ids": [],
        },
        "issues": [],
        "message": "",
    }

    if not index_path.exists():
        result["issues"].append(issue("error", "index_missing", f"Index file missing: {index_rel}"))
        result["message"] = f"INDEX_VALIDATION_FAIL: index_key={args.index_key} reason=index_missing"
        text = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(text)
        return 1

    parsed = parse_index_file(index_path)
    metadata = parsed["metadata"]
    rows = parsed["rows"]
    source_text = ""

    hard_missing_metadata = sorted(
        field
        for field in (REQUIRED_METADATA_FIELDS - MIGRATION_METADATA_FIELDS)
        if field not in metadata or not metadata.get(field, "").strip()
    )
    if hard_missing_metadata:
        for field in hard_missing_metadata:
            result["issues"].append(issue("error", "missing_metadata", f"Missing required metadata field: {field}", field=field))

    missing_validation_metadata = sorted(
        field
        for field in MIGRATION_METADATA_FIELDS
        if field not in metadata or not metadata.get(field, "").strip()
    )
    for field in missing_validation_metadata:
        result["issues"].append(issue("warn", "missing_validation_metadata", f"Missing validation metadata field: {field}", field=field))

    expected_source = expected_source_path(contract, index_key=args.index_key, slug=args.slug, date=args.date, module=args.module)
    actual_source = metadata.get("source_artifact", "")
    result["source_artifact"] = actual_source or expected_source
    if actual_source and actual_source != expected_source:
        result["issues"].append(issue("error", "source_artifact_mismatch", f"Expected source_artifact={expected_source}, got {actual_source}", field="source_artifact"))

    source_path = repo / expected_source
    if not source_path.exists():
        result["issues"].append(issue("error", "source_artifact_missing", f"Source artifact missing: {expected_source}"))
    else:
        actual_hash = compute_source_hash(source_path)
        if actual_hash and metadata.get("source_hash", "") and metadata["source_hash"] != actual_hash:
            result["issues"].append(issue("error", "source_hash_mismatch", f"source_hash does not match current source for {expected_source}", field="source_hash"))
        if source_path.is_file():
            source_text = source_path.read_text(encoding="utf-8")

    stale_status = metadata.get("stale_status", "").strip().lower()
    if stale_status and stale_status not in VALID_STALE_STATUS:
        result["issues"].append(issue("error", "invalid_stale_status", f"Invalid stale_status: {stale_status}", field="stale_status"))

    result["stats"]["row_count"] = len(rows)
    if not rows:
        result["issues"].append(issue("error", "routing_rows_missing", "Index has no routing rows"))
    else:
        valid_columns, missing_columns = rows_have_required_columns(args.index_key, rows)
        if not valid_columns:
            for column in missing_columns:
                result["issues"].append(issue("error", "missing_column", f"Missing required column: {column}", field=column))

    indexed_ids: set[str] = set()
    duplicate_signatures: set[tuple[str, str]] = set()
    seen_signatures: set[tuple[str, str]] = set()
    for idx, row in enumerate(rows, start=1):
        missing_fields = row_missing_required_fields(args.index_key, row)
        for field in missing_fields:
            result["issues"].append(issue("error", "missing_row_field", f"Row {idx} missing required field {field}", row=idx, field=field))

        ids = row_ids(args.index_key, row)
        indexed_ids.update(ids)
        if not ids:
            raw_trace = strip_code(row.get("Trace IDs", ""))
            import re as _re
            raw_tokens = _re.findall(r"\b[A-Z][A-Za-z0-9][A-Za-z0-9-]*\b", raw_trace)
            detail = ""
            if raw_tokens:
                detail = f" Trace IDs column contains: {', '.join(raw_tokens[:8])}. Allowed prefixes: {_allowed_prefixes_text()}."
            result["issues"].append(issue("error", "row_ids_missing", f"Row {idx} has no detectable trace or route IDs.{detail}", row=idx))

        for field in INDEX_VALIDATION_RULES[args.index_key].get("count_fields", []):
            value = strip_code(row.get(field, ""))
            if not value.isdigit() or int(value) <= 0:
                result["issues"].append(issue("error", "invalid_count_field", f"Row {idx} has invalid {field}: {value or '<empty>'}", row=idx, field=field))

        # Verify indexed file exists on disk (resolve from module root, not index parent)
        file_field = row.get("File", "")
        if file_field and file_field != "—":
            fname = strip_code(file_field)
            if fname:
                # File column has paths like "usecases/uc-login.md" relative to module root
                module_root = index_path.parent.parent
                if not (module_root / fname).exists():
                    result["issues"].append(issue("error", "indexed_file_missing", f"Row {idx}: indexed file does not exist: {fname}", row=idx, field="File"))

        if source_text:
            valid_target, reason = validate_row_target(args.index_key, row, source_path=source_path, source_text=source_text)
            if not valid_target:
                result["issues"].append(issue("error", "invalid_route_target", f"Row {idx} target is not extractable: {reason}", row=idx))

            row_text = " ".join(strip_code(value) for value in row.values())
            row_expected_ids = extract_id_tokens(row_text, INDEX_VALIDATION_RULES[args.index_key]["coverage_patterns"])
            missing_in_source = sorted(token for token in row_expected_ids if token not in source_text)
            if missing_in_source:
                result["issues"].append(issue("error", "row_id_missing_in_source", f"Row {idx} references IDs not found in source: {', '.join(missing_in_source)}", row=idx))

        signature = ("|".join(sorted(ids)), row_target(args.index_key, row))
        if signature in seen_signatures:
            duplicate_signatures.add(signature)
        else:
            seen_signatures.add(signature)

    for ids, target in sorted(duplicate_signatures):
        result["issues"].append(issue("error", "duplicate_route_signature", f"Duplicate route signature ids={ids} target={target}"))

    if source_text:
        discovered_source_ids = source_ids(args.index_key, source_text)
        result["stats"]["source_id_count"] = len(discovered_source_ids)
        result["stats"]["indexed_id_count"] = len(indexed_ids)
        missing_source_ids = sorted(discovered_source_ids - indexed_ids)
        result["stats"]["missing_source_ids"] = missing_source_ids
        if missing_source_ids:
            result["issues"].append(
                issue(
                    "error",
                    "source_coverage_missing",
                    f"Index does not cover source IDs: {', '.join(missing_source_ids[:20])}",
                )
            )
            # Detect format inconsistencies: FR-1 in source vs FR-01 in index
            siblings = detect_format_siblings(missing_source_ids, indexed_ids)
            if siblings:
                examples = [f"{s['missing']} vs {s['indexed']}" for s in siblings[:5]]
                result["issues"].append(
                    issue(
                        "warn",
                        "format_sibling_detected",
                        f"Source and index may use different ID formats for the same entities: {', '.join(examples)}. Normalize backbone.md to consistent format.",
                    )
                )

    errors = [item for item in result["issues"] if item["severity"] == "error"]
    warnings = [item for item in result["issues"] if item["severity"] == "warn"]

    if errors:
        result["status"] = "fail"
        result["current_issuable"] = False
        result["suggested_stale_status"] = "stale"
        result["message"] = f"INDEX_VALIDATION_FAIL: index_key={args.index_key} errors={len(errors)} warnings={len(warnings)}"
    elif warnings:
        result["status"] = "warn"
        result["current_issuable"] = True
        result["suggested_stale_status"] = "current"
        result["message"] = f"INDEX_VALIDATION_WARN: index_key={args.index_key} warnings={len(warnings)} action={result['action_guardrail'].get('navigation_source', '')}"
    else:
        result["status"] = "pass"
        result["current_issuable"] = True
        result["suggested_stale_status"] = "current"
        result["message"] = f"INDEX_VALIDATION_PASS: index_key={args.index_key} rows={len(rows)} indexed_ids={len(indexed_ids)} action={result['action_guardrail'].get('navigation_source', '')}"

    if args.writeback:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        validated_at = timestamp if result["current_issuable"] else ""
        validated_by = VALIDATOR_NAME if result["current_issuable"] else ""
        updated = update_metadata_table(
            parsed["text"],
            {
                "validated_at": validated_at,
                "validated_by": validated_by,
                "stale_status": result["suggested_stale_status"],
            },
        )
        index_path.write_text(updated, encoding="utf-8")
        result["writeback"] = {
            "applied": True,
            "validated_at": validated_at,
            "validated_by": validated_by,
            "stale_status": result["suggested_stale_status"],
        }

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
