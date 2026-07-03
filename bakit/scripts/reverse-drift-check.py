#!/usr/bin/env python3
"""Reverse drift check: verify documented_commit still exists in git history
and that locked files have not changed since the baseline was recorded."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reverse_guardrail_common import (
    block,
    check_fail,
    check_pass,
    emit_result,
    git_commit_exists,
    git_file_hash_at_commit,
    load_json,
    normalize_baseline_lock,
    ok,
    sha256_file,
    validate_baseline_lock,
    with_block_code,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check for drift between baseline lock and current repo state.")
    parser.add_argument("--baseline-lock", required=True, help="Path to reverse-baseline-lock.json")
    parser.add_argument("--project-path", required=True, help="Repo root path")
    args = parser.parse_args()

    lock_path = Path(args.baseline_lock).resolve()
    repo = Path(args.project_path).resolve()
    checks: list[dict] = []

    # Check 1: lock file exists
    if not lock_path.exists():
        checks.append(check_fail("baseline_lock_exists", str(lock_path)))
        result = with_block_code(
            block(checks, f"baseline lock not found: {lock_path}", status="missing", documented_commit=""),
            "baseline_lock_missing",
        )
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("baseline_lock_exists", str(lock_path)))

    # Parse and validate lock
    try:
        lock_data = normalize_baseline_lock(load_json(lock_path))
    except Exception as exc:
        checks.append(check_fail("baseline_lock_parseable", str(exc)))
        result = with_block_code(
            block(checks, f"baseline lock JSON parse error: {exc}", status="missing", documented_commit=""),
            "baseline_lock_invalid",
        )
        emit_result(result, stderr_summary=result["message"])
        return 1

    errors = validate_baseline_lock(lock_data)
    if errors:
        checks.append(check_fail("baseline_lock_valid", "; ".join(errors)))
        result = with_block_code(block(
            checks,
            f"baseline lock invalid: {'; '.join(errors)}",
            status="missing",
            documented_commit=lock_data.get("documented_commit", ""),
            validation_errors=errors,
        ), "baseline_lock_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("baseline_lock_valid", "required fields present"))

    documented_commit = lock_data["documented_commit"]

    # Check 2: documented_commit exists in git history
    if not git_commit_exists(repo, documented_commit):
        checks.append(check_fail("commit_in_history", f"commit not found: {documented_commit}"))
        result = with_block_code(block(
            checks,
            f"documented_commit {documented_commit} no longer exists in git history. Baseline is stale.",
            status="stale",
            documented_commit=documented_commit,
            drifted_files=[],
        ), "reverse_drift_detected")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("commit_in_history", documented_commit))

    # Check 3: locked files have not changed since baseline commit
    locked_files: list[str] = lock_data.get("locked_files", [])
    if not locked_files:
        checks.append(check_pass("locked_files_drift", "no locked files to check"))
        result = ok(
            checks,
            f"drift check passed: commit={documented_commit} (no locked files)",
            status="current",
            documented_commit=documented_commit,
            drifted_files=[],
        )
        emit_result(result, stderr_summary=result["message"])
        return 0

    drifted_files: list[dict] = []
    for rel_path in locked_files:
        current_path = repo / rel_path
        if not current_path.exists():
            drifted_files.append({"file": rel_path, "reason": "deleted_since_lock"})
            continue

        current_hash = sha256_file(current_path)
        baseline_hash = git_file_hash_at_commit(repo, documented_commit, rel_path)

        if baseline_hash is None:
            # File wasn't tracked at that commit — treat as new/untracked, not drift
            continue

        if current_hash != baseline_hash:
            drifted_files.append({
                "file": rel_path,
                "reason": "content_changed",
                "baseline_hash": baseline_hash[:12],
                "current_hash": current_hash[:12],
            })

    if drifted_files:
        checks.append(check_fail(
            "locked_files_drift",
            f"{len(drifted_files)} file(s) drifted since baseline commit",
        ))
        result = with_block_code(block(
            checks,
            f"baseline drift detected: {len(drifted_files)} file(s) changed since {documented_commit}. "
            "Re-run baseline scan to refresh.",
            status="stale",
            documented_commit=documented_commit,
            drifted_files=drifted_files,
        ), "reverse_drift_detected")
        emit_result(result, stderr_summary=result["message"])
        return 1

    checks.append(check_pass("locked_files_drift", f"{len(locked_files)} file(s) unchanged"))

    result = ok(
        checks,
        f"drift check passed: commit={documented_commit} files={len(locked_files)} unchanged",
        status="current",
        documented_commit=documented_commit,
        drifted_files=[],
    )
    emit_result(result, stderr_summary=result["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
