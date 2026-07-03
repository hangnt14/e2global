#!/usr/bin/env python3
"""Compute runtime guardrail verdicts for hard-enforced BA commands."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from guardrail_common import (
    COMMAND_POLICIES,
    build_canonical_state_summary,
    classify_index_state,
    coerce_path_entries,
    dominant_state,
    load_contract,
)


def make_ok_message(command: str, index_names: list[str], current_count: int, allow_tokens: list[str], deny_tokens: list[str], mode: str) -> str:
    parts = [f"cmd={command}", f"mode={mode}"]
    if index_names:
        parts.append(f"idx={'+'.join(index_names)}")
        parts.append(f"current={current_count}")
    if allow_tokens:
        parts.append(f"allow={','.join(allow_tokens)}")
    if deny_tokens:
        parts.append(f"deny={','.join(deny_tokens)}")
    return "GUARDRAIL: " + " ".join(parts)


def make_block_message(command: str, reason: str, refresh_command: str) -> str:
    return f"GUARDRAIL_BLOCK: cmd={command} reason={reason} refresh={refresh_command}"

def make_refresh_command(index_key: str, *, slug: str, date: str, module: str, index_state: dict[str, str]) -> str:
    reason = index_state.get("reason", "")

    # Missing index entirely → bootstrap from source artifacts
    if reason == "index_missing":
        parts = [
            "python3 scripts/context-budget-bootstrap.py",
            "--repo .",
            f"--slug {slug}",
            f"--date {date}",
            f"--index-key {index_key}",
        ]
        if module and "{" not in module:
            parts.append(f"--module {module}")
        return " ".join(parts)

    # Stale / metadata issues / hash mismatch → re-validate existing index
    parts = [
        "python3 scripts/validate-index-quality.py",
        "--repo .",
        f"--index-key {index_key}",
        f"--slug {slug}",
        f"--date {date}",
    ]
    if module:
        parts.append(f"--module {module}")
    parts.append("--writeback")
    return " ".join(parts)


def _load_snapshot(repo: Path, contract: dict, *, slug: str, date: str) -> dict | None:
    """Load package snapshot manifest if present and parse its state."""
    snapshot_path_template = "plans/{slug}-{date}/02_backbone/package-snapshot.md"
    snapshot_rel = snapshot_path_template.replace("{slug}", slug).replace("{date}", date)
    snapshot_path = repo / snapshot_rel
    if not snapshot_path.exists():
        return None
    text = snapshot_path.read_text(encoding="utf-8")
    # Parse YAML frontmatter between --- delimiters
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        return None
    import re
    meta: dict = {}
    for line in lines[1:end]:
        m = re.match(r'^(\w+):\s*"?([^"]*)"?\s*$', line)
        if m:
            meta[m.group(1)] = m.group(2)
    meta["_path"] = snapshot_rel
    return meta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--command", choices=sorted(COMMAND_POLICIES), required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", default="")
    parser.add_argument("--feature", default="")
    parser.add_argument("--trace-id", default="")
    parser.add_argument("--heading", default="")
    parser.add_argument("--allow-escalation", action="store_true")
    parser.add_argument("--snapshot", action="store_true", help="Include package snapshot state in output")
    parser.add_argument("--output", help="Write JSON output to this path as well as stdout")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    plan_root = repo / f"plans/{args.slug}-{args.date}"
    contract = load_contract(repo)
    policy = COMMAND_POLICIES[args.command]

    index_states = {}
    for index_key in policy["required_indexes"]:
        index_states[index_key] = classify_index_state(
            repo=repo,
            contract=contract,
            index_key=index_key,
            slug=args.slug,
            date=args.date,
            module=args.module,
            feature=args.feature,
            trace_id=args.trace_id,
            heading=args.heading,
            require_extractable=args.command in {"frd", "stories"},
        )

    state_values = [data["state"] for data in index_states.values()] or ["current"]
    overall_state = dominant_state(state_values)

    allow_reads = coerce_path_entries(
        repo=repo,
        contract=contract,
        slug=args.slug,
        date=args.date,
        module=args.module,
        keys=policy["required_reads"],
    )
    deny_reads = coerce_path_entries(
        repo=repo,
        contract=contract,
        slug=args.slug,
        date=args.date,
        module=args.module,
        keys=policy["deny_reads"],
    )

    result = {
        "status": "ok",
        "command": args.command,
        "resolved_slug": args.slug,
        "resolved_date": args.date,
        "resolved_module": args.module or "",
        "guardrail_mode": policy["guardrail_mode"],
        "project_home_override": policy["project_home_override"],
        "action_guardrail": policy["action_guardrail"],
        "indexes": {
            key: {k: v for k, v in value.items() if k not in {"rows", "metadata"}}
            for key, value in index_states.items()
        },
        "allow_reads": allow_reads,
        "deny_reads": deny_reads,
        "excerpt_plan": "backbone_by_module" if args.command in {"frd", "stories"} else "",
        "message": "",
    }

    # Attach snapshot state for package/status/next or when --snapshot flag is set
    if args.command in {"package", "status", "next"} or args.snapshot:
        snapshot_meta = _load_snapshot(repo, contract, slug=args.slug, date=args.date)
        if snapshot_meta:
            result["snapshot"] = {
                "state": snapshot_meta.get("snapshot_state", "unknown"),
                "generated_at": snapshot_meta.get("generated_at", ""),
                "path": snapshot_meta.get("_path", ""),
            }
        else:
            result["snapshot"] = {"state": "absent", "path": ""}

    if args.command in {"status", "next"}:
        result.update(
            build_canonical_state_summary(
                repo,
                contract,
                slug=args.slug,
                date=args.date,
                module=args.module,
                command=args.command,
            )
        )

    # Package receipt validation: scan all modules, require receipt + template_compliance
    if args.command == "package" and result["status"] == "ok":
        import json as _json
        modules_dir = plan_root / "03_modules"
        if modules_dir.is_dir():
            scan_issues = []
            for mod_dir in sorted(modules_dir.iterdir()):
                if not mod_dir.is_dir():
                    continue
                srs_md = mod_dir / "srs.md"
                receipt_json = mod_dir / "srs-compile-receipt.json"
                if not srs_md.exists():
                    continue
                if not receipt_json.exists():
                    scan_issues.append(f"{mod_dir.name}: receipt missing")
                    continue
                try:
                    receipt = _json.loads(receipt_json.read_text(encoding="utf-8"))
                except Exception:
                    scan_issues.append(f"{mod_dir.name}: receipt invalid JSON")
                    continue
                tc = receipt.get("template_compliance")
                if tc is not True:
                    scan_issues.append(f"{mod_dir.name}: template_compliance={tc}")
                # Validate source hashes
                source_hashes = receipt.get("source_hashes", {})
                for rel_path, expected_hash in source_hashes.items():
                    fpath = mod_dir / rel_path
                    if not fpath.exists():
                        scan_issues.append(f"{mod_dir.name}: source missing {rel_path}")
                        continue
                    actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
                    if actual_hash != expected_hash:
                        scan_issues.append(f"{mod_dir.name}: source hash mismatch {rel_path}")
            if scan_issues:
                result["status"] = "block"
                result["reason"] = "package_receipt_validation_failed"
                result["module_issues"] = scan_issues
                rc = make_refresh_command(
                    "package",
                    slug=args.slug,
                    date=args.date,
                    module="",
                    index_state={"state": "missing", "reason": "Compile modules first"},
                )
                result["refresh_command"] = rc
                result["message"] = make_block_message(args.command, "receipt_validation", rc)

    if index_states and overall_state != "current" and not args.allow_escalation:
        reason = next(
            f"{key}_{value['state']}"
            for key, value in index_states.items()
            if value["state"] != "current"
        )
        blocked_key = next(key for key, value in index_states.items() if value["state"] != "current")
        refresh_command = make_refresh_command(
            blocked_key,
            slug=args.slug,
            date=args.date,
            module=args.module,
            index_state=index_states[blocked_key],
        )
        result["status"] = "block"
        result["reason"] = reason
        result["refresh_command"] = refresh_command
        result["message"] = make_block_message(args.command, reason, refresh_command)
    elif result["status"] == "ok" and index_states and overall_state != "current" and args.allow_escalation:
        result["status"] = "warn"
        result["reason"] = f"escalation_required:{overall_state}"
        result["message"] = (
            f"GUARDRAIL_WARN: cmd={args.command} mode={policy['guardrail_mode']} escalation={overall_state}"
        )
    elif result["status"] == "ok":
        allow_tokens = [Path(path).name if "/" in path else path for path in allow_reads if not path.endswith(".md") or "index" in path or path.endswith("plan.md")]
        deny_tokens = [Path(path).stem for path in deny_reads]
        result["message"] = make_ok_message(
            args.command,
            list(index_states.keys()),
            sum(1 for data in index_states.values() if data["state"] == "current"),
            allow_tokens,
            deny_tokens,
            policy["guardrail_mode"],
        )

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
