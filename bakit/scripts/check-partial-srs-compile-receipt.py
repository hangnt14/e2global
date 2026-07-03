#!/usr/bin/env python3
"""Validate the partial SRS compile receipt for a module."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from guardrail_common import load_contract, render_path, sha256_file

REQUIRED_RECEIPT_FIELDS = {"compile_scope", "requested_sections", "included_sources", "excluded_sources"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", help="Write JSON result to this path")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    contract = load_contract(repo)

    receipt_rel = render_path(
        contract["paths"]["srs_compile_receipt"],
        slug=args.slug,
        date=args.date,
        module=args.module,
    )
    receipt_path = repo / receipt_rel
    srs_rel = render_path(
        contract["paths"]["srs"],
        slug=args.slug,
        date=args.date,
        module=args.module,
    )
    srs_path = repo / srs_rel

    result: dict = {
        "status": "pass",
        "receipt_path": receipt_rel,
        "issues": [],
        "message": "",
    }

    # srs.md exists but receipt missing → block
    if srs_path.exists() and not receipt_path.exists():
        result["status"] = "fail"
        result["issues"].append({"severity": "error", "code": "receipt_missing", "message": f"srs.md exists but receipt missing: {receipt_rel}"})
        result["message"] = f"PARTIAL_COMPILE_RECEIPT_FAIL: receipt_missing"
        output = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(output)
        return 1

    if not receipt_path.exists():
        result["message"] = "PARTIAL_COMPILE_RECEIPT_SKIP: no srs.md and no receipt"
        output = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(output)
        return 0

    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result["status"] = "fail"
        result["issues"].append({"severity": "error", "code": "receipt_invalid_json", "message": str(exc)})
        result["message"] = "PARTIAL_COMPILE_RECEIPT_FAIL: invalid_json"
        output = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(output)
        return 1

    # Check required fields
    for field in REQUIRED_RECEIPT_FIELDS:
        if field not in receipt:
            result["issues"].append({"severity": "error", "code": "receipt_missing_field", "field": field})

    # Validate in-scope source hashes
    source_hashes = receipt.get("source_hashes", {})
    included = receipt.get("included_sources", [])
    stale_sources: list[str] = []
    module_root_rel = render_path(
        contract["paths"]["module_root"],
        slug=args.slug,
        date=args.date,
        module=args.module,
    )
    for src_path_str in included:
        src_path = repo / module_root_rel / src_path_str
        if not src_path.exists():
            result["issues"].append({"severity": "error", "code": "included_source_missing", "file": src_path_str})
            continue
        current_hash = sha256_file(src_path)
        recorded_hash = source_hashes.get(src_path_str, "")
        if recorded_hash and current_hash != recorded_hash:
            stale_sources.append(src_path_str)

    if stale_sources:
        result["issues"].append({"severity": "error", "code": "in_scope_sources_stale", "files": stale_sources})

    errors = [i for i in result["issues"] if i["severity"] == "error"]
    result["status"] = "fail" if errors else "pass"
    result["stale_in_scope_sources"] = stale_sources
    result["message"] = (
        f"PARTIAL_COMPILE_RECEIPT_FAIL: errors={len(errors)}"
        if errors
        else f"PARTIAL_COMPILE_RECEIPT_PASS: scope={receipt.get('compile_scope', 'unknown')}"
    )

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
