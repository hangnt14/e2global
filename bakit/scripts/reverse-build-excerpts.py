#!/usr/bin/env python3
"""Reverse excerpt builder: extract focused excerpts from index-listed files only.

v1 source-only enforcement: blocks subprocess calls, HTTP requests to localhost,
and any live endpoint verification patterns found in scanned source files.
"""

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
    detect_live_probes,
    emit_result,
    ok,
    with_block_code,
)

SECTION_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def parse_index_file_list(index_text: str) -> list[str]:
    """Extract file paths listed in the reverse index."""
    files: list[str] = []
    for line in index_text.splitlines():
        m = re.match(r"^[-*]\s+`?([^\s`]+\.[a-zA-Z0-9]+)`?\s*", line)
        if m:
            files.append(m.group(1))
            continue
        if line.startswith("|"):
            cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
            if len(cells) >= 2 and "/" in cells[1] and "." in cells[1]:
                files.append(cells[1])
    return files


def extract_focused_excerpt(text: str, focus_area: str, max_chars: int = 4000) -> str:
    """Extract the section of text most relevant to focus_area by heading match."""
    lines = text.splitlines()
    focus_lower = focus_area.lower()

    # Find best matching heading
    best_start: int | None = None
    best_level = 7
    for i, line in enumerate(lines):
        m = SECTION_RE.match(line.strip())
        if m and focus_lower in m.group(2).lower():
            level = len(m.group(1))
            if level < best_level:
                best_level = level
                best_start = i

    if best_start is None:
        # Fallback: keyword scan — return surrounding context
        for i, line in enumerate(lines):
            if focus_lower in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 30)
                return "\n".join(lines[start:end])
        return ""

    # Extract section until next heading of same or higher level
    end = len(lines)
    for j in range(best_start + 1, len(lines)):
        m = SECTION_RE.match(lines[j].strip())
        if m and len(m.group(1)) <= best_level:
            end = j
            break

    excerpt = "\n".join(lines[best_start:end]).strip()
    return excerpt[:max_chars]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build focused excerpts from reverse index files.")
    parser.add_argument("--index-path", required=True, help="Path to reverse-index.md")
    parser.add_argument("--focus-areas", required=True, help="Comma-separated focus area keywords")
    parser.add_argument("--output-dir", required=True, help="Directory to write excerpt files")
    parser.add_argument("--project-path", required=True, help="Repo root for resolving relative file paths")
    args = parser.parse_args()

    index_path = Path(args.index_path).resolve()
    output_dir = Path(args.output_dir).resolve()
    repo = Path(args.project_path).resolve()
    focus_areas = [f.strip() for f in args.focus_areas.split(",") if f.strip()]
    checks: list[dict] = []

    # Check 1: index exists
    if not index_path.exists():
        checks.append(check_fail("index_exists", str(index_path)))
        result = with_block_code(block(checks, f"reverse index not found: {index_path}"), "reverse_index_missing")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("index_exists", str(index_path)))

    index_text = index_path.read_text(encoding="utf-8")
    indexed_files = parse_index_file_list(index_text)

    if not indexed_files:
        checks.append(check_fail("index_has_files", "no files listed in index"))
        result = with_block_code(block(checks, "reverse index contains no file entries"), "reverse_index_invalid")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("index_has_files", f"{len(indexed_files)} files in index"))

    # Check 2: focus areas provided
    if not focus_areas:
        checks.append(check_fail("focus_areas_provided", "empty"))
        result = with_block_code(block(checks, "no focus areas specified"), "focus_selection_required")
        emit_result(result, stderr_summary=result["message"])
        return 1
    checks.append(check_pass("focus_areas_provided", ", ".join(focus_areas)))

    output_dir.mkdir(parents=True, exist_ok=True)
    excerpts_built: list[dict] = []
    live_probe_violations: list[dict] = []

    for rel_path in indexed_files:
        file_path = repo / rel_path
        if not file_path.exists():
            checks.append(check_fail("file_readable", f"missing: {rel_path}"))
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            checks.append(check_fail("file_readable", f"{rel_path}: {exc}"))
            continue

        # v1 source-only enforcement: detect live probes in scanned files
        probe_hits = detect_live_probes(content)
        if probe_hits:
            live_probe_violations.append({"file": rel_path, "patterns": probe_hits})

        for focus in focus_areas:
            excerpt = extract_focused_excerpt(content, focus)
            if not excerpt:
                continue
            safe_focus = re.sub(r"[^a-zA-Z0-9_-]", "-", focus)
            safe_file = re.sub(r"[/\\]", "__", rel_path)
            out_name = f"excerpt__{safe_file}__{safe_focus}.md"
            out_path = output_dir / out_name
            out_path.write_text(
                f"# Reverse Excerpt\n\n"
                f"- source_file: `{rel_path}`\n"
                f"- focus_area: `{focus}`\n\n"
                f"{excerpt}\n",
                encoding="utf-8",
            )
            excerpts_built.append({"source_file": rel_path, "focus_area": focus, "output": out_name})

    # Fail closed on live probe violations
    if live_probe_violations:
        checks.append(check_fail(
            "source_only_enforcement",
            f"{len(live_probe_violations)} file(s) contain live-probe patterns",
        ))
        result = with_block_code(block(
            checks,
            "READ_ESCALATION: reverse-build-excerpts detected live-probe patterns in source files. "
            "v1 reverse mode is source-only. Remove or isolate runtime calls before proceeding.",
            live_probe_violations=live_probe_violations,
            excerpts_built=len(excerpts_built),
            focus_areas=focus_areas,
        ), "reverse_source_only_violation")
        emit_result(result, stderr_summary=result["message"])
        return 1

    checks.append(check_pass("source_only_enforcement", "no live-probe patterns detected"))

    # Write manifest
    manifest = {
        "status": "ok",
        "excerpts_built": len(excerpts_built),
        "focus_areas": focus_areas,
        "output_dir": str(output_dir),
        "excerpts": excerpts_built,
    }
    manifest_path = output_dir / "reverse-excerpts-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = ok(
        checks,
        f"excerpts built: {len(excerpts_built)} for {len(focus_areas)} focus area(s)",
        excerpts_built=len(excerpts_built),
        focus_areas=focus_areas,
        output_dir=str(output_dir),
    )
    emit_result(result, stderr_summary=result["message"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
