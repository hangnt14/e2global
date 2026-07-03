#!/usr/bin/env python3
"""Validate shared/traceability.md coverage for a project."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from guardrail_common import load_contract, render_path

ID_PATTERN = re.compile(r"\b(?:US|UC|SCR|FR)-[A-Za-z0-9-]+\b")
COVERAGE_GAP_RE = re.compile(r"^\|\s*(story_without_uc|uc_without_screen|screen_without_story)\s*\|", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--output", help="Write JSON result to this path")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    contract = load_contract(repo)

    traceability_rel = render_path(
        contract["paths"]["shared_traceability"],
        slug=args.slug,
        date=args.date,
        module="",
    )
    traceability_path = repo / traceability_rel

    result: dict = {
        "status": "pass",
        "path": traceability_rel,
        "issues": [],
        "coverage_gaps": [],
        "message": "",
    }

    if not traceability_path.exists():
        result["status"] = "warn"
        result["message"] = f"SHARED_TRACEABILITY_WARN: file missing at {traceability_rel}"
        output = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(output)
        return 0  # warn only — traceability is generated, not a hard block

    text = traceability_path.read_text(encoding="utf-8")

    # Check for coverage gaps section
    gaps: list[str] = []
    for line in text.splitlines():
        m = COVERAGE_GAP_RE.match(line)
        if m:
            gaps.append(line.strip())

    if gaps:
        result["coverage_gaps"] = gaps
        result["issues"].append({
            "severity": "warn",
            "code": "traceability_coverage_gaps",
            "count": len(gaps),
            "message": f"{len(gaps)} coverage gap(s) found in shared/traceability.md",
        })

    # Check that at least some IDs are present
    ids_found = ID_PATTERN.findall(text)
    if not ids_found:
        result["issues"].append({
            "severity": "warn",
            "code": "traceability_no_ids",
            "message": "No traceable IDs (US/UC/SCR/FR) found in shared/traceability.md",
        })

    errors = [i for i in result["issues"] if i["severity"] == "error"]
    result["status"] = "fail" if errors else ("warn" if result["issues"] else "pass")
    result["message"] = (
        f"SHARED_TRACEABILITY_FAIL: errors={len(errors)}"
        if errors
        else (
            f"SHARED_TRACEABILITY_WARN: gaps={len(gaps)}"
            if gaps
            else f"SHARED_TRACEABILITY_PASS: ids={len(set(ids_found))}"
        )
    )

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
