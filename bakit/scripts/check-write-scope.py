#!/usr/bin/env python3
"""Best-effort write-scope guardrail for BA-kit command outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ALLOWED_SUFFIXES = {
    "frd": (
        "/frd.md",
    ),
    "stories": (
        "/userstories/",
    ),
    "backbone": (
        "/02_backbone/",
    ),
    "srs": (
        "/usecases/",
        "/ascii-screen/",
        "/srs/",
        "/srs.md",
        "/srs-compile-receipt.json",
        "/screen-field-contract.yaml",
    ),
    "wireframes": (),
    "figma-sync": (
        "/figma-sync/figma-sync-report.md",
        "/figma-sync/figma-mismatch-report.md",
    ),
    "package": (
        "/04_compiled/",
        "/package-snapshot.md",
    ),
    "qc-export": (
        "/04_compiled/qc-kit",
    ),
}

FORBIDDEN_BY_COMMAND = {
    "figma-sync": (
        "/srs.md",
        "/ascii-screen/",
        "/usecases/",
        "/userstories/",
        "/shared-shell-contract.md",
    ),
    "package": (
        "/ascii-screen/",
        "/usecases/",
        "/userstories/",
        "/srs/",
        "/shared-shell-contract.md",
    ),
    "srs": (
        "/userstories/",
    ),
    "qc-export": (
        "/usecases/",
        "/ascii-screen/",
        "/userstories/",
        "/srs/",
        "/02_backbone/",
    ),
}


def normalized(path: Path) -> str:
    return "/" + path.as_posix().lstrip("./")


def _token_matches(token: str, value: str) -> bool:
    """Boundary-aware path match: token /04_compiled/qc-kit matches
    /plans/.../04_compiled/qc-kit but not /plans/.../04_compiled/qc-kit-backup."""
    return (token.rstrip("/") + "/") in (value + "/")


def validate(command: str, paths: list[Path]) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    allowed = ALLOWED_SUFFIXES.get(command)
    forbidden = FORBIDDEN_BY_COMMAND.get(command, ())

    if allowed is None:
        warnings.append(f"unknown command; no write-scope matrix entry: {command}")
        allowed = ()

    for path in paths:
        value = normalized(path)
        if any(_token_matches(t, value) for t in forbidden):
            errors.append(f"{path}: forbidden write for command {command}")
            continue
        if allowed and not any(_token_matches(t, value) for t in allowed):
            errors.append(f"{path}: outside allowed write scope for command {command}")

    return {"command": command, "errors": errors, "warnings": warnings, "ok": not errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = validate(args.command, args.paths)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(("PASS" if result["ok"] else "BLOCK") + f": {args.command}")
        for error in result["errors"]:
            print(f"BLOCK: {error}")
        for warning in result["warnings"]:
            print(f"WARN: {warning}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
