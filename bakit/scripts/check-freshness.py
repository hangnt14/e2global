#!/usr/bin/env python3
"""Check compiled SRS freshness against source manifest (srs-compile-receipt.json).

Compares SHA256 hashes of current source files against the receipt.
Output: FRESH / STALE / MISSING.

Usage:
    python3 scripts/check-freshness.py --repo . --slug X --date YYMMDD-HHmm --module auth [--json] [--fix]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def load_contract(repo: Path) -> dict:
    contract_path = repo / "core" / "contract.yaml"
    if not contract_path.exists():
        home_contract = Path.home() / ".claude" / "core" / "contract.yaml"
        if home_contract.exists():
            contract_path = home_contract
    return json.loads(contract_path.read_text(encoding="utf-8"))


def render_path(template: str, slug: str, date: str, module: str) -> str:
    return template.replace("{slug}", slug).replace("{date}", date).replace("{module_slug}", module)


def sha256_file(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_freshness(repo: Path, slug: str, date: str, module: str) -> dict:
    contract = load_contract(repo)
    receipt_rel = render_path(contract["paths"]["srs_compile_receipt"], slug=slug, date=date, module=module)
    receipt_path = repo / receipt_rel
    module_root = receipt_path.parent

    if not receipt_path.exists():
        return {"status": "MISSING", "stale_files": [], "message": "No compile receipt found — run ba-start srs first"}

    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "MISSING", "stale_files": [], "message": "Receipt is corrupted"}

    source_manifest = _normalise_source_manifest(receipt, module_root)
    if not source_manifest:
        return {"status": "MISSING", "stale_files": [], "message": "Receipt has no source hashes"}

    stale_files = []
    for entry in source_manifest:
        source_path = Path(entry.get("path", ""))
        if not source_path.is_absolute():
            base = module_root if entry.get("base") == "module" else repo
            source_path = base / source_path
        if not source_path.exists():
            stale_files.append({"path": entry.get("path", "?"), "reason": "deleted"})
            continue
        current_hash = sha256_file(source_path)
        receipt_hash = entry.get("source_hash", "")
        if current_hash != receipt_hash:
            stale_files.append({
                "path": entry.get("path", "?"),
                "reason": "changed",
                "receipt_hash": receipt_hash[:12],
                "current_hash": current_hash[:12],
            })

    if stale_files:
        return {"status": "STALE", "stale_files": stale_files,
                "message": f"{len(stale_files)} source files changed since last compile"}
    return {"status": "FRESH", "stale_files": [], "message": "All sources match receipt — no re-compile needed"}


def _normalise_source_manifest(receipt: dict, module_root: Path) -> list[dict[str, str]]:
    """Support both current source_hashes receipts and older source_manifest receipts."""
    manifest = receipt.get("source_manifest")
    if isinstance(manifest, list):
        return [
            {
                "path": str(entry.get("path", "")),
                "source_hash": str(entry.get("source_hash", "")),
                "base": str(entry.get("base", "repo")),
            }
            for entry in manifest
            if isinstance(entry, dict)
        ]

    source_hashes = receipt.get("source_hashes")
    if isinstance(source_hashes, dict):
        return [
            {"path": str(path), "source_hash": str(source_hash), "base": "module"}
            for path, source_hash in source_hashes.items()
        ]

    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Check compiled SRS freshness")
    parser.add_argument("--repo", default=".", type=Path)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fix", action="store_true", help="Re-compile if stale")
    args = parser.parse_args()

    repo = args.repo.resolve()
    result = check_freshness(repo, args.slug, args.date, args.module)

    if args.fix and result["status"] == "STALE":
        print(f"STALE: {result['message']} — re-compiling...")
        compile_script = SCRIPT_DIR / "compile-srs.py"
        if compile_script.exists():
            subprocess.run([
                "python3", str(compile_script),
                "--repo", str(repo), "--slug", args.slug,
                "--date", args.date, "--module", args.module,
            ], check=False)
            result = check_freshness(repo, args.slug, args.date, args.module)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        status_icon = {"FRESH": "OK", "STALE": "WARN", "MISSING": "ERR"}
        print(f"[{status_icon.get(result['status'], '?')}] {result['status']}: {result['message']}")
        for f in result.get("stale_files", []):
            print(f"  - {f['path']}: {f['reason']}" + (f" ({f.get('receipt_hash')} → {f.get('current_hash')})" if f.get('receipt_hash') else ""))

    return 1 if result["status"] in ("STALE", "MISSING") else 0


if __name__ == "__main__":
    sys.exit(main())
