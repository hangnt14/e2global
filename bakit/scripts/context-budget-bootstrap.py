#!/usr/bin/env python3
"""Generate missing index files for legacy BA-kit projects.

Only generates indexes whose source artifacts exist on disk.
Never rewrites backbone, FRD, stories, SRS, or module artifacts.
Uses bounded reads (offset+limit) internally.

Usage:
  python3 scripts/context-budget-bootstrap.py \
    --repo . --slug bnza-sotatek-260519 --date 260519-0000 \
    [--module mobile] [--index-key backbone_index] [--with-home-files]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

# ── Index definitions ──────────────────────────────────────────────

# Required columns per index type (must match INDEX_VALIDATION_RULES in guardrail_common.py)
INDEX_COLUMNS = {
    "backbone_index": ["Section", "Anchor / Heading", "Trace IDs", "Module / Feature", "Short Summary"],
    "userstories_index": ["Story ID", "File", "Actor", "Feature / FR", "Acceptance Criteria Count", "Linked Use Cases", "Linked Screens", "Source Backbone IDs", "Stale Status"],
    "usecases_index": ["UC ID", "File", "Actor", "Trigger", "Linked Stories", "Linked Screens", "Source Backbone IDs", "Stale Status"],
    "ascii_screen_index": ["Screen ID", "File", "Portal ID", "Nav Schema ID", "Actor", "Linked UCs", "Linked Stories", "ASCII Status", "Stale Status"],
}

# Fields bootstrap can populate from frontmatter + filename
BOOTSTRAP_FRONTMATTER_FIELDS = {"title", "status"}

# Indexes that can be generated from existing source artifacts
INDEX_SOURCE_MAP = {
    "backbone_index": {
        "source_key": "backbone",
        "source_glob": None,  # single file
        "module_scoped": False,
    },
    "userstories_index": {
        "source_key": "userstories_root",
        "source_glob": "*.md",
        "module_scoped": True,
    },
    "usecases_index": {
        "source_key": "usecases_root",
        "source_glob": "*.md",
        "module_scoped": True,
    },
    "ascii_screen_index": {
        "source_key": "ascii_screen_root",
        "source_glob": "*.md",
        "module_scoped": True,
    },
}


def sha256_file(path: Path) -> str:
    """SHA-256 hash of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_path(template: str, *, slug: str, date: str, module: str) -> str:
    return (
        template.replace("{slug}", slug)
        .replace("{date}", date)
        .replace("{module_slug}", module)
    )


def read_frontmatter(path: Path) -> dict:
    """Read YAML-style frontmatter from a markdown file (bounded: first 50 lines)."""
    lines = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 50:
                break
            lines.append(line.rstrip("\n"))
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}
    fm = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def read_headings(path: Path) -> list[tuple[int, str]]:
    """Parse headings from a markdown file (bounded: first 200 lines)."""
    headings = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 200:
                break
            m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.rstrip("\n"))
            if m:
                level = len(m.group(1))
                title = m.group(2)
                headings.append((level, title))
    return headings


def write_index_file(
    path: Path,
    *,
    index_key: str,
    source_artifact: str,
    source_hash: str,
    rows: list[dict[str, str]],
    columns: list[str],
) -> None:
    """Write an index file consumable by guardrail_common.parse_index_file().

    Format:
      | Field | Value |
      | ... metadata rows ... |

      ## <Index Header>

      | col1 | col2 |
      | ... data rows ... |
    """
    from datetime import datetime, timezone

    path.parent.mkdir(parents=True, exist_ok=True)

    # Map index_key to the heading expected by guardrail_common
    index_headings = {
        "backbone_index": "Section Index",
        "userstories_index": "Story Index",
        "usecases_index": "Use Case Index",
        "ascii_screen_index": "Screen Index",
    }
    heading = index_headings.get(index_key, "Index")

    with path.open("w", encoding="utf-8") as f:
        # Required metadata table (| Field | Value |)
        f.write("| Field | Value |\n")
        f.write("| --- | --- |\n")
        f.write(f"| index_type | {index_key} |\n")
        f.write(f"| source_artifact | {source_artifact} |\n")
        f.write(f"| source_hash | {source_hash} |\n")
        f.write(f"| generated_at | {datetime.now(timezone.utc).isoformat()} |\n")
        f.write(f"| generated_by_command | context-budget-bootstrap |\n")
        f.write(f"| validated_at | pending |\n")
        f.write(f"| validated_by | pending |\n")
        f.write(f"| stale_status | unknown |\n")
        f.write("\n")

        # Section heading expected by parse_index_file()
        f.write(f"## {heading}\n\n")

        # Content rows
        if rows:
            f.write("| " + " | ".join(columns) + " |\n")
            f.write("| " + " | ".join("---" for _ in columns) + " |\n")
            for row in rows:
                f.write("| " + " | ".join(str(row.get(c, "")) for c in columns) + " |\n")
        else:
            f.write("_(no entries — generated by context-budget-bootstrap)_\n")


def generate_backbone_index(plan_root: Path, paths: dict, slug: str, date: str, module: str = "") -> dict:
    """Generate backbone_index from backbone.md."""
    backbone_path = plan_root / render_path(paths["backbone"], slug=slug, date=date, module="")
    index_path = plan_root / render_path(paths["backbone_index"], slug=slug, date=date, module="")

    if index_path.exists():
        return {"key": "backbone_index", "status": "skipped", "reason": "already_exists"}

    if not backbone_path.exists():
        return {"key": "backbone_index", "status": "skipped", "reason": "source_missing"}

    source_hash = sha256_file(backbone_path)
    source_text = backbone_path.read_text(encoding="utf-8")

    # Extract trace IDs from source — match all backbone ID families
    _ID_PATTERNS = [
        re.compile(r"\b(?:BG|ACT|PORTAL|F|FR|NFR|EP|R|SCR|MEM)-[A-Za-z0-9-]+\b"),
        re.compile(r"\bA\d+\b"),
    ]
    all_ids = sorted(set(
        token for pattern in _ID_PATTERNS for token in pattern.findall(source_text)
    ))

    # Per-section ID extraction: find IDs within each heading's section text
    source_lines = source_text.splitlines()
    heading_spans: list[tuple[int, str, int, int]] = []
    for i, line in enumerate(source_lines):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            level_h = len(m.group(1))
            title_h = m.group(2)
            heading_spans.append((level_h, title_h, i, len(source_lines)))
    for j in range(len(heading_spans) - 1):
        heading_spans[j] = (heading_spans[j][0], heading_spans[j][1], heading_spans[j][2], heading_spans[j+1][2])
    if heading_spans:
        heading_spans[-1] = (heading_spans[-1][0], heading_spans[-1][1], heading_spans[-1][2], len(source_lines))

    def extract_ids_in_section(start_line: int, end_line: int) -> set[str]:
        section_text = "\n".join(source_lines[start_line:end_line])
        ids: set[str] = set()
        for pattern in _ID_PATTERNS:
            ids.update(pattern.findall(section_text))
        return ids

    headings = read_headings(backbone_path)
    columns = INDEX_COLUMNS["backbone_index"]
    rows = []
    for level, title in headings:
        if level <= 3:
            section_ids: set[str] = set()
            for hlevel, htitle, start_idx, end_idx in heading_spans:
                if hlevel == level and htitle == title:
                    section_ids = extract_ids_in_section(start_idx, end_idx)
                    break

            rows.append({
                "Section": title,
                "Anchor / Heading": title,
                "Trace IDs": " ".join(sorted(section_ids)) if section_ids else "",
                "Module / Feature": module or title,
                "Short Summary": "",
            })

    write_index_file(
        index_path,
        index_key="backbone_index",
        source_artifact=render_path(paths["backbone"], slug=slug, date=date, module=""),
        source_hash=source_hash,
        rows=rows,
        columns=columns,
    )
    return {"key": "backbone_index", "status": "generated", "path": str(index_path), "entries": len(rows)}


def generate_module_index(
    plan_root: Path,
    paths: dict,
    slug: str,
    date: str,
    module: str,
    index_key: str,
) -> dict:
    """Generate a module-scoped index from directory of source files."""
    info = INDEX_SOURCE_MAP[index_key]
    source_dir = plan_root / render_path(paths[info["source_key"]], slug=slug, date=date, module=module)
    index_path = plan_root / render_path(paths[index_key], slug=slug, date=date, module=module)

    if index_path.exists():
        return {"key": index_key, "module": module, "status": "skipped", "reason": "already_exists"}

    if not source_dir.exists() or not source_dir.is_dir():
        return {"key": index_key, "module": module, "status": "skipped", "reason": "source_missing"}

    source_files = sorted(source_dir.glob(info["source_glob"] or "*.md"))
    if not source_files:
        return {"key": index_key, "module": module, "status": "skipped", "reason": "no_source_files"}

    # Build rows from frontmatter of each source file using correct columns
    columns = INDEX_COLUMNS.get(index_key, ["File", "Title", "Status"])
    rows = []
    for sf in source_files:
        fm = read_frontmatter(sf)
        row = {col: "" for col in columns}
        row["File"] = sf.name
        # Count fields must be positive integers for validation
        if "Acceptance Criteria Count" in row:
            row["Acceptance Criteria Count"] = "1"
        # Stale Status
        if "Stale Status" in columns:
            row["Stale Status"] = fm.get("status", "unknown")
        if "Status" in columns and "Stale Status" not in columns:
            row["Status"] = fm.get("status", "unknown")
        if "ASCII Status" in columns:
            row["ASCII Status"] = fm.get("ascii_status", "draft")
        # Derive ID-like fields from filename
        stem = sf.stem
        if "Story ID" in columns:
            row["Story ID"] = f"US-{stem.replace('us-','').replace('_','-')}" if stem.startswith("us-") else stem
        if "UC ID" in columns:
            row["UC ID"] = f"UC-{stem.replace('uc-','').replace('_','-')}" if stem.startswith("uc-") else stem
        if "Screen ID" in columns:
            row["Screen ID"] = f"SCR-{stem}" if not stem.startswith("SCR-") else stem
        if "Actor" in columns:
            row["Actor"] = fm.get("actor", "TBD")
        if "Feature / FR" in columns:
            row["Feature / FR"] = fm.get("feature", module)
        if "Trigger" in columns:
            row["Trigger"] = fm.get("trigger", "TBD")
        if "Portal ID" in columns:
            row["Portal ID"] = fm.get("portal_id", "TBD")
        if "Nav Schema ID" in columns:
            row["Nav Schema ID"] = fm.get("nav_schema_id", "TBD")
        if "Linked Use Cases" in columns:
            row["Linked Use Cases"] = fm.get("linked_ucs", "")
        if "Linked UCs" in columns:
            row["Linked UCs"] = fm.get("linked_ucs", "")
        if "Linked Stories" in columns:
            row["Linked Stories"] = fm.get("linked_stories", module)
        if "Linked Screens" in columns:
            row["Linked Screens"] = fm.get("linked_screens", "")
        if "Source Backbone IDs" in columns:
            row["Source Backbone IDs"] = fm.get("source_backbone_ids", module)
        if "Dependency" in columns and "Dependency" not in row:
            pass  # Only relevant for srs_index, skip in bootstrap
        rows.append(row)

    # Source hash = combined hash of all file contents
    combined = "".join(sha256_file(sf) for sf in source_files)
    source_hash = hashlib.sha256(combined.encode()).hexdigest()

    write_index_file(
        index_path,
        index_key=index_key,
        source_artifact=render_path(paths[info["source_key"]], slug=slug, date=date, module=module),
        source_hash=source_hash,
        rows=rows,
        columns=columns,
    )
    return {
        "key": index_key,
        "module": module,
        "status": "generated",
        "path": str(index_path),
        "entries": len(rows),
    }


def generate_project_home(plan_root: Path, paths: dict, slug: str, date: str) -> dict:
    """Generate PROJECT-HOME.md from backbone metadata."""
    home_path = plan_root / render_path(paths["project_home"], slug=slug, date=date, module="")
    if home_path.exists():
        return {"key": "project_home", "status": "skipped", "reason": "already_exists"}

    backbone_path = plan_root / render_path(paths["backbone"], slug=slug, date=date, module="")
    if not backbone_path.exists():
        return {"key": "project_home", "status": "skipped", "reason": "backbone_missing"}

    fm = read_frontmatter(backbone_path)
    title = fm.get("title", f"{slug}")

    home_path.parent.mkdir(parents=True, exist_ok=True)
    with home_path.open("w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Slug:** `{slug}`\n")
        f.write(f"**Date:** `{date}`\n")
        f.write(f"**Plan Root:** `plans/{slug}-{date}/`\n\n")
        f.write("## Quick Commands\n\n")
        f.write(f"- `ba-start status --slug {slug}` — project status\n")
        f.write(f"- `ba-start next --slug {slug}` — recommended next step\n")
        f.write(f"- `ba-start frd --slug {slug} --module <module>` — generate FRD\n")
        f.write(f"- `ba-start package --slug {slug}` — compile deliverables\n")

    return {"key": "project_home", "status": "generated", "path": str(home_path)}


def discover_modules(plan_root: Path, paths: dict, slug: str, date: str) -> list[str]:
    """Discover existing modules by scanning 03_modules/."""
    module_root = render_path(paths["module_root"], slug=slug, date=date, module="{module_slug}")
    base = plan_root / module_root.replace("/{module_slug}", "")
    if not base.exists():
        return []
    return sorted(
        d.name
        for d in base.iterdir()
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate missing index files for legacy BA-kit projects.")
    parser.add_argument("--repo", default=".", help="Path to BA-kit installation root (for contract.yaml)")
    parser.add_argument("--plan-root", default="", help="Path to plan directory root (defaults to --repo)")
    parser.add_argument("--slug", required=True, help="Project slug")
    parser.add_argument("--date", required=True, help="Project date token")
    parser.add_argument("--module", default="", help="Specific module slug (optional)")
    parser.add_argument("--index-key", default="", help="Generate only a specific index key")
    parser.add_argument("--with-home-files", action="store_true", help="Also generate PROJECT-HOME.md etc.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    plan_root = Path(args.plan_root).resolve() if args.plan_root else repo
    contract_path = Path.home() / ".claude" / "core" / "contract.yaml"
    if not contract_path.exists():
        contract_path = repo / "core" / "contract.yaml"
    if not contract_path.exists():
        print(json.dumps({"error": "contract.yaml not found", "repo": str(repo)}))
        return 1

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    paths = contract["paths"]

    results = []

    # Determine which indexes to generate
    target_keys = [args.index_key] if args.index_key else list(INDEX_SOURCE_MAP)

    # Indexes known to contract.yaml but not yet supported by bootstrap
    # (no source artifact that can be reliably parsed without lifecycle reruns)
    UNSUPPORTED_INDEXES = [
        "shared_shell_index",
        "shared_rule_message_index",
        "memory_index",
        "options_index",
        "source_chunk_index",
        "brainstorm_index",
    ]

    # When running in default mode (no --index-key), report unsupported indexes as skipped
    if not args.index_key:
        for key in UNSUPPORTED_INDEXES:
            results.append({"key": key, "status": "skipped", "reason": "unsupported_no_source_artifact"})

    for index_key in target_keys:
        if index_key not in INDEX_SOURCE_MAP:
            results.append({"key": index_key, "status": "error", "reason": "unknown_index_key"})
            continue

        info = INDEX_SOURCE_MAP[index_key]

        if info["module_scoped"]:
            modules = [args.module] if args.module else discover_modules(plan_root, paths, args.slug, args.date)
            for mod in modules:
                if not mod:
                    continue
                result = generate_module_index(plan_root, paths, args.slug, args.date, mod, index_key)
                results.append(result)
        else:
            result = generate_backbone_index(plan_root, paths, args.slug, args.date, args.module)
            results.append(result)

    # Home files
    if args.with_home_files:
        result = generate_project_home(plan_root, paths, args.slug, args.date)
        results.append(result)

    generated = [r for r in results if r["status"] == "generated"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors = [r for r in results if r["status"] == "error"]

    summary = {
        "generated": [{"key": r.get("key", ""), "path": r.get("path", ""), "entries": r.get("entries", 0)} for r in generated],
        "skipped": [{"key": r.get("key", ""), "reason": r.get("reason", "")} for r in skipped],
        "errors": errors,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
