#!/usr/bin/env python3
"""Validate backbone-owned CR/MSG registries and module usage."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CODE_RE = re.compile(r"\b(CR-(?:DIS|BEH|VAL|MIX)-\d{2}|MSG-(?:ERR|WRN|SUC|INF)-\d{2})\b")
DATE_RE = re.compile(r"^(.+)-(\d{6}-\d{4})$")
MODULE_LOCAL_HEADINGS = re.compile(r"^##\s+(Common Rules|Quy tắc dùng chung|Message List|Danh sách thông điệp)\b", re.MULTILINE)


def render_path(template: str, *, slug: str, date: str, module: str = "") -> str:
    return (
        template.replace("{slug}", slug)
        .replace("{date}", date)
        .replace("{module_slug}", module)
        .replace("{group}", "*")
        .replace("{option}", "*")
    )


def read_contract(ba_source: Path) -> dict:
    return json.loads((ba_source / "core" / "contract.yaml").read_text(encoding="utf-8"))


def infer_from_module_root(module_root: Path) -> tuple[Path, str, str, str]:
    resolved = module_root.resolve()
    parts = resolved.parts
    if "plans" not in parts or "03_modules" not in parts:
        raise SystemExit("Cannot infer repo/slug/date/module from module_root")
    module_index = parts.index("03_modules")
    project_dir = parts[module_index - 1]
    match = DATE_RE.match(project_dir)
    if not match:
        raise SystemExit(f"Cannot parse project directory: {project_dir}")
    slug, date = match.groups()
    module = parts[module_index + 1]
    repo = Path(*parts[: parts.index("plans")])
    return repo, slug, date, module


def table_rows_after(text: str, heading: str) -> list[dict[str, str]]:
    start = text.find(heading)
    if start == -1:
        return []
    next_heading = text.find("\n## ", start + len(heading))
    section = text[start : next_heading if next_heading != -1 else len(text)]
    rows = [line for line in section.splitlines() if line.startswith("|") and "---" not in line]
    if len(rows) < 2:
        return []
    headers = [cell.strip() for cell in rows[0].strip("|").split("|")]
    parsed: list[dict[str, str]] = []
    for row in rows[1:]:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if len(cells) < len(headers):
            cells.extend([""] * (len(headers) - len(cells)))
        parsed.append(dict(zip(headers, cells)))
    return parsed


def load_registry(path: Path, heading: str, text_column: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    errors: list[str] = []
    entries: dict[str, dict[str, str]] = {}
    if not path.is_file():
        return entries, [f"missing registry: {path}"]
    for row in table_rows_after(path.read_text(encoding="utf-8"), heading):
        code = row.get("code", "").strip("` ")
        if not code or code.startswith("["):
            continue
        if code in entries and entries[code].get(text_column) != row.get(text_column):
            errors.append(f"duplicate code with different text: {code} in {path}")
        entries[code] = row
    return entries, errors


def load_index(path: Path) -> tuple[set[str], str, list[str]]:
    if not path.is_file():
        return set(), "missing", []
    text = path.read_text(encoding="utf-8")
    metadata = {row.get("Field", ""): row.get("Value", "") for row in table_rows_after(text, "## Metadata")}
    status = metadata.get("stale_status", "").strip("` ") or "unknown"
    codes: set[str] = set()
    for heading in ("## Rule Code Index", "## Message Code Index"):
        for row in table_rows_after(text, heading):
            code = row.get("code", "").strip("` ")
            if code and not code.startswith("["):
                codes.add(code)
    errors = [] if codes or status != "current" else [f"current index has no codes: {path}"]
    return codes, status, errors


def module_files(module_root: Path) -> list[Path]:
    patterns = [
        "ascii-screen/*.md",
        "usecases/*.md",
        "srs.md",
        "srs/*.md",
        "screen-field-contract.yaml",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(module_root.glob(pattern)))
    return [path for path in files if path.is_file()]


def issue(severity: str, code: str, message: str, path: Path | None = None) -> dict[str, str]:
    item = {"severity": severity, "code": code, "message": message}
    if path:
        item["path"] = path.as_posix()
    return item


def build_index(common_rules: Path, message_list: Path, index_path: Path, rules: dict, messages: dict, issues: list[dict[str, str]]) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = [
        "# Chỉ mục rule/message dùng chung (Shared Rule Message Index)",
        "",
        "## Metadata",
        "",
        "| Field | Value |",
        "| --- | --- |",
        "| index_type | shared-rule-message |",
        f"| source_common_rules | `{common_rules.as_posix()}` |",
        f"| source_message_list | `{message_list.as_posix()}` |",
        f"| generated_at | {now} |",
        "| generated_by_command | `validate-shared-rule-message-registry --write-index` |",
        "| stale_status | current |",
        f"| validated_at | {now} |",
        "| validated_by | `validate-shared-rule-message-registry` |",
        "",
        "## Rule Code Index",
        "",
        "| code | type | summary | source_anchor | applies_to | owner | status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for code, row in sorted(rules.items()):
        lines.append(
            f"| {code} | {row.get('type', '')} | {row.get('rule_statement', '')} | common-rules.md#{code} | {row.get('applies_to', '')} | {row.get('owner', '')} | {row.get('status', '')} |"
        )
    lines.extend(
        [
            "",
            "## Message Code Index",
            "",
            "| code | type | summary | source_anchor | applies_to | owner | status |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for code, row in sorted(messages.items()):
        lines.append(
            f"| {code} | {row.get('type', '')} | {row.get('canonical_text', '')} | message-list.md#{code} | {row.get('applies_to', '')} | {row.get('owner', '')} | {row.get('status', '')} |"
        )
    errors = [entry for entry in issues if entry["severity"] == "error"]
    lines.extend(
        [
            "",
            "## Collision And Scope Signals",
            "",
            "| signal | value |",
            "| --- | --- |",
            f"| rule_count | {len(rules)} |",
            f"| message_count | {len(messages)} |",
            f"| duplicate_codes | {sum(1 for entry in issues if entry['code'] == 'duplicate_code')} |",
            f"| stale_refs | {sum(1 for entry in issues if entry['code'] == 'undeclared_code')} |",
            f"| module_local_definitions | {sum(1 for entry in issues if entry['code'] == 'module_local_definition')} |",
            f"| error_count | {len(errors)} |",
        ]
    )
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="")
    parser.add_argument("--slug", default="")
    parser.add_argument("--date", default="")
    parser.add_argument("--module", default="")
    parser.add_argument("--module-root", type=Path)
    parser.add_argument("--write-index", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    # BAkit source dir: where core/contract.yaml lives. Default to script's own parent repo.
    ba_source = Path(__file__).resolve().parent.parent

    if args.module_root:
        repo, slug, date, module = infer_from_module_root(args.module_root)
    else:
        repo = Path(args.repo).resolve() if args.repo else Path.cwd()
        slug, date, module = args.slug, args.date, args.module
    if not slug or not date:
        raise SystemExit("--slug and --date are required unless --module-root is provided")

    paths = read_contract(ba_source)["paths"]
    common_rules = repo / render_path(paths["common_rules"], slug=slug, date=date)
    message_list = repo / render_path(paths["message_list"], slug=slug, date=date)
    index_path = repo / render_path(paths["shared_rule_message_index"], slug=slug, date=date)

    index_codes, index_status, index_errors = load_index(index_path)
    use_full_registries = args.write_index or index_status != "current"
    rules: dict[str, dict[str, str]] = {}
    messages: dict[str, dict[str, str]] = {}
    issues = [issue("error", "index_error", error) for error in index_errors]
    if use_full_registries:
        if index_status != "current":
            issues.append(issue("warning", "stale_index", f"shared index status is {index_status}; reading full registries"))
        rules, rule_errors = load_registry(common_rules, "## Common Rules", "rule_statement")
        messages, message_errors = load_registry(message_list, "## Message List", "canonical_text")
        issues.extend(issue("error", "registry_error", error) for error in rule_errors + message_errors)

    module_roots = [repo / render_path(paths["module_root"], slug=slug, date=date, module=module)] if module else sorted((repo / render_path(paths["project_root"], slug=slug, date=date) / "03_modules").glob("*"))
    declared = (set(rules) | set(messages)) if use_full_registries else index_codes
    for module_root in [path for path in module_roots if path.is_dir()]:
        for path in module_files(module_root):
            rel = path.relative_to(repo)
            text = path.read_text(encoding="utf-8")
            if MODULE_LOCAL_HEADINGS.search(text):
                issues.append(issue("error", "module_local_definition", "module artifact defines Common Rules or Message List; use backbone registries", rel))
            for code in sorted(set(CODE_RE.findall(text))):
                if code not in declared:
                    issues.append(issue("error", "undeclared_code", f"{code} is not declared in backbone shared registries", rel))
            if re.search(r"(inline|toast|banner|error|lỗi|thông báo)", text, re.IGNORECASE) and "MSG-" not in text:
                issues.append(issue("warning", "inline_message_without_code", "message-like text found without MSG-* reference", rel))

    if args.write_index:
        build_index(common_rules.relative_to(repo), message_list.relative_to(repo), index_path, rules, messages, issues)

    errors = [entry for entry in issues if entry["severity"] == "error"]
    result = {
        "ok": not errors,
        "slug": slug,
        "date": date,
        "module": module or "*",
        "common_rules": common_rules.relative_to(repo).as_posix(),
        "message_list": message_list.relative_to(repo).as_posix(),
        "shared_rule_message_index": index_path.relative_to(repo).as_posix(),
        "issues": issues,
    }
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(("PASS" if result["ok"] else "BLOCK") + ": shared rule/message registry")
        for entry in issues:
            prefix = "BLOCK" if entry["severity"] == "error" else "WARN"
            location = f" {entry['path']}:" if "path" in entry else ""
            print(f"{prefix}:{location} {entry['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
