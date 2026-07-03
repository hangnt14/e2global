#!/usr/bin/env python3
"""Build compact excerpt files from current guardrail indexes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from guardrail_common import (
    INDEX_TABLE_HEADERS,
    candidate_index_headings,
    classify_index_state,
    extract_sections_by_headings,
    load_contract,
    parse_index_file,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--index-key", choices=sorted(INDEX_TABLE_HEADERS), required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", default="")
    parser.add_argument("--feature", default="")
    parser.add_argument("--trace-id", default="")
    parser.add_argument("--heading", default="")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    contract = load_contract(repo)
    index_state = classify_index_state(
        repo=repo,
        contract=contract,
        index_key=args.index_key,
        slug=args.slug,
        date=args.date,
        module=args.module,
        feature=args.feature,
        trace_id=args.trace_id,
        heading=args.heading,
        require_extractable=True,
    )
    if index_state["state"] != "current":
        raise SystemExit(f"Cannot build excerpts from non-current index: {args.index_key} state={index_state['state']}")

    index_path = repo / index_state["path"]
    parsed = parse_index_file(index_path)
    headings = candidate_index_headings(
        index_key=args.index_key,
        rows=parsed["rows"],
        module=args.module,
        feature=args.feature,
        heading=args.heading,
        trace_id=args.trace_id,
    )
    if not headings:
        raise SystemExit("No headings matched the requested excerpt scope")

    source_path = repo / index_state["source_artifact"]
    sections = extract_sections_by_headings(source_path.read_text(encoding="utf-8"), headings)
    if not sections:
        raise SystemExit("No source sections matched the requested headings")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    excerpt_path = output_dir / f"{args.index_key.replace('_index', '')}-excerpt.md"
    manifest_path = output_dir / f"{args.index_key.replace('_index', '')}-excerpt-manifest.json"

    excerpt_lines = [
        f"# Guardrail Excerpt - {args.index_key}",
        "",
        f"- source_artifact: `{index_state['source_artifact']}`",
        f"- headings: {', '.join(headings)}",
        "",
    ]
    for section in sections:
        excerpt_lines.append(section["content"].rstrip())
        excerpt_lines.append("")
    excerpt_text = "\n".join(excerpt_lines).rstrip() + "\n"
    excerpt_path.write_text(excerpt_text, encoding="utf-8")

    manifest = {
        "status": "ok",
        "index_key": args.index_key,
        "index_path": index_state["path"],
        "source_artifact": index_state["source_artifact"],
        "excerpt_path": excerpt_path.as_posix(),
        "headings": headings,
        "section_count": len(sections),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
