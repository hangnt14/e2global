#!/usr/bin/env python3
"""ba-qc-export: Export BA-kit module canon into QC-kit per-UC input format.

One-way bridge. BA-kit canon remains source of truth.
Output goes to 04_compiled/qc-kit/docs/BA/ by default.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Placeholder patterns (same as compile-srs.py)
PLACEHOLDER_PATTERNS = [
    r"\[Tên dự án\]",
    r"\[Tên module\]",
    r"\[Tên portal[^\]]*\]",
    r"\[Tên màn hình\]",
    r"\[Tên UC\]",
    r"\[Mô tả\]",
    r"\[TBD\]",
    r"\[placeholder[^\]]*\]",
    r"\[Project\]",
    r"\[Module\]",
    r"\[Screen Name\]",
    r"\[Use Case Name\]",
]


def detect_placeholders(text: str, source_label: str) -> list[str]:
    """Find unfilled template placeholders in text."""
    found = []
    for pattern in PLACEHOLDER_PATTERNS:
        for m in re.finditer(pattern, text):
            found.append(f"{source_label}: {m.group(0)}")
    return found


# ---------------------------------------------------------------------------
# Write-scope guard (defence-in-depth — wrapper also runs this)
# ---------------------------------------------------------------------------

def _run_guard(output_root: Path) -> None:
    """Validate external-output against write-scope rules.

    Resolves guard from this exporter's own directory — always available,
    regardless of what --repo points to.  Fails closed: if output is inside
    the repo the guard MUST run and pass.
    """
    guard_script = Path(__file__).resolve().parent / "check-write-scope.py"
    result = subprocess.run(
        [sys.executable, str(guard_script), "--command", "qc-export", str(output_root)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        detail = "\n".join(filter(None, [result.stdout.strip(), result.stderr.strip()]))
        sys.exit(f"qc-export write-scope blocked: {output_root} outside allowed scope\n{detail}")


def _guard_path(path: Path, repo_root: Path) -> None:
    """Validate path against write-scope rules if it is inside the repo."""
    if path.is_relative_to(repo_root):
        _run_guard(path)


# ---------------------------------------------------------------------------
# YAML frontmatter (conservative subset — enough for BA-kit canon files)
# ---------------------------------------------------------------------------

_YAML_LINE_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)")

def _parse_yaml_list_lines(lines: list[str]) -> list[Any]:
    items: list[Any] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter_dict, body). Handles BA-kit's YAML subset."""
    if not text.startswith("---"):
        return {}, text
    end_idx = text.find("\n---", 3)
    if end_idx == -1:
        return {}, text
    fm_block = text[4:end_idx]
    body = text[end_idx + 4:].lstrip("\n")

    fm: dict[str, Any] = {}
    in_list: str | None = None
    list_lines: list[str] = []
    for raw in fm_block.splitlines():
        line = raw.rstrip()
        if in_list:
            if line.strip().startswith("- "):
                list_lines.append(line)
                continue
            fm[in_list] = _parse_yaml_list_lines(list_lines)
            in_list = None
            list_lines = []

        m = _YAML_LINE_RE.match(line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val == "":
                # could be start of a list
                in_list = key
                list_lines = []
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                fm[key] = [x.strip().strip("'\"") for x in inner.split(",")] if inner else []
            else:
                fm[key] = val.strip("'\"")
    if in_list and list_lines:
        fm[in_list] = _parse_yaml_list_lines(list_lines)
    return fm, body


# ---------------------------------------------------------------------------
# Markdown section splitting
# ---------------------------------------------------------------------------

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def split_sections(body: str) -> list[tuple[int, str, str]]:
    """Return list of (level, heading, content) preserving all sections in order."""
    sections: list[tuple[int, str, str]] = []
    current_level: int | None = None
    current_heading: str = ""
    current_lines: list[str] = []

    for line in body.splitlines():
        m = HEADING_RE.match(line)
        if m:
            if current_heading or current_lines:
                sections.append((current_level or 1, current_heading, "\n".join(current_lines).strip()))
            current_level = len(m.group(1))
            current_heading = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading or current_lines:
        sections.append((current_level or 1, current_heading, "\n".join(current_lines).strip()))
    return sections


def sections_to_dict(body: str) -> dict[str, str]:
    """Return {heading: full_content} for ## headings, including all ### subsections."""
    result: dict[str, str] = {}
    sections = split_sections(body)
    current_h2: str | None = None
    buf: list[str] = []

    for level, heading, content in sections:
        if level == 2:
            if current_h2 is not None:
                result[current_h2] = "\n".join(buf).strip()
            current_h2 = heading
            buf = [content] if content.strip() else []
        elif current_h2 is not None:
            hdr = f"{'#' * level} {heading}"
            if content.strip():
                buf.append(f"{hdr}\n{content}")
            else:
                buf.append(hdr)

    if current_h2 is not None:
        result[current_h2] = "\n".join(buf).strip()
    return result


def get_subsections(body: str, parent_heading: str) -> list[tuple[int, str, str]]:
    """Get subsections within a parent section by heading name."""
    sections = split_sections(body)
    in_target = False
    parent_level: int | None = None
    result: list[tuple[int, str, str]] = []
    for level, heading, content in sections:
        if heading == parent_heading:
            in_target = True
            parent_level = level
            continue
        if in_target:
            if parent_level is not None and level <= parent_level:
                break
            result.append((level, heading, content))
    return result


# ---------------------------------------------------------------------------
# Registry parsing
# ---------------------------------------------------------------------------

TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")
CODE_RE = re.compile(r"\b(CR-[A-Z]+-\d{2,3}|MSG-[A-Z]+-\d{2,3}|BR-[A-Za-z0-9-]+)\b")


def parse_registry_table(content: str) -> dict[str, str]:
    """Parse a markdown table into {code: description} map. First column = code."""
    registry: dict[str, str] = {}
    lines = content.strip().splitlines()
    for line in lines:
        m = TABLE_ROW_RE.match(line.strip())
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if not cells or cells[0].startswith("-") or cells[0] == "Code":
            continue
        code = cells[0].strip("`")
        desc = cells[1] if len(cells) > 1 else ""
        if re.match(r"^(CR-|MSG-|BR-)", code):
            registry[code] = desc
    return registry


def parse_registry_bullets(content: str) -> dict[str, str]:
    """Parse bullet-based registry: `- **CODE**: description`."""
    registry: dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        m = re.match(r"^-\s*\*?\*?(CR-\w+-\d{2,3}|MSG-\w+-\d{2,3}|BR-[\w-]+)\*?\*?\s*[:：-]\s*(.+)", stripped)
        if m:
            registry[m.group(1)] = m.group(2).strip()
    return registry


def load_registry(filepath: Path) -> dict[str, str]:
    """Load a registry file, trying table first, then bullets."""
    if not filepath.exists():
        return {}
    content = filepath.read_text(encoding="utf-8")
    _, body = split_frontmatter(content)
    registry = parse_registry_table(body)
    if not registry:
        registry = parse_registry_bullets(body)
    return registry


def resolve_codes_in_text(text: str, registry: dict[str, str]) -> tuple[str, list[str]]:
    """Resolve CR-*/MSG-*/BR-* codes in text. Returns (resolved_text, unresolved_codes)."""
    unresolved: list[str] = []
    seen = set()

    def _replace(m: re.Match) -> str:
        code = m.group(1)
        if code in registry:
            return f"{code} ({registry[code]})"
        if code not in seen:
            unresolved.append(code)
            seen.add(code)
        return f"{code} [unresolved]"

    result = CODE_RE.sub(_replace, text)
    return result, unresolved


# ---------------------------------------------------------------------------
# Contract helpers
# ---------------------------------------------------------------------------

def load_contract(repo: Path) -> dict[str, Any]:
    # Try ~/.claude/core/ first (installed BA-kit contract), then {repo}/core/
    home_contract = Path.home() / ".claude" / "core" / "contract.yaml"
    if home_contract.exists():
        return json.loads(home_contract.read_text(encoding="utf-8"))
    p = repo / "core" / "contract.yaml"
    if not p.exists():
        sys.exit(f"Contract not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def render_path(template: str, **kwargs: str) -> str:
    result = template
    # Support both {module} and {module_slug} in templates
    if "module" in kwargs and "{module_slug}" in result:
        kwargs = {**kwargs, "module_slug": kwargs["module"]}
    for key, val in kwargs.items():
        result = result.replace(f"{{{key}}}", val)
    return result


# ---------------------------------------------------------------------------
# Artifact indexing
# ---------------------------------------------------------------------------

def index_files(directory: Path, glob_pattern: str) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob(glob_pattern))


def build_story_index(stories_root: Path) -> dict[str, Path]:
    """Map story slug -> file path."""
    idx: dict[str, Path] = {}
    for f in index_files(stories_root, "us-*.md"):
        slug = f.stem  # e.g. us-001
        idx[slug] = f
    return idx


def build_screen_index(screens_root: Path) -> dict[str, Path]:
    """Map screen slug -> file path."""
    idx: dict[str, Path] = {}
    for f in index_files(screens_root, "*.md"):
        if f.name == "index.md":
            continue
        idx[f.stem] = f
    return idx


# ---------------------------------------------------------------------------
# PNG asset discovery
# ---------------------------------------------------------------------------

def find_pngs(screen_path: Path, screens_dir: Path) -> list[Path]:
    """Find PNG files near a screen file: same-name directories or sibling PNGs."""
    pngs: list[Path] = []
    stem = screen_path.stem
    # Check for a directory named after the screen
    asset_dir = screen_path.parent / stem
    if asset_dir.is_dir():
        pngs.extend(sorted(asset_dir.glob("*.png")))
    # Check for sibling PNGs
    pngs.extend(sorted(screen_path.parent.glob(f"{stem}*.png")))
    # Deduplicate
    seen = set()
    result = []
    for p in pngs:
        if p.name not in seen:
            seen.add(p.name)
            result.append(p)
    return result


# ---------------------------------------------------------------------------
# Cross-function table parsing
# ---------------------------------------------------------------------------

def parse_cross_function_table(content: str) -> list[dict[str, str]]:
    """Parse a cross-function impact table into list of row dicts."""
    rows: list[dict[str, str]] = []
    lines = content.strip().splitlines()
    headers: list[str] = []
    for line in lines:
        m = TABLE_ROW_RE.match(line.strip())
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if not cells or cells[0] == "None" or cells[0] == "—":
            continue
        if not headers:
            # Check if it's a separator row
            if all(c.startswith("-") or c == "" for c in cells if c):
                continue
            headers = cells
            continue
        if all(c.startswith("-") or c == "" for c in cells if c):
            continue
        row = {}
        for i, cell in enumerate(cells):
            if i < len(headers):
                row[headers[i]] = cell
        if row:
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# QC Markdown renderer
# ---------------------------------------------------------------------------

def render_source_links(uc_slug: str, uc_path: Path, linked_stories: list[str],
                        linked_screens: list[str], module_root: Path,
                        common_rules_path: Path | None, message_list_path: Path | None,
                        repo_root: Path) -> str:
    """Render the BA-kit Source Links table."""
    lines = [
        "**BA-kit Source Links**",
        "",
        "| Artifact | Source Path |",
        "|----------|-------------|",
    ]
    uc_rel = _try_rel(uc_path, repo_root)
    lines.append(f"| Use Case | {uc_rel} |")
    for s in linked_stories:
        story_path = module_root / "userstories" / f"{s}.md"
        lines.append(f"| User Story {s} | `{_try_rel(story_path, repo_root)}` |")
    for scr in linked_screens:
        screen_path = module_root / "ascii-screen" / f"{scr}.md"
        lines.append(f"| Screen {scr} | `{_try_rel(screen_path, repo_root)}` |")
    if common_rules_path and common_rules_path.exists():
        lines.append(f"| Common Rules | {_try_rel(common_rules_path, repo_root)} |")
    if message_list_path and message_list_path.exists():
        lines.append(f"| Message List | {_try_rel(message_list_path, repo_root)} |")
    lines.append("")
    return "\n".join(lines)


def _try_rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except ValueError:
        return str(p)


def render_section_1(uc_sections: dict[str, str]) -> str:
    """Section 1: Use Case Description."""
    parts = ["## 1. Use Case Description", ""]
    for heading in ["Actors", "Preconditions", "Trigger", "Main Flow",
                     "Alternate Flows", "Error / Exception Flows", "Postconditions"]:
        if heading in uc_sections:
            parts.append(f"### {heading}")
            parts.append("")
            parts.append(uc_sections[heading])
            parts.append("")
    # Collect business rules from UC body
    uc_body = uc_sections.get("", "")
    if "business rule" in uc_body.lower() or "Business Rule" in uc_body:
        parts.append("### Business Rules")
        parts.append("")
        parts.append("Extracted from use case body — see source UC for details.")
        parts.append("")
    return "\n".join(parts)


def render_section_2(linked_screens: list[str], screen_index: dict[str, Path],
                     screens_dir: Path, repo_root: Path) -> tuple[str, list[str]]:
    """Section 2: Screen Description. Returns (markdown, png_copied_paths)."""
    parts = ["## 2. Screen Description", ""]
    all_pngs: list[Path] = []
    if not linked_screens:
        parts.append("_No screens linked to this use case._")
        parts.append("")
        return "\n".join(parts), []

    for scr_slug in linked_screens:
        scr_path = screen_index.get(scr_slug)
        if not scr_path:
            parts.append(f"### {scr_slug}")
            parts.append("")
            parts.append("_Screen file not found in canon._")
            parts.append("")
            continue

        parts.append(f"### {scr_slug}")
        parts.append("")
        # Read screen content, demoting ## → #### so screen headings don't leak
        # as top-level sections in the exported document.
        scr_text = scr_path.read_text(encoding="utf-8")
        _, scr_body = split_frontmatter(scr_text)
        # Demote any remaining ## headings to #### (preserve ### as-is for subsection)
        scr_body = re.sub(r"^## ", "#### ", scr_body, flags=re.MULTILINE)
        parts.append(scr_body)
        parts.append("")

        # List PNGs — link to the exported screens/ bundle, not the BA source path
        pngs = find_pngs(scr_path, screens_dir)
        if pngs:
            parts.append("#### Design Assets")
            parts.append("")
            for p in pngs:
                parts.append(f"- ![ {p.name} ](screens/{p.name})")
            parts.append("")
            all_pngs.extend(pngs)

    return "\n".join(parts), [str(p) for p in all_pngs]


def render_section_3(linked_screens: list[str], screen_index: dict[str, Path],
                     message_registry: dict[str, str],
                     rule_registry: dict[str, str]) -> tuple[str, list[str]]:
    """Section 3: Validation Summary. Returns (markdown, unresolved_codes)."""
    parts = ["## 3. Validation Summary", ""]
    all_unresolved: list[str] = []
    full_registry = {**rule_registry, **message_registry}

    if not linked_screens:
        parts.append("_No screens linked — no validation rules to export._")
        parts.append("")
        return "\n".join(parts), []

    for scr_slug in linked_screens:
        scr_path = screen_index.get(scr_slug)
        if not scr_path:
            continue
        scr_text = scr_path.read_text(encoding="utf-8")
        _, scr_body = split_frontmatter(scr_text)
        scr_sections = sections_to_dict(scr_body)

        parts.append(f"### {scr_slug} Validation Rules")
        parts.append("")
        # Try to find validation-related sections
        for heading in ["Validation Rules", "Field Validation", "Error States",
                        "Behaviour Rules", "Behavior Rules"]:
            if heading in scr_sections:
                content, unresolved = resolve_codes_in_text(scr_sections[heading], full_registry)
                all_unresolved.extend(unresolved)
                parts.append(f"#### {heading}")
                parts.append("")
                parts.append(content)
                parts.append("")
    return "\n".join(parts), all_unresolved


def render_section_4(uc_sections: dict[str, str], rule_registry: dict[str, str],
                     message_registry: dict[str, str], uc_body: str,
                     unresolved_input: list[str],
                     screen_codes: set[str] | None = None) -> tuple[str, list[str]]:
    """Section 4: Cross-References with Functional Integration."""
    parts = ["## 4. Cross-References", ""]
    all_unresolved = list(unresolved_input)

    # Collect all code references from UC body + screen bodies
    codes = set(CODE_RE.findall(uc_body))
    for content in uc_sections.values():
        codes.update(CODE_RE.findall(content))
    if screen_codes:
        codes.update(screen_codes)

    # Merge registries
    full_registry = {**rule_registry, **message_registry}

    # Build reference table
    if codes:
        parts.append("### Referenced Rules & Messages")
        parts.append("")
        parts.append("| Code | Description | Status |")
        parts.append("|------|-------------|--------|")
        for code in sorted(codes):
            if code in full_registry:
                parts.append(f"| {code} | {full_registry[code]} | Resolved |")
            else:
                parts.append(f"| {code} | — | Unresolved |")
                if code not in all_unresolved:
                    all_unresolved.append(code)
        parts.append("")
    else:
        parts.append("_No rule or message codes referenced in this use case._")
        parts.append("")

    # Functional Integration (from Cross-Function Impact)
    cf_content = uc_sections.get("Cross-Function Impact", "")
    if cf_content and cf_content.strip():
        parts.append("### Functional Integration")
        parts.append("")
        parts.append(cf_content)
        parts.append("")

    return "\n".join(parts), all_unresolved


def render_section_5(uc_sections: dict[str, str],
                     story_index: dict[str, Path],
                     linked_stories: list[str]) -> str:
    """Section 5: Open Questions."""
    parts = ["## 5. Open Questions", ""]

    oq_content = uc_sections.get("Open Questions", "")
    if oq_content:
        parts.append("### From Use Case")
        parts.append("")
        parts.append(oq_content)
        parts.append("")

    # Collect OQs from linked stories
    for s_slug in linked_stories:
        s_path = story_index.get(s_slug)
        if not s_path:
            continue
        s_text = s_path.read_text(encoding="utf-8")
        _, s_body = split_frontmatter(s_text)
        s_sections = sections_to_dict(s_body)
        s_oq = s_sections.get("Open Questions", "")
        if s_oq:
            parts.append(f"### From {s_slug}")
            parts.append("")
            parts.append(s_oq)
            parts.append("")

    if not oq_content and len(parts) <= 2:
        parts.append("_No open questions._")
        parts.append("")
    return "\n".join(parts)


def render_section_6(uc_fm: dict[str, Any], linked_stories: list[str],
                     story_index: dict[str, Path]) -> str:
    """Section 6: Changelog (aggregated from UC + stories)."""
    parts = ["## 6. Changelog", ""]

    # UC changelog
    uc_changelog = uc_fm.get("changelog", [])
    if uc_changelog:
        parts.append("### Use Case Changelog")
        parts.append("")
        if isinstance(uc_changelog, list):
            for entry in uc_changelog:
                parts.append(f"- {entry}")
        else:
            parts.append(str(uc_changelog))
        parts.append("")

    # Story changelogs
    for s_slug in linked_stories:
        s_path = story_index.get(s_slug)
        if not s_path:
            continue
        s_text = s_path.read_text(encoding="utf-8")
        s_fm, _ = split_frontmatter(s_text)
        s_cl = s_fm.get("changelog", [])
        if s_cl:
            parts.append(f"### {s_slug} Changelog")
            parts.append("")
            if isinstance(s_cl, list):
                for entry in s_cl:
                    parts.append(f"- {entry}")
            else:
                parts.append(str(s_cl))
            parts.append("")

    # Exporter entry
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts.append(f"### Export")
    parts.append("")
    parts.append(f"- {now} | ba-qc-export | generated from BA-kit canon")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Post-export validation
# ---------------------------------------------------------------------------

EXPECTED_HEADINGS = [
    "## 1. Use Case Description",
    "## 2. Screen Description",
    "## 3. Validation Summary",
    "## 4. Cross-References",
    "## 5. Open Questions",
    "## 6. Changelog",
]


def validate_exported_uc(content: str, uc_slug: str) -> list[str]:
    """Validate exported UC has exactly the 6 expected ## headings and no extras."""
    errors: list[str] = []
    found: list[str] = []
    for line in content.splitlines():
        if line.startswith("## "):
            found.append(line)

    expected_full = [h for h in EXPECTED_HEADINGS]

    if len(found) != len(expected_full):
        errors.append(
            f"{uc_slug}: expected {len(expected_full)} top-level ## headings, "
            f"found {len(found)}: {found}"
        )

    for i, exp in enumerate(expected_full):
        if i < len(found) and found[i] != exp:
            errors.append(
                f"{uc_slug}: heading {i + 1} expected '{exp}', got '{found[i]}'"
            )
        elif i >= len(found):
            errors.append(f"{uc_slug}: missing heading '{exp}'")

    for h in found:
        if h not in expected_full:
            errors.append(f"{uc_slug}: unexpected heading '{h}'")

    return errors


# ---------------------------------------------------------------------------
# Main export logic
# ---------------------------------------------------------------------------

def run_export(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    contract = load_contract(repo)
    paths = contract["paths"]
    slug, date_token, module = args.slug, args.date, args.module

    # Resolve paths
    module_root = repo / render_path(paths["module_root"], slug=slug, date=date_token, module=module)

    usecases_dir = repo / render_path(paths["usecases_root"], slug=slug, date=date_token, module=module)
    stories_dir = repo / render_path(paths["userstories_root"], slug=slug, date=date_token, module=module)
    screens_dir = repo / render_path(paths["ascii_screen_root"], slug=slug, date=date_token, module=module)
    common_rules_path = repo / render_path(paths.get("common_rules", "plans/{slug}-{date}/02_backbone/common-rules.md"), slug=slug, date=date_token)
    message_list_path = repo / render_path(paths.get("message_list", "plans/{slug}-{date}/02_backbone/message-list.md"), slug=slug, date=date_token)

    # Default output root
    output_root = repo / render_path(paths["qc_export_root"], slug=slug, date=date_token)
    if args.external_output:
        output_root = Path(args.external_output).resolve()
    _guard_path(output_root, repo)


    # Validate inputs
    if not module_root.exists():
        sys.exit(f"Module root not found: {module_root}")
    if not usecases_dir.exists():
        sys.exit(f"Use cases directory not found: {usecases_dir}")

    # Load registries
    rule_registry = load_registry(common_rules_path)
    message_registry = load_registry(message_list_path)

    # Build indexes
    story_index = build_story_index(stories_dir)
    screen_index = build_screen_index(screens_dir)

    # Index use cases
    uc_files = index_files(usecases_dir, "uc-*.md")
    if not uc_files:
        print("No use case files found.", file=sys.stderr)
        return 1

    # Output directories — clean stale UC files and usecase-list from prior exports for this module
    docs_ba = output_root / "docs" / "BA"
    module_docs_ba = docs_ba / module
    # Clean stale per-UC screen dirs from previous export
    for stale_dir in module_docs_ba.glob("UC-*-screens"):
        if stale_dir.is_dir():
            shutil.rmtree(stale_dir)
    # Clean stale UC markdown files from previous export (e.g. UC removed from canon)
    for stale_uc in module_docs_ba.glob("UC-*.md"):
        if stale_uc.is_file():
            stale_uc.unlink()
    stale_list = module_docs_ba / "usecase-list.md"
    if stale_list.exists():
        stale_list.unlink()
    common_dir = docs_ba / "Common rule"
    common_dir.mkdir(parents=True, exist_ok=True)

    # Write common rules and message list
    export_common_rules(common_dir, rule_registry, message_registry, repo)

    summary: dict[str, Any] = {
        "slug": slug,
        "date": date_token,
        "module": module,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "uc_count": len(uc_files),
        "usecases": [],
    }

    # Process each UC
    for uc_path in uc_files:
        uc_result = process_use_case(
            uc_path=uc_path,
            docs_ba=docs_ba,
            output_root=output_root,
            module_root=module_root,
            repo_root=repo,
            story_index=story_index,
            screen_index=screen_index,
            screens_dir=screens_dir,
            rule_registry=rule_registry,
            message_registry=message_registry,
            common_rules_path=common_rules_path,
            message_list_path=message_list_path,
            contract_paths=paths,
            slug=slug,
            date_token=date_token,
            module=module,
        )
        summary["usecases"].append(uc_result)

    # Write summary
    summary_path = output_root / "qc-export-summary.json"
    _guard_path(summary_path, repo)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


    # Optional usecase list
    if args.usecase_list:
        write_usecase_list(module_docs_ba, summary, uc_files, repo)


    # Print summary
    resolved = sum(1 for u in summary["usecases"] if not u.get("unresolved_refs"))
    total_unresolved = sum(len(u.get("unresolved_refs", [])) for u in summary["usecases"])
    total_placeholders = sum(len(u.get("placeholder_warnings", [])) for u in summary["usecases"])
    print(f"Exported {len(uc_files)} UC(s) to {docs_ba}")
    print(f"  Resolved: {resolved}/{len(uc_files)}")
    if total_unresolved:
        print(f"  Unresolved references: {total_unresolved}")
    if total_placeholders:
        print(f"  Placeholder warnings: {total_placeholders}")
        for u in summary["usecases"]:
            for pw in u.get("placeholder_warnings", []):
                print(f"    - {pw}")
    # Check validation errors
    total_val_errors = sum(len(u.get("validation_errors", [])) for u in summary["usecases"])
    if total_val_errors:
        print(f"  Validation errors: {total_val_errors}", file=sys.stderr)
        print(f"  Summary: {summary_path}")
        return 1
    print(f"  Summary: {summary_path}")
    return 0


def process_use_case(*, uc_path: Path, docs_ba: Path, output_root: Path,
                     module_root: Path, repo_root: Path,
                     story_index: dict[str, Path], screen_index: dict[str, Path],
                     screens_dir: Path, rule_registry: dict[str, str],
                     message_registry: dict[str, str], common_rules_path: Path | None,
                     message_list_path: Path | None,
                     contract_paths: dict[str, Any] | None = None,
                     slug: str = "", date_token: str = "",
                     module: str = "") -> dict[str, Any]:
    # noqa: PLR0913 — contract resolution, validation, external-output support
    """Process one UC file and write its QC export."""
    uc_text = uc_path.read_text(encoding="utf-8")
    uc_fm, uc_body = split_frontmatter(uc_text)
    uc_sections = sections_to_dict(uc_body)

    uc_slug = uc_fm.get("usecase_id", uc_fm.get("slug", uc_path.stem))
    # Sanitize: keep only safe chars for directory name
    uc_slug_safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(uc_slug))
    # Raw slug without UC- prefix for contract path templates (e.g. "checkout" not "UC-checkout")
    uc_slug_raw = uc_fm.get("slug", "")
    if uc_slug_raw.startswith("UC-"):
        uc_slug_raw = uc_slug_raw[3:]
    if not uc_slug_raw and str(uc_slug).startswith("UC-"):
        uc_slug_raw = str(uc_slug)[3:]
    if not uc_slug_raw:
        uc_slug_raw = uc_slug_safe
    linked_stories = _resolve_linked(uc_fm.get("linked_stories", []))
    linked_screens = _resolve_linked(uc_fm.get("linked_screens", []))

    # Resolve codes in UC body
    full_registry = {**rule_registry, **message_registry}
    _, unresolved_from_uc = resolve_codes_in_text(uc_body, full_registry)

    # Detect placeholders in UC body
    uc_placeholders = detect_placeholders(uc_body, f"UC-{uc_slug}")
    screen_placeholders: list[str] = []

    # Collect codes from linked screen bodies for §4 Cross-References
    screen_body_codes: set[str] = set()
    for scr_slug in linked_screens:
        scr_path = screen_index.get(scr_slug)
        if scr_path:
            scr_text = scr_path.read_text(encoding="utf-8")
            _, scr_body = split_frontmatter(scr_text)
            screen_body_codes.update(CODE_RE.findall(scr_body))
            screen_placeholders.extend(detect_placeholders(scr_body, f"Screen-{scr_slug}"))

    # Set source path for header metadata
    uc_fm["_source_path"] = str(_try_rel(uc_path, repo_root))

    # Render sections
    header = render_header(uc_fm, uc_slug)
    source_links = render_source_links(uc_slug, uc_path, linked_stories, linked_screens,
                                       module_root, common_rules_path, message_list_path, repo_root)
    sec1 = render_section_1(uc_sections)
    sec2, png_paths = render_section_2(linked_screens, screen_index, screens_dir, repo_root)
    sec3, unresolved_val = render_section_3(linked_screens, screen_index, message_registry, rule_registry)
    sec4, unresolved_cr = render_section_4(uc_sections, rule_registry, message_registry,
                                           uc_body, unresolved_from_uc + unresolved_val,
                                           screen_body_codes)
    sec5 = render_section_5(uc_sections, story_index, linked_stories)
    sec6 = render_section_6(uc_fm, linked_stories, story_index)

    all_unresolved = sorted(set(unresolved_cr))

    # Disclaimer
    disclaimer = (
        "> This file was generated by ba-qc-export.\n"
        "> It is a one-way handoff for QC-kit — do not edit as the business source.\n"
        "> Apply all corrections to the BA-kit canon artifacts, then re-export.\n"
    )

    full_doc = "\n\n".join([
        header, disclaimer, source_links, sec1, sec2, sec3, sec4, sec5, sec6
    ])

    # Resolve output path from contract when available, fallback to docs_ba layout.
    # Contract resolution uses output_root as base (handles both repo-default and --external-output).
    if contract_paths and slug and date_token:
        usecase_file_template = contract_paths.get(
            "qc_export_usecase_file",
            "plans/{slug}-{date}/04_compiled/qc-kit/docs/BA/{module}/UC-{usecase_slug}.md",
        )
        # Rebase contract path under output_root:
        # strip the qc_export_root prefix so result is output_root / relative-path-under-qc-kit
        qc_root_template = contract_paths.get(
            "qc_export_root",
            "plans/{slug}-{date}/04_compiled/qc-kit",
        )
        rendered_root = render_path(qc_root_template, slug=slug, date=date_token)
        rendered_full = render_path(
            usecase_file_template, slug=slug, date=date_token, usecase_slug=uc_slug_raw, module=module,
        )
        if rendered_full.startswith(rendered_root + "/"):
            rel = rendered_full[len(rendered_root) + 1:]
        else:
            rel = rendered_full
        out_path = output_root / rel
    else:
        uc_dir = docs_ba / module
        out_path = uc_dir / f"{uc_slug_safe}.md"

    # Validate before writing — invalid handoff must not be emitted
    validation_errors = validate_exported_uc(full_doc, str(uc_slug))
    generated_path = str(_try_rel(out_path, repo_root))
    if validation_errors:
        for err in validation_errors:
            print(f"  VALIDATION: {err}", file=sys.stderr)
        generated_path = "(not written — validation failed)"
    else:
        _guard_path(out_path, repo_root)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(full_doc + "\n", encoding="utf-8")

        # Copy PNGs
        screens_out = out_path.parent / f"UC-{uc_slug_safe}-screens"
        for png_src in png_paths:
            png_dest = screens_out / Path(png_src).name
            _guard_path(png_dest, repo_root)
            screens_out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(png_src, png_dest)


    return {
        "uc_slug": uc_slug,
        "source_path": str(_try_rel(uc_path, repo_root)),
        "generated_path": generated_path,
        "linked_stories": linked_stories,
        "linked_screens": linked_screens,
        "unresolved_refs": all_unresolved,
        "placeholder_warnings": sorted(set(uc_placeholders + screen_placeholders)),
        "validation_errors": validation_errors,
        "png_count": len(png_paths) if not validation_errors else 0,
    }


def _resolve_linked(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []


def render_header(uc_fm: dict[str, Any], uc_slug: str) -> str:
    lines = [
        f"# {uc_slug}",
        "",
        f"**Source Project:** {uc_fm.get('module', 'N/A')}",
        f"**Source UC Path:** `{uc_fm.get('_source_path', 'N/A')}`",
        f"**Export Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"**Actor:** {uc_fm.get('actor', 'N/A')}",
        f"**Status:** {uc_fm.get('status', 'N/A')}",
    ]
    return "\n".join(lines)


def export_common_rules(common_dir: Path, rule_registry: dict[str, str],
                        message_registry: dict[str, str], repo_root: Path) -> None:
    """Write common-rules.md and message-list.md in QC format."""
    # Common rules
    cr_lines = [
        "# Common Rules",
        "",
        "> Generated by ba-qc-export. One-way handoff — do not edit as business source.",
        "",
        "| Code | Description |",
        "|------|-------------|",
    ]
    for code in sorted(rule_registry):
        cr_lines.append(f"| {code} | {rule_registry[code]} |")
    cr_lines.append("")
    cr_path = common_dir / "common-rules.md"
    _guard_path(cr_path, repo_root)
    cr_path.write_text("\n".join(cr_lines), encoding="utf-8")

    # Message list
    ml_lines = [
        "# Message List",
        "",
        "> Generated by ba-qc-export. One-way handoff — do not edit as business source.",
        "",
        "| Code | Message |",
        "|------|---------|",
    ]
    for code in sorted(message_registry):
        ml_lines.append(f"| {code} | {message_registry[code]} |")
    ml_lines.append("")
    ml_path = common_dir / "message-list.md"
    _guard_path(ml_path, repo_root)
    ml_path.write_text("\n".join(ml_lines), encoding="utf-8")



def write_usecase_list(module_dir: Path, summary: dict[str, Any], uc_files: list[Path], repo_root: Path) -> None:
    lines = [
        "# Use Case List",
        "",
        "> Generated by ba-qc-export. One-way handoff — do not edit as business source.",
        "",
        "| UC ID | Resolved | Unresolved Refs |",
        "|-------|----------|-----------------|",
    ]
    for u in summary["usecases"]:
        slug = u["uc_slug"]
        resolved = "Yes" if not u.get("unresolved_refs") else "No"
        refs = ", ".join(u.get("unresolved_refs", [])) or "—"
        lines.append(f"| {slug} | {resolved} | {refs} |")
    lines.append("")
    list_path = module_dir / "usecase-list.md"
    _guard_path(list_path, repo_root)
    list_path.write_text("\n".join(lines), encoding="utf-8")



# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True, help="YYMMDD-HHmm token")
    parser.add_argument("--module", required=True)
    parser.add_argument("--repo", required=True, help="BA-kit repo root")
    parser.add_argument("--external-output", help="External output root (overrides default)")
    parser.add_argument("--usecase-list", action="store_true", help="Generate usecase-list.md")
    args = parser.parse_args()
    return run_export(args)


if __name__ == "__main__":
    sys.exit(main())
