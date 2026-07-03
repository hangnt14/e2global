#!/usr/bin/env python3
"""Build a narrow validated package snapshot manifest from current indexes.

The manifest is a machine-readable YAML-frontmatter file that records which
artifact paths are present, their hashes, and their index states.  Package,
status, and next can consume this manifest instead of re-running broad
discovery reads.

Usage:
    python3 scripts/package-snapshot.py --repo . --slug <slug> --date <date> [--module <module>] [--output <path>]

Exit codes:
    0  manifest written (all required indexes current)
    1  one or more indexes missing or stale (manifest written with degraded state)
    2  contract load error or unrecoverable failure
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from guardrail_common import (
    classify_index_state,
    load_contract,
    render_path,
    sha256_file,
)

SNAPSHOT_VERSION = "1"

SNAPSHOT_INDEX_KEYS = ["backbone_index", "userstories_index", "usecases_index", "ascii_screen_index"]

SNAPSHOT_ARTIFACT_KEYS = [
    "intake",
    "plan",
    "backbone",
    "frd",
    "srs",
    "srs_spec",
    "srs_compile_receipt",
    "shared_traceability",
    "shared_staleness",
    "shared_definitions",
    "compiled_frd",
    "compiled_srs",
    "project_home",
    "memory_index",
    "project_memory",
]


def artifact_entry(repo: Path, path_str: str) -> dict:
    """Return a compact entry for a single artifact path."""
    p = repo / path_str
    if not p.exists():
        return {"path": path_str, "exists": False}
    stat = p.stat()
    return {
        "path": path_str,
        "exists": True,
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha256_file(p),
    }


def index_entry(repo: Path, contract: dict, *, index_key: str, slug: str, date: str, module: str) -> dict:
    """Classify an index and return a compact entry."""
    state_data = classify_index_state(
        repo=repo,
        contract=contract,
        index_key=index_key,
        slug=slug,
        date=date,
        module=module,
    )
    entry: dict = {
        "index_key": index_key,
        "state": state_data["state"],
        "path": state_data.get("path", ""),
        "reason": state_data.get("reason", ""),
    }
    if "source_artifact" in state_data:
        entry["source_artifact"] = state_data["source_artifact"]
    return entry


def build_snapshot(repo: Path, contract: dict, *, slug: str, date: str, module: str) -> dict:
    """Build the full snapshot dict."""
    paths = contract["paths"]

    indexes: list[dict] = []
    all_current = True
    for key in SNAPSHOT_INDEX_KEYS:
        if key not in paths:
            continue
        entry = index_entry(repo, contract, index_key=key, slug=slug, date=date, module=module)
        indexes.append(entry)
        if entry["state"] != "current":
            all_current = False

    artifacts: list[dict] = []
    for key in SNAPSHOT_ARTIFACT_KEYS:
        template = paths.get(key)
        if not template:
            continue
        path_str = render_path(template, slug=slug, date=date, module=module)
        artifacts.append(artifact_entry(repo, path_str))

    # Detect module directories
    module_root_template = paths.get("module_root", "")
    modules_found: list[str] = []
    if module_root_template:
        modules_parent = repo / render_path(
            str(Path(module_root_template).parent), slug=slug, date=date, module=module
        )
        if modules_parent.exists():
            modules_found = sorted(d.name for d in modules_parent.iterdir() if d.is_dir())

    snapshot_state = "current" if all_current else "degraded"

    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "slug": slug,
        "date": date,
        "module": module or "",
        "snapshot_state": snapshot_state,
        "indexes": indexes,
        "artifacts": artifacts,
        "modules_found": modules_found,
    }


def render_yaml_frontmatter(data: dict) -> str:
    """Render snapshot as a markdown file with YAML frontmatter."""
    lines = ["---"]
    for key in ("snapshot_version", "generated_at", "slug", "date", "module", "snapshot_state"):
        lines.append(f"{key}: {json.dumps(data[key])}")
    lines.append("---")
    lines.append("")
    lines.append("# Package Snapshot Manifest")
    lines.append("")
    lines.append(f"- slug: `{data['slug']}`")
    lines.append(f"- date: `{data['date']}`")
    lines.append(f"- state: `{data['snapshot_state']}`")
    lines.append(f"- generated_at: `{data['generated_at']}`")
    lines.append("")
    lines.append("## Indexes")
    lines.append("")
    for idx in data["indexes"]:
        mark = "current" if idx["state"] == "current" else idx["state"]
        lines.append(f"- `{idx['index_key']}`: {mark} — `{idx['path']}`")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    for art in data["artifacts"]:
        if art["exists"]:
            lines.append(f"- `{art['path']}` — {art['size_bytes']}B sha256:{art['sha256'][:12]}")
        else:
            lines.append(f"- `{art['path']}` — missing")
    if data["modules_found"]:
        lines.append("")
        lines.append("## Modules Found")
        lines.append("")
        for mod in data["modules_found"]:
            lines.append(f"- `{mod}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build package snapshot manifest.")
    parser.add_argument("--repo", default=".", help="Repo root path")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", default="")
    parser.add_argument("--output", help="Write manifest to this path (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of markdown")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    try:
        contract = load_contract(repo)
    except Exception as exc:
        print(f"ERROR: failed to load contract: {exc}", file=sys.stderr)
        return 2

    snapshot = build_snapshot(repo, contract, slug=args.slug, date=args.date, module=args.module)

    if getattr(args, "json"):
        text = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    else:
        text = render_yaml_frontmatter(snapshot)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(f"SNAPSHOT: state={snapshot['snapshot_state']} path={args.output}")
    else:
        print(text, end="")

    return 0 if snapshot["snapshot_state"] == "current" else 1


if __name__ == "__main__":
    raise SystemExit(main())
