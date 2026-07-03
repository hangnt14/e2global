#!/usr/bin/env python3
"""Estimate BA-kit runtime read context size for a command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

COMMAND_SCOPES = {
    "intake": ["source_summary", "source_chunk_index", "project_memory"],
    "options": ["intake", "plan", "source_chunk_index"],
    "backbone": ["intake", "plan", "options_index", "options_comparison"],
    "frd": ["backbone_index", "plan", "project_memory"],
    "stories": ["backbone_index", "plan", "frd", "project_memory"],
    "srs": ["backbone_index", "userstories_index", "frd", "project_memory"],
    "impact": ["intake", "backbone_index", "backbone", "userstories_index", "usecases_index", "ascii_screen_index", "srs_compile_receipt", "project_memory"],
    "wireframes": ["ascii_screen_index", "design_doc", "srs_compile_receipt", "project_memory"],
    "package": ["backbone_index", "userstories_index", "usecases_index", "ascii_screen_index", "srs_compile_receipt", "memory_index"],
    "status": ["project_home", "project_memory", "memory_index"],
}

LANE_SCOPES = {
    "figma-make": [
        "screen_field_contract",
        "tool_lane_state",
        "make_guidelines",
        "make_prompt_pack",
        "make_uc_prompt",
        "make_uc_change_log",
        "prototype_conformance_checklist",
        "prototype_conformance_report",
        "figma_make_shared_rules",
        "figma_make_shared_prompt_skeleton",
        "figma_make_shared_component_contracts",
    ]
}


def render_path(template: str, *, slug: str, date: str, module: str) -> str:
    return (
        template.replace("{slug}", slug)
        .replace("{date}", date)
        .replace("{module_slug}", module)
        .replace("{usecase_slug}", "*")
        .replace("{group}", "*")
        .replace("{option}", "*")
    )


def size_for(root: Path, rel_pattern: str) -> int:
    if "*" in rel_pattern:
        return sum(path.stat().st_size for path in root.glob(rel_pattern) if path.is_file())
    path = root / rel_pattern
    return path.stat().st_size if path.is_file() else 0

def detect_lane(root: Path, lane_state_rel: str) -> str:
    path = root / lane_state_rel
    if not path.is_file():
        return "manual"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- Selected lane:"):
            return line.split(":", 1)[1].strip().strip("`") or "manual"
    return "manual"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--command", choices=sorted(COMMAND_SCOPES), default="status")
    parser.add_argument("--slug", default="{slug}")
    parser.add_argument("--date", default="{date}")
    parser.add_argument("--module", default="{module_slug}")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    contract = json.loads((repo / "core" / "contract.yaml").read_text(encoding="utf-8"))
    paths = contract["paths"]
    profiles = contract.get("artifact_profiles", {})

    scope_keys = list(COMMAND_SCOPES[args.command])
    if args.command == "wireframes":
        lane_state_rel = render_path(paths["tool_lane_state"], slug=args.slug, date=args.date, module=args.module)
        lane = "manual" if "{" in lane_state_rel else detect_lane(repo, lane_state_rel)
        scope_keys.extend(LANE_SCOPES.get(lane, []))
    else:
        lane = ""

    rows = []
    total = 0
    for key in scope_keys:
        template = paths.get(key)
        if not template:
            continue
        rendered = render_path(template, slug=args.slug, date=args.date, module=args.module)
        size = 0 if "{" in rendered else size_for(repo, rendered)
        total += size
        rows.append((key, profiles.get(key, "unclassified"), rendered, size))

    print(f"Context budget for command: {args.command}")
    if lane:
        print(f"Resolved tool lane: {lane}")
    print("")
    print("| Path Key | Profile | Resolved Path | Bytes |")
    print("| --- | --- | --- | --- |")
    for key, profile, rendered, size in rows:
        print(f"| {key} | {profile} | `{rendered}` | {size} |")
    print(f"| TOTAL | | | {total} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
