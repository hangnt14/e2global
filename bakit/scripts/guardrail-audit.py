#!/usr/bin/env python3
"""Audit actual runtime reads against a guardrail preflight manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from guardrail_common import load_json_input, normalize_paths


def load_reads_manifest(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    data = load_json_input(path)
    if isinstance(data, list):
        return normalize_paths([str(item) for item in data]), []
    if isinstance(data, dict):
        reads = normalize_paths([str(item) for item in data.get("reads", [])])
        escalations = [
            {
                "path": Path(str(item.get("path", ""))).as_posix(),
                "reason": str(item.get("reason", "")).strip(),
            }
            for item in data.get("escalations", [])
        ]
        return reads, escalations
    raise SystemExit("Unsupported reads manifest format")


def is_allowed(path: str, allowed: list[str]) -> bool:
    return any(path == item or path.startswith(item.rstrip("/") + "/") for item in allowed)


def has_escalation(path: str, escalations: list[dict[str, str]]) -> bool:
    return any(path == item["path"] and item["reason"] for item in escalations)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", required=True)
    parser.add_argument("--reads-manifest", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    preflight = load_json_input(Path(args.preflight))
    reads, escalations = load_reads_manifest(Path(args.reads_manifest))

    allow_reads = normalize_paths([str(item) for item in preflight.get("allow_reads", [])])
    deny_reads = normalize_paths([str(item) for item in preflight.get("deny_reads", [])])

    violations: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    for path in reads:
        if is_allowed(path, allow_reads):
            continue
        if path in deny_reads:
            if has_escalation(path, escalations):
                warnings.append(
                    {
                        "type": "escalated_read",
                        "path": path,
                        "reason": "read_allowed_via_escalation",
                    }
                )
                continue
            violations.append(
                {
                    "type": "disallowed_read",
                    "path": path,
                    "reason": "path_denied_by_guardrail",
                }
            )
            continue
        if has_escalation(path, escalations):
            warnings.append(
                {
                    "type": "escalated_unknown_read",
                    "path": path,
                    "reason": "path_not_allowlisted_but_escalated",
                }
            )
            continue
        violations.append(
            {
                "type": "unallowlisted_read",
                "path": path,
                "reason": "path_not_present_in_allowlist",
            }
        )

    status = "pass"
    if violations:
        status = "fail"
    elif warnings:
        status = "warn"

    result = {
        "status": status,
        "command": preflight.get("command", ""),
        "guardrail_mode": preflight.get("guardrail_mode", ""),
        "actual_reads": reads,
        "violations": violations,
        "warnings": warnings,
        "message": "",
    }
    if status == "fail" and violations:
        first = violations[0]
        result["message"] = (
            f"GUARDRAIL_AUDIT_FAIL: cmd={result['command']} violation={first['type']} path={first['path']}"
        )
    elif status == "warn" and warnings:
        first = warnings[0]
        result["message"] = (
            f"GUARDRAIL_AUDIT_WARN: cmd={result['command']} warning={first['type']} path={first['path']}"
        )
    else:
        result["message"] = f"GUARDRAIL_AUDIT_PASS: cmd={result['command']}"

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
