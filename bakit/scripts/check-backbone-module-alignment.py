#!/usr/bin/env python3
"""Validate backbone-module alignment before module-mutating writes.

Checks that the module exists in backbone, actors are known, and
terminology matches shared definitions. Emits BACKBONE_ALIGNMENT_FAIL
with a scope code when alignment fails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from guardrail_common import load_contract, render_path

MODULE_SECTION_RE = re.compile(r"(?:^|\n)#{1,3}\s+.*\b{module}\b", re.IGNORECASE)
ACTOR_RE = re.compile(r"\bactor[s]?\b.*?:\s*(.+)", re.IGNORECASE)


def backbone_text(repo: Path, contract: dict, *, slug: str, date: str) -> str:
    path = repo / render_path(contract["paths"]["backbone"], slug=slug, date=date, module="")
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def shared_definitions_text(repo: Path, contract: dict, *, slug: str, date: str) -> str:
    path = repo / render_path(contract["paths"]["shared_definitions"], slug=slug, date=date, module="")
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def check_module_in_backbone(backbone: str, module: str) -> bool:
    pattern = re.compile(rf"\b{re.escape(module)}\b", re.IGNORECASE)
    return bool(pattern.search(backbone))


def check_actors(backbone: str, actors: list[str]) -> list[str]:
    """Return actors not found in backbone text."""
    missing = []
    for actor in actors:
        if actor and not re.search(re.escape(actor), backbone, re.IGNORECASE):
            missing.append(actor)
    return missing


def check_terms(backbone: str, definitions: str, terms: list[str]) -> list[str]:
    """Return terms not found in backbone or shared definitions."""
    combined = backbone + "\n" + definitions
    missing = []
    for term in terms:
        if term and not re.search(re.escape(term), combined, re.IGNORECASE):
            missing.append(term)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--scope", default="general",
                        choices=["general", "story_scope", "usecase_scope", "screen_scope",
                                 "srs_spec_scope", "flow_scope", "state_scope"],
                        help="Alignment scope being validated")
    parser.add_argument("--actors", default="", help="Comma-separated actor names to verify")
    parser.add_argument("--terms", default="", help="Comma-separated terms to verify against backbone/definitions")
    parser.add_argument("--output", help="Write JSON result to this path")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    contract = load_contract(repo)

    backbone = backbone_text(repo, contract, slug=args.slug, date=args.date)
    definitions = shared_definitions_text(repo, contract, slug=args.slug, date=args.date)

    issues: list[dict] = []

    # Check module exists in backbone
    if not backbone:
        issues.append({"severity": "error", "code": "backbone_missing",
                       "message": "backbone.md not found; cannot validate alignment"})
    elif not check_module_in_backbone(backbone, args.module):
        issues.append({"severity": "error", "code": "module_not_in_backbone",
                       "message": f"Module '{args.module}' not found in backbone",
                       "block_code": f"BACKBONE_ALIGNMENT_FAIL: {args.scope}"})

    # Check actors
    if args.actors and backbone:
        actor_list = [a.strip() for a in args.actors.split(",") if a.strip()]
        missing_actors = check_actors(backbone, actor_list)
        if missing_actors:
            issues.append({"severity": "error", "code": "unknown_actors",
                           "message": f"Actors not found in backbone: {missing_actors}",
                           "block_code": f"BACKBONE_ALIGNMENT_FAIL: {args.scope}"})

    # Check terms
    if args.terms and (backbone or definitions):
        term_list = [t.strip() for t in args.terms.split(",") if t.strip()]
        missing_terms = check_terms(backbone, definitions, term_list)
        if missing_terms:
            issues.append({"severity": "error", "code": "unknown_terms",
                           "message": f"Terms not found in backbone or shared definitions: {missing_terms}",
                           "block_code": f"BACKBONE_ALIGNMENT_FAIL: {args.scope}"})

    errors = [i for i in issues if i["severity"] == "error"]
    block_codes = list({i["block_code"] for i in errors if "block_code" in i})

    result = {
        "status": "fail" if errors else "pass",
        "module": args.module,
        "scope": args.scope,
        "issues": issues,
        "block_codes": block_codes,
        "message": (
            f"{block_codes[0] if block_codes else 'BACKBONE_ALIGNMENT_FAIL'}: errors={len(errors)}"
            if errors
            else f"BACKBONE_ALIGNMENT_PASS: module={args.module} scope={args.scope}"
        ),
    }

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)

    if errors:
        print(result["message"], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
