#!/usr/bin/env python3
"""Check terminology consistency across BA artifacts.

Scans .md files for forbidden terms and suggests canonical replacements.
Terminology map loaded from control-type-library.md (## Terminology section).

Usage:
    python3 scripts/check-terminology-consistency.py path/ [--json] [--strict] [--fix]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Built-in terminology map (fallback when library not found)
BUILTIN_FORBIDDEN_MAP: dict[str, list[str]] = {
    "ấn": ["bấm", "nhấn", "nhấp", "click", "tap"],
    "chọn": ["select", "pick", "lựa"],
    "điền": ["nhập", "gõ", "type", "enter"],
    "mở": ["open", "navigate to", "redirect", "chuyển đến"],
    "đóng": ["close", "dismiss"],
    "hiện": ["show", "display", "xuất hiện", "render"],
    "ẩn": ["hide", "disappear"],
    "bật": ["on", "enable", "activate"],
    "tắt": ["off", "disable", "deactivate"],
    "lưu": ["save", "persist", "store"],
    "xóa": ["delete", "remove", "clear"],
    "kiểm tra": ["validate", "check", "verify"],
    "xác thực": ["authenticate", "auth"],
    "tìm": ["search", "query", "filter"],
    "gửi": ["send", "submit", "dispatch"],
    "hủy": ["cancel", "abort", "discard"],
    "tải lên": ["upload"],
    "tải xuống": ["download"],
}

# Exclusion zones — don't check these
EXCLUDE_PATTERNS = [
    re.compile(r"```[\s\S]*?```"),       # code blocks
    re.compile(r"`[^`]+`"),               # inline code
    re.compile(r"https?://\S+"),          # URLs
    re.compile(r"\b(?:CR|MSG|SCR|FR|NFR|UC|US|ACT)-\S+"),  # IDs
    re.compile(r"<!--.*?-->"),            # HTML comments
]


def load_terminology_map(library_path: Path | None) -> dict[str, list[str]]:
    """Load terminology from control-type-library.md ## Terminology section."""
    if library_path and library_path.exists():
        text = library_path.read_text(encoding="utf-8")
        term_start = text.find("## Terminology")
        if term_start != -1:
            next_h2 = text.find("\n## ", term_start + 1)
            section = text[term_start:next_h2 if next_h2 != -1 else len(text)]
            return _parse_terminology_tables(section)
    return dict(BUILTIN_FORBIDDEN_MAP)


def _parse_terminology_tables(section: str) -> dict[str, list[str]]:
    """Parse markdown tables in Terminology section: Từ chuẩn | Từ cấm."""
    result: dict[str, list[str]] = {}
    for table_match in re.finditer(r"\| Từ chuẩn \| Từ cấm \|.*?\n\|[-\s|]+\|\n((?:\|.*\n)+)", section):
        rows = table_match.group(1).strip().split("\n")
        for row in rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            if len(cells) >= 2:
                canonical = cells[0]
                forbidden_raw = cells[1]
                forbidden = [f.strip() for f in forbidden_raw.split(",") if f.strip()]
                if canonical and forbidden:
                    result[canonical] = forbidden
    return result


def _build_forbidden_to_canonical(term_map: dict[str, list[str]]) -> dict[str, str]:
    """Build reverse map: forbidden_word → canonical_word."""
    reverse: dict[str, str] = {}
    for canonical, forbidden_list in term_map.items():
        for fw in forbidden_list:
            reverse[fw.lower()] = canonical
    return reverse


def _strip_exclusions(text: str) -> str:
    """Replace exclusion zones with spaces to preserve line/col positions."""
    for pattern in EXCLUDE_PATTERNS:
        text = pattern.sub(lambda m: " " * len(m.group(0)), text)
    return text


def check_file(path: Path, forbidden_map: dict[str, str]) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    clean = _strip_exclusions(text)
    findings: list[dict[str, Any]] = []

    for line_num, line in enumerate(clean.splitlines(), start=1):
        for forbidden_word, canonical in forbidden_map.items():
            # Case-insensitive match for English, exact for Vietnamese
            if forbidden_word.isascii():
                pattern = re.compile(rf"\b{re.escape(forbidden_word)}\b", re.IGNORECASE)
            else:
                pattern = re.compile(re.escape(forbidden_word))

            for m in pattern.finditer(line):
                findings.append({
                    "file": str(path),
                    "line": line_num,
                    "col": m.start() + 1,
                    "forbidden": forbidden_word,
                    "suggestion": canonical,
                })

    return findings


def fix_file(path: Path, forbidden_map: dict[str, str]) -> int:
    """Replace forbidden terms with canonical. Returns number of replacements."""
    text = path.read_text(encoding="utf-8")
    clean = _strip_exclusions(text)
    orig_text = path.read_text(encoding="utf-8")
    count = 0

    # Build replacements per line (to avoid overlapping replacements)
    replacements: dict[int, list[tuple[int, int, str]]] = {}
    for line_num, line in enumerate(clean.splitlines(), start=1):
        for forbidden_word, canonical in forbidden_map.items():
            if forbidden_word.isascii():
                pattern = re.compile(rf"\b{re.escape(forbidden_word)}\b", re.IGNORECASE)
            else:
                pattern = re.compile(re.escape(forbidden_word))
            for m in pattern.finditer(line):
                if line_num not in replacements:
                    replacements[line_num] = []
                replacements[line_num].append((m.start(), m.end(), canonical))
                count += 1

    if not count:
        return 0

    # Backup
    backup = path.with_suffix(".bak")
    backup.write_text(orig_text, encoding="utf-8")

    # Apply replacements (reverse order to preserve positions)
    lines = orig_text.splitlines()
    for line_num, reps in sorted(replacements.items(), reverse=True):
        line = lines[line_num - 1]
        for start, end, canonical in sorted(reps, key=lambda r: r[0], reverse=True):
            line = line[:start] + canonical + line[end:]
        lines[line_num - 1] = line

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return count


def collect_files(raw_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in raw_paths:
        p = Path(raw_path)
        if p.is_dir():
            files += sorted(item for item in p.rglob("*.md") if "index.md" not in item.name)
        elif p.is_file():
            files.append(p)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Check terminology consistency")
    parser.add_argument("path", nargs="+", help="File(s) or directory to scan")
    parser.add_argument("--library", type=Path, help="Path to control-type-library.md for terminology map")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="BLOCK on forbidden terms (for CI)")
    parser.add_argument("--fix", action="store_true", help="Auto-replace forbidden terms with canonical")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help="Repo root")
    args = parser.parse_args()

    library_path = args.library
    if not library_path:
        template_path = args.repo / "templates" / "control-type-library-template.md"
        if template_path.exists():
            library_path = template_path

    term_map = load_terminology_map(library_path)
    forbidden_map = _build_forbidden_to_canonical(term_map)

    try:
        files = collect_files(args.path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.fix:
        total = 0
        for f in files:
            n = fix_file(f, forbidden_map)
            if n:
                print(f"Fixed {n} term(s) in {f}")
                total += n
        print(f"\nTotal: {total} replacements across {len(files)} files")
        return 0

    all_findings: list[dict[str, Any]] = []
    for f in files:
        findings = check_file(f, forbidden_map)
        all_findings.extend(findings)

    if args.json:
        print(json.dumps({"files_scanned": len(files), "findings": all_findings}, indent=2, ensure_ascii=False))
    else:
        if not all_findings:
            print(f"OK: {len(files)} files — terminology consistent")
        else:
            for finding in all_findings:
                print(f"  {finding['file']}:{finding['line']}:{finding['col']} "
                      f"'{finding['forbidden']}' → dùng '{finding['suggestion']}'")
            print(f"\n{len(all_findings)} forbidden term(s) in {len(files)} files")

    if args.strict and all_findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
