#!/usr/bin/env python3
"""Validate the SRS source set for a module (srs/spec.md, flows.md, states.md, erd.md)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from guardrail_common import load_contract, render_path, sha256_file

REQUIRED_SOURCE_FILES = ["srs/spec.md"]
OPTIONAL_SOURCE_FILES = ["srs/flows.md", "srs/states.md", "srs/erd.md"]


def check_source_file(path: Path) -> dict:
    if not path.exists():
        return {"state": "missing", "hash": ""}
    return {"state": "present", "hash": sha256_file(path)}


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

    module_root = repo / render_path(
        contract["paths"]["module_root"],
        slug=args.slug,
        date=args.date,
        module=args.module,
    )

    result: dict = {
        "status": "pass",
        "module": args.module,
        "required": {},
        "optional": {},
        "issues": [],
    }

    for rel in REQUIRED_SOURCE_FILES:
        info = check_source_file(module_root / rel)
        result["required"][rel] = info
        if info["state"] == "missing":
            result["issues"].append({"severity": "error", "code": "required_source_missing", "file": rel})

    for rel in OPTIONAL_SOURCE_FILES:
        info = check_source_file(module_root / rel)
        result["optional"][rel] = info

    errors = [i for i in result["issues"] if i["severity"] == "error"]
    result["status"] = "fail" if errors else "pass"
    result["message"] = (
        f"SRS_SOURCE_SET_FAIL: missing={[i['file'] for i in errors]}"
        if errors
        else f"SRS_SOURCE_SET_PASS: module={args.module}"
    )

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
