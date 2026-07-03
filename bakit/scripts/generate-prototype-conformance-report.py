#!/usr/bin/env python3
"""Generate a prototype conformance report skeleton from the screen field contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def render_path(template: str, *, slug: str, date: str, module: str) -> str:
    return (
        template.replace("{slug}", slug)
        .replace("{date}", date)
        .replace("{module_slug}", module)
        .replace("{group}", "*")
        .replace("{option}", "*")
    )


def detect_lane(path: Path) -> str:
    if not path.is_file():
        return "manual"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- Selected lane:"):
            return line.split(":", 1)[1].strip().strip("`") or "manual"
    return "manual"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--lane", default="")
    parser.add_argument("--prototype-source", default="[Figma Make URL / export reference]")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    contract = json.loads((repo / "core" / "contract.yaml").read_text(encoding="utf-8"))
    paths = contract["paths"]

    lane_state_path = repo / render_path(paths["tool_lane_state"], slug=args.slug, date=args.date, module=args.module)
    lane = args.lane or detect_lane(lane_state_path)
    report_path = Path(args.output) if args.output else repo / render_path(paths["prototype_conformance_report"], slug=args.slug, date=args.date, module=args.module)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    contract_path = repo / render_path(paths["screen_field_contract"], slug=args.slug, date=args.date, module=args.module)
    screen_ids: list[str] = []
    if contract_path.is_file():
        screen_ids = re.findall(r"^\s*-\s*screen_id:\s*([A-Z0-9-]+)\s*$", contract_path.read_text(encoding="utf-8"), flags=re.MULTILINE)

    lines = [
        "# Báo cáo conformance prototype (Prototype Conformance Report)",
        "",
        "## Summary",
        "",
        f"- Lane: `{lane}`",
        "- Verdict: [pass / fail / blocked / needs-impact]",
        f"- Scope: `{args.module}`",
        f"- Source contract: `{render_path(paths['screen_field_contract'], slug=args.slug, date=args.date, module=args.module)}`",
        f"- Prototype source: {args.prototype_source}",
        "",
        "## Findings by screen",
        "",
        "| Screen ID | Verdict | Extra Fields | Missing Fields | State Drift | Validation Drift | Menu Drift | Needs Impact | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if screen_ids:
        for screen_id in screen_ids:
            lines.append(f"| {screen_id} | blocked | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |")
    else:
        lines.append("| SCR-01 | blocked | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | missing screen-field-contract input |")

    lines.extend(
        [
            "",
            "## Next action",
            "",
            "- Fix prototype and re-run conformance review, or",
            "- Route requirement drift through `ba-start impact`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "lane": lane,
                "report_path": report_path.relative_to(repo).as_posix() if report_path.is_relative_to(repo) else report_path.as_posix(),
                "screen_count": len(screen_ids),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
