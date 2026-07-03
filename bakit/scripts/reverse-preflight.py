#!/usr/bin/env python3
"""Reverse-mode preflight: verify 00_reverse dir, baseline lock, and focus selection."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reverse_guardrail_common import (
    block,
    check_fail,
    check_pass,
    emit_result,
    load_contract,
    normalize_baseline_lock,
    ok,
    render_path,
    validate_baseline_lock,
    with_block_code,
    load_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reverse-mode preflight checks.")
    parser.add_argument("--repo", default=".", help="Repo root path")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    try:
        contract = load_contract(repo)
    except Exception as exc:
        checks = [check_fail("contract_loadable", str(exc))]
        result = with_block_code(
            block(checks, f"reverse contract missing or unreadable under {repo}: {exc}"),
            "reverse_contract_invalid",
        )
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks: list[dict] = []

    # Check 1: 00_reverse directory exists
    reverse_root_rel = render_path(contract["paths"]["reverse_root"], slug=args.slug, date=args.date)
    reverse_root = repo / reverse_root_rel
    if reverse_root.is_dir():
        checks.append(check_pass("reverse_root_exists", reverse_root_rel))
    else:
        checks.append(check_fail("reverse_root_exists", f"missing: {reverse_root_rel}"))
        result = with_block_code(block(
            checks,
            f"00_reverse directory missing at {reverse_root_rel}. Run: ba-start reverse --slug {args.slug}",
            refresh_command=f"ba-start reverse --slug {args.slug}",
        ), "reverse_root_missing")
        emit_result(result, stderr_summary=result["message"])
        return 1

    # Check 2: baseline_lock.md present
    lock_rel = render_path(contract["paths"]["reverse_baseline_lock"], slug=args.slug, date=args.date)
    lock_path = repo / lock_rel
    if lock_path.exists():
        checks.append(check_pass("baseline_lock_present", lock_rel))
    else:
        checks.append(check_fail("baseline_lock_present", f"missing: {lock_rel}"))
        result = with_block_code(block(
            checks,
            f"baseline_lock missing at {lock_rel}. Run: ba-start reverse --slug {args.slug}",
            refresh_command=f"ba-start reverse --slug {args.slug}",
        ), "baseline_lock_missing")
        emit_result(result, stderr_summary=result["message"])
        return 1

    # Check 3: baseline_lock valid (required fields + format)
    try:
        lock_data = normalize_baseline_lock(load_json(lock_path))
    except Exception as exc:
        checks.append(check_fail("baseline_lock_valid", f"parse error: {exc}"))
        result = with_block_code(block(checks, f"baseline_lock is not valid JSON: {exc}"), "baseline_lock_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1

    errors = validate_baseline_lock(lock_data)
    if errors:
        checks.append(check_fail("baseline_lock_valid", "; ".join(errors)))
        result = with_block_code(block(
            checks,
            f"baseline_lock invalid: {'; '.join(errors)}",
            validation_errors=errors,
        ), "baseline_lock_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("baseline_lock_valid", f"commit={lock_data['documented_commit']}"))

    # Check 4: focus_selection made (non-empty list or string)
    focus = lock_data.get("focus_selection")
    if focus and (isinstance(focus, list) and len(focus) > 0 or isinstance(focus, str) and focus.strip()):
        focus_summary = focus if isinstance(focus, str) else ", ".join(focus)
        checks.append(check_pass("focus_selection_made", focus_summary))
    else:
        checks.append(check_fail("focus_selection_made", "focus_selection is empty or missing"))
        result = with_block_code(block(
            checks,
            "focus_selection not made. Update baseline_lock with at least one focus area before proceeding.",
        ), "focus_selection_required")
        emit_result(result, stderr_summary=result["message"])
        return 1

    result = ok(
        checks,
        f"preflight passed: slug={args.slug} date={args.date} commit={lock_data['documented_commit']}",
        documented_commit=lock_data["documented_commit"],
        scan_timestamp=lock_data["scan_timestamp"],
        focus_selection=focus,
    )
    emit_result(result, stderr_summary=result["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
