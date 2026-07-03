#!/usr/bin/env python3
"""Validate userstories/index.md for a module against the new folder-based canon."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from guardrail_common import (
    classify_index_state,
    load_contract,
    render_path,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", help="Write JSON result to this path")
    parser.add_argument("--feature", default="")
    parser.add_argument("--trace-id", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    contract = load_contract(repo)

    result = classify_index_state(
        repo=repo,
        contract=contract,
        index_key="userstories_index",
        slug=args.slug,
        date=args.date,
        module=args.module,
        feature=args.feature,
        trace_id=args.trace_id,
    )

    # Verify each story file listed in the index actually exists
    if result["state"] == "current" and "rows" in result:
        missing_files: list[str] = []
        module_root = repo / render_path(
            contract["paths"]["module_root"],
            slug=args.slug,
            date=args.date,
            module=args.module,
        )
        for row in result["rows"]:
            file_val = row.get("File", "").strip().strip("`")
            if file_val:
                target = (module_root / file_val).resolve()
                if not target.exists():
                    missing_files.append(file_val)
        if missing_files:
            result["state"] = "stale"
            result["reason"] = "story_files_missing"
            result["missing_files"] = missing_files

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)

    if result["state"] == "current":
        return 0
    print(
        f"USERSTORIES_INDEX_FAIL: state={result['state']} reason={result.get('reason', '')}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
