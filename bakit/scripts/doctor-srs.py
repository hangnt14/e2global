#!/usr/bin/env python3
"""Run lightweight SRS canon guardrails for a module directory (new architecture)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_check(cmd: list[str]) -> dict[str, object]:
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    return {
        "cmd": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


import re

DATE_TOKEN_RE = re.compile(r"^(.+)-(\d{6}-\d{4})$")


def derive_slug_date_module(module_root: Path) -> tuple[str, str, str]:
    """Derive slug, date, module from module_root path convention.

    Expected: plans/{slug}-{date}/03_modules/{module}
    Date token format: YYMMDD-HHmm (e.g. 260528-1000)
    """
    module = module_root.name
    project_dir = module_root.parent.parent  # skip 03_modules
    m = DATE_TOKEN_RE.match(project_dir.name)
    if m:
        slug, date = m.group(1), m.group(2)
    else:
        # fallback: no date token found
        slug, date = project_dir.name, ""
    return slug, date, module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module_root", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--repo", default=".", help="Repo root path")
    args = parser.parse_args()

    module_root = args.module_root.resolve()
    repo = Path(args.repo).resolve()
    script_dir = Path(__file__).resolve().parent
    checks: list[dict[str, object]] = []

    slug, date, module = derive_slug_date_module(module_root)

    # Check userstories index
    checks.append(run_check([
        sys.executable, str(script_dir / "check-userstories-index.py"),
        "--repo", str(repo), "--slug", slug, "--date", date, "--module", module,
    ]))

    # Check usecases index
    checks.append(run_check([
        sys.executable, str(script_dir / "check-usecases-index.py"),
        "--repo", str(repo), "--slug", slug, "--date", date, "--module", module,
    ]))

    # Check ascii-screen index (with ASCII coverage)
    checks.append(run_check([
        sys.executable, str(script_dir / "check-ascii-screen-index.py"),
        "--repo", str(repo), "--slug", slug, "--date", date, "--module", module,
        "--require-ascii-current",
    ]))

    ascii_screen_root = module_root / "ascii-screen"
    if any(path.name != "index.md" for path in ascii_screen_root.glob("*.md")):
        checks.append(run_check([sys.executable, str(script_dir / "check-screen-behaviour.py"), str(ascii_screen_root)]))
        control_library = module_root.parent.parent / "02_backbone" / "control-type-library.md"
        ct_cmd = [sys.executable, str(script_dir / "check-control-type-compliance.py"), str(ascii_screen_root)]
        if control_library.exists():
            ct_cmd.extend(["--library", str(control_library)])
        checks.append(run_check(ct_cmd))
        checks.append(run_check([sys.executable, str(script_dir / "check-message-placement.py"), str(ascii_screen_root)]))

        common_rules = module_root.parent.parent / "02_backbone" / "common-rules.md"
        if common_rules.exists():
            checks.append(run_check([
                sys.executable, str(script_dir / "validate-cr-coverage.py"),
                str(ascii_screen_root),
                "--common-rules", str(common_rules),
            ]))

    term_cmd = [sys.executable, str(script_dir / "check-terminology-consistency.py"), str(module_root)]
    control_library = module_root.parent.parent / "02_backbone" / "control-type-library.md"
    if control_library.exists():
        term_cmd.extend(["--library", str(control_library)])
    checks.append(run_check(term_cmd))

    # Check srs source set
    checks.append(run_check([
        sys.executable, str(script_dir / "check-srs-source-set.py"),
        "--repo", str(repo), "--slug", slug, "--date", date, "--module", module,
    ]))

    # Check partial compile receipt
    checks.append(run_check([
        sys.executable, str(script_dir / "check-partial-srs-compile-receipt.py"),
        "--repo", str(repo), "--slug", slug, "--date", date, "--module", module,
    ]))

    # Check compiled SRS freshness
    checks.append(run_check([
        sys.executable, str(script_dir / "check-freshness.py"),
        "--repo", str(repo), "--slug", slug, "--date", date, "--module", module,
    ]))

    # Check source of truth
    checks.append(run_check([sys.executable, str(script_dir / "check-source-of-truth.py"), str(module_root)]))

    # Check template compliance (srs.md vs template)
    srs_path = module_root / "srs.md"
    if srs_path.exists():
        checks.append(run_check([
            sys.executable, str(script_dir / "check-srs-template-compliance.py"),
            "--srs", str(srs_path),
            "--repo", str(repo),
        ]))

    # Check backbone-module alignment
    checks.append(run_check([
        sys.executable, str(script_dir / "check-backbone-module-alignment.py"),
        "--repo", str(repo), "--slug", slug, "--date", date, "--module", module,
        "--scope", "general",
    ]))

    # Check shared traceability (warn-only)
    checks.append(run_check([
        sys.executable, str(script_dir / "check-shared-traceability.py"),
        "--repo", str(repo), "--slug", slug, "--date", date,
    ]))

    # Check shared rule/message registry
    checks.append(run_check([sys.executable, str(script_dir / "validate-shared-rule-message-registry.py"), "--module-root", str(module_root)]))

    compile_receipt = module_root / "srs-compile-receipt.json"
    receipt_status = "present" if compile_receipt.exists() else "missing"

    ok = all(int(check["returncode"]) == 0 for check in checks)
    result = {"module_root": str(module_root), "ok": ok, "compile_receipt": receipt_status, "checks": checks}

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(("PASS" if ok else "BLOCK") + f": {module_root}")
        for check in checks:
            if check["stdout"]:
                print(check["stdout"])
            if check["stderr"]:
                print(f"BLOCK: {check['stderr']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
