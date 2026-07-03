#!/usr/bin/env python3
"""Reverse index validation: checks index exists, documented_commit matches baseline, all indexed files exist."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from reverse_guardrail_common import (
    block,
    check_fail,
    check_pass,
    emit_result,
    git_commit_exists,
    ok,
    with_block_code,
)

# Minimal metadata fields expected in a reverse index frontmatter table.
REQUIRED_INDEX_METADATA = {"documented_commit", "generated_at", "index_type"}


def parse_reverse_index(text: str) -> dict:
    """Extract metadata and file list from a reverse index markdown file."""
    lines = text.splitlines()
    metadata: dict[str, str] = {}
    indexed_files: list[str] = []

    # Parse frontmatter-style metadata table (| Field | Value |)
    for i, line in enumerate(lines):
        if "| Field | Value |" in line or "| field | value |" in line.lower():
            for j in range(i + 2, len(lines)):
                row = lines[j].strip()
                if not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.strip("|").split("|")]
                if len(cells) >= 2:
                    metadata[cells[0].lower().replace(" ", "_")] = cells[1].strip("`").strip()
            break

    if not metadata:
        for line in lines:
            if ":" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip().strip("`")
            if key in REQUIRED_INDEX_METADATA or key in {"stale_status", "validated_at", "validated_by", "source_artifact"}:
                metadata[key] = value

    # Collect indexed file paths (lines starting with - or * followed by a path)
    for line in lines:
        m = re.match(r"^[-*]\s+`?([^\s`]+\.[a-zA-Z0-9]+)`?\s*", line)
        if m:
            indexed_files.append(m.group(1))
            continue
        if line.startswith("|"):
            cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
            if len(cells) >= 2 and "/" in cells[1] and "." in cells[1]:
                indexed_files.append(cells[1])

    return {"metadata": metadata, "indexed_files": indexed_files}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a reverse-mode index file.")
    parser.add_argument("--index-path", required=True, help="Path to reverse-index.md")
    parser.add_argument("--project-path", required=True, help="Project root (repo root)")
    args = parser.parse_args()

    index_path = Path(args.index_path).resolve()
    repo = Path(args.project_path).resolve()
    checks: list[dict] = []

    # Check 1: index file exists
    if not index_path.exists():
        checks.append(check_fail("index_exists", str(index_path)))
        result = with_block_code(block(checks, f"reverse index not found: {index_path}"), "reverse_index_missing")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("index_exists", str(index_path)))

    # Parse index
    text = index_path.read_text(encoding="utf-8")
    parsed = parse_reverse_index(text)
    metadata = parsed["metadata"]
    indexed_files = parsed["indexed_files"]

    # Check 2: required metadata fields present
    missing_meta = [f for f in REQUIRED_INDEX_METADATA if f not in metadata or not metadata[f]]
    if missing_meta:
        checks.append(check_fail("metadata_complete", f"missing: {', '.join(missing_meta)}"))
        result = with_block_code(block(
            checks,
            f"reverse index missing metadata fields: {', '.join(missing_meta)}",
            documented_commit="",
            checks_detail={"missing_metadata": missing_meta},
        ), "reverse_index_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1
    documented_commit = metadata["documented_commit"]
    checks.append(check_pass("metadata_complete", f"commit={documented_commit}"))

    # Check 3: documented_commit exists in git history
    if git_commit_exists(repo, documented_commit):
        checks.append(check_pass("commit_in_history", documented_commit))
    else:
        checks.append(check_fail("commit_in_history", f"commit not found: {documented_commit}"))
        result = with_block_code(block(
            checks,
            f"documented_commit {documented_commit} not found in git history. Index is stale.",
            status="stale",
            documented_commit=documented_commit,
        ), "reverse_index_stale")
        emit_result(result, stderr_summary=result["message"])
        return 1

    # Check 4: all indexed files exist on disk
    missing_files: list[str] = []
    for rel in indexed_files:
        candidate = repo / rel
        if not candidate.exists():
            missing_files.append(rel)

    if missing_files:
        checks.append(check_fail("indexed_files_exist", f"{len(missing_files)} missing: {missing_files[:5]}"))
        result = with_block_code(block(
            checks,
            f"{len(missing_files)} indexed file(s) missing from disk. Index may be stale.",
            status="missing",
            documented_commit=documented_commit,
            missing_files=missing_files,
        ), "reverse_index_file_missing")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("indexed_files_exist", f"{len(indexed_files)} files verified"))

    result = ok(
        checks,
        f"reverse index valid: commit={documented_commit} files={len(indexed_files)}",
        status="ok",
        documented_commit=documented_commit,
        indexed_file_count=len(indexed_files),
    )
    emit_result(result, stderr_summary=result["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
