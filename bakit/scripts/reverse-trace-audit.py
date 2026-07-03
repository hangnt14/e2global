#!/usr/bin/env python3
"""Reverse trace audit: verify every claim in promoted artifacts has a trace_id in the evidence ledger."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reverse_guardrail_common import (
    block,
    check_fail,
    check_pass,
    emit_result,
    extract_trace_ids,
    ok,
    parse_evidence_ledger,
    REQUIRED_TRACE_FIELDS,
    with_block_code,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit trace coverage between evidence ledger and promoted artifacts.")
    parser.add_argument("--evidence-ledger", required=True, help="Path to reverse-evidence-ledger.md")
    parser.add_argument("--promoted-artifacts", required=True, nargs="+", help="Paths to promoted artifact files")
    args = parser.parse_args()

    ledger_path = Path(args.evidence_ledger).resolve()
    checks: list[dict] = []

    # Check 1: ledger exists
    if not ledger_path.exists():
        checks.append(check_fail("ledger_exists", str(ledger_path)))
        result = with_block_code(block(checks, f"evidence ledger not found: {ledger_path}"), "reverse_trace_ledger_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("ledger_exists", str(ledger_path)))

    # Parse ledger records
    records = parse_evidence_ledger(ledger_path)
    ledger_trace_ids: set[str] = {r["trace_id"] for r in records if "trace_id" in r}

    # Check 2: ledger has records
    if not records:
        checks.append(check_fail("ledger_has_records", "no trace records found"))
        result = with_block_code(block(checks, "evidence ledger contains no trace records"), "reverse_trace_ledger_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("ledger_has_records", f"{len(records)} records"))

    # Check 3: each record has required fields
    incomplete_records: list[str] = []
    for rec in records:
        missing = [f for f in REQUIRED_TRACE_FIELDS if f not in rec or not rec[f]]
        if missing:
            incomplete_records.append(f"{rec.get('trace_id', '?')}: missing {', '.join(missing)}")
    if incomplete_records:
        checks.append(check_fail("ledger_record_completeness", f"{len(incomplete_records)} incomplete records"))
    else:
        checks.append(check_pass("ledger_record_completeness", "all records have required fields"))

    # Collect trace IDs referenced in promoted artifacts
    artifact_trace_ids: set[str] = set()
    missing_artifacts: list[str] = []
    for artifact_path_str in args.promoted_artifacts:
        artifact_path = Path(artifact_path_str).resolve()
        if not artifact_path.exists():
            missing_artifacts.append(str(artifact_path))
            continue
        text = artifact_path.read_text(encoding="utf-8")
        artifact_trace_ids.update(extract_trace_ids(text))

    if missing_artifacts:
        checks.append(check_fail("promoted_artifacts_exist", f"missing: {missing_artifacts}"))
        result = with_block_code(block(
            checks,
            f"{len(missing_artifacts)} promoted artifact(s) not found on disk",
            missing_artifacts=missing_artifacts,
        ), "reverse_trace_ledger_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("promoted_artifacts_exist", f"{len(args.promoted_artifacts)} artifact(s) readable"))

    # Check 4: every trace ID in promoted artifacts exists in ledger
    missing_traces = sorted(artifact_trace_ids - ledger_trace_ids)
    total = len(artifact_trace_ids)
    covered = total - len(missing_traces)
    coverage_pct = round(100 * covered / total, 1) if total > 0 else 100.0

    if missing_traces:
        checks.append(check_fail(
            "trace_coverage",
            f"{len(missing_traces)} trace ID(s) in artifacts not found in ledger",
        ))
        result = with_block_code(block(
            checks,
            f"trace coverage incomplete: {coverage_pct}% ({covered}/{total}). "
            f"Missing traces must be added to evidence ledger before promotion.",
            status="incomplete",
            coverage=f"{coverage_pct}%",
            covered=covered,
            total=total,
            missing_traces=missing_traces,
            incomplete_records=incomplete_records,
        ), "reverse_trace_incomplete")
        emit_result(result, stderr_summary=result["message"])
        return 1

    if incomplete_records:
        result = with_block_code(block(
            checks,
            f"evidence ledger has {len(incomplete_records)} incomplete record(s). "
            "Complete all required trace fields before promotion.",
            status="incomplete",
            coverage=f"{coverage_pct}%",
            covered=covered,
            total=total,
            missing_traces=[],
            incomplete_records=incomplete_records,
        ), "reverse_trace_ledger_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1

    checks.append(check_pass("trace_coverage", f"{coverage_pct}% ({covered}/{total})"))

    result = ok(
        checks,
        f"trace audit passed: {coverage_pct}% coverage ({covered}/{total} trace IDs)",
        status="ok",
        coverage=f"{coverage_pct}%",
        covered=covered,
        total=total,
        missing_traces=[],
        incomplete_records=incomplete_records,
    )
    emit_result(result, stderr_summary=result["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
