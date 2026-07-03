#!/usr/bin/env python3
"""Check canon-first SRS source-of-truth invariants."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate(module_root: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []

    if not module_root.exists():
        errors.append("module root does not exist")
        return {"module_root": str(module_root), "errors": errors, "warnings": warnings, "ok": False}
    if not module_root.is_dir():
        errors.append("module root is not a directory")
        return {"module_root": str(module_root), "errors": errors, "warnings": warnings, "ok": False}

    srs = module_root / "srs.md"
    receipt = module_root / "srs-compile-receipt.json"
    # New architecture: ascii-screen/ and usecases/ as folder-based canon
    ascii_screen = module_root / "ascii-screen"
    usecases = module_root / "usecases"
    srs_spec = module_root / "srs" / "spec.md"

    has_canon = (
        (ascii_screen.exists() and any(ascii_screen.glob("*.md")))
        or (usecases.exists() and any(usecases.glob("*.md")))
        or srs_spec.exists()
    )

    if srs.exists() and has_canon and not receipt.exists():
        errors.append("compiled srs.md exists with canon sources but srs-compile-receipt.json is missing")

    if receipt.exists() and not srs.exists():
        errors.append("srs-compile-receipt.json exists but compiled srs.md is missing")

    if srs.exists() and not has_canon:
        warnings.append("compiled srs.md exists without canon screen/usecase sources; legacy flow may be active")

    return {"module_root": str(module_root), "errors": errors, "warnings": warnings, "ok": not errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module_root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = validate(args.module_root)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(("PASS" if result["ok"] else "BLOCK") + f": {result['module_root']}")
        for error in result["errors"]:
            print(f"BLOCK: {error}")
        for warning in result["warnings"]:
            print(f"WARN: {warning}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
