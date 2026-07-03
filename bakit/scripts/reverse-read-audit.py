#!/usr/bin/env python3
"""Reverse read audit: verify all reads in a manifest are within allowlisted scope.
Flags out-of-scope reads as READ_ESCALATION entries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from reverse_guardrail_common import (
    block,
    check_fail,
    check_pass,
    emit_result,
    ok,
    with_block_code,
)

# NDJSON record fields expected in the read manifest
REQUIRED_MANIFEST_FIELDS = {"path", "timestamp"}


def load_ndjson(path: Path) -> list[dict]:
    """Parse newline-delimited JSON manifest."""
    records: list[dict] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {i}: {exc}") from exc
    return records


def load_allowlist(path: Path) -> list[str]:
    """Load allowlist from a JSON array file or plain text (one path per line)."""
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("["):
        return json.loads(text)
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def path_is_allowed(read_path: str, allowlist: list[str]) -> bool:
    """Return True if read_path matches any allowlist entry (exact or prefix)."""
    norm = Path(read_path).as_posix()
    for entry in allowlist:
        entry_norm = Path(entry).as_posix().rstrip("/")
        if norm == entry_norm:
            return True
        if norm.startswith(entry_norm + "/"):
            return True
        # Glob-style wildcard: entry ends with /*
        if entry_norm.endswith("/*"):
            prefix = entry_norm[:-2]
            if norm.startswith(prefix + "/") and "/" not in norm[len(prefix) + 1:]:
                return True
        # Recursive wildcard: entry ends with /**
        if entry_norm.endswith("/**"):
            prefix = entry_norm[:-3]
            if norm.startswith(prefix + "/"):
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit reverse-mode read manifest against allowlist.")
    parser.add_argument("--read-manifest", required=True, help="Path to reverse-read-manifest.ndjson")
    parser.add_argument("--allowlist", default="", help="Path to allowlist file (JSON array or plain text)")
    args = parser.parse_args()

    manifest_path = Path(args.read_manifest).resolve()
    checks: list[dict] = []

    # Check 1: manifest exists
    if not manifest_path.exists():
        checks.append(check_fail("manifest_exists", str(manifest_path)))
        result = with_block_code(block(checks, f"read manifest not found: {manifest_path}"), "reverse_manifest_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("manifest_exists", str(manifest_path)))

    # Parse manifest
    try:
        records = load_ndjson(manifest_path)
    except ValueError as exc:
        checks.append(check_fail("manifest_parseable", str(exc)))
        result = with_block_code(block(checks, f"read manifest parse error: {exc}"), "reverse_manifest_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("manifest_parseable", f"{len(records)} records"))

    # Check 2: records have required fields
    malformed: list[int] = []
    for i, rec in enumerate(records):
        missing = [f for f in REQUIRED_MANIFEST_FIELDS if f not in rec]
        if missing:
            malformed.append(i)
    if malformed:
        checks.append(check_fail("manifest_record_format", f"{len(malformed)} malformed record(s) at indices {malformed[:5]}"))
    else:
        checks.append(check_pass("manifest_record_format", "all records have required fields"))

    # Load allowlist (optional — if not provided, all reads are flagged as unverified)
    allowlist: list[str] = []
    if args.allowlist:
        allowlist_path = Path(args.allowlist).resolve()
        if not allowlist_path.exists():
            checks.append(check_fail("allowlist_exists", str(allowlist_path)))
            result = with_block_code(block(checks, f"allowlist file not found: {allowlist_path}"), "reverse_allowlist_invalid")
            emit_result(result, stderr_summary=result["message"])
            return 1
        try:
            allowlist = load_allowlist(allowlist_path)
        except Exception as exc:
            checks.append(check_fail("allowlist_parseable", str(exc)))
            result = with_block_code(block(checks, f"allowlist parse error: {exc}"), "reverse_allowlist_invalid")
            emit_result(result, stderr_summary=result["message"])
            return 1
        checks.append(check_pass("allowlist_loaded", f"{len(allowlist)} entries"))

    # Check 3: classify reads
    out_of_scope: list[dict] = []
    in_scope_count = 0

    for rec in records:
        read_path = rec.get("path", "")
        if not read_path:
            continue
        if not allowlist:
            # No allowlist supplied — all reads are unverified, emit as escalation
            out_of_scope.append({
                "path": read_path,
                "reason": "no_allowlist_supplied",
                "timestamp": rec.get("timestamp", ""),
            })
            continue
        if path_is_allowed(read_path, allowlist):
            in_scope_count += 1
        else:
            out_of_scope.append({
                "path": read_path,
                "reason": "out_of_scope",
                "timestamp": rec.get("timestamp", ""),
            })

    total_reads = len([r for r in records if r.get("path")])

    if out_of_scope:
        escalation_lines = "\n".join(
            f"  READ_ESCALATION: reverse read {e['path']} due to {e['reason']}"
            for e in out_of_scope[:10]
        )
        checks.append(check_fail(
            "read_scope",
            f"{len(out_of_scope)} out-of-scope read(s) detected",
        ))
        result = {
            "status": "escalation",
            "checks": checks,
            "block_code": "REVERSE_READ_SCOPE_ESCALATION",
            "message": (
                f"READ_ESCALATION: {len(out_of_scope)} read(s) outside allowlisted scope. "
                "Review and add to allowlist or restrict read scope."
            ),
            "out_of_scope": out_of_scope,
            "in_scope": in_scope_count,
            "total_reads": total_reads,
            "escalation_entries": [
                f"READ_ESCALATION: reverse read {e['path']} due to {e['reason']}"
                for e in out_of_scope
            ],
        }
        emit_result(result, stderr_summary=result["message"])
        return 1

    checks.append(check_pass("read_scope", f"all {total_reads} reads within allowlisted scope"))

    result = ok(
        checks,
        f"read audit clean: {total_reads} reads, all in scope",
        status="clean",
        out_of_scope=[],
        in_scope=in_scope_count,
        total_reads=total_reads,
    )
    emit_result(result, stderr_summary=result["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
