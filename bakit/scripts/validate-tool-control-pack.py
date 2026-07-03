#!/usr/bin/env python3
"""Validate AI wireframe tool control artifacts for a module."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_PROMPT_LINES = {
    "Do not add fields not listed",
    "Do not add screens not listed",
    "Do not change top-level navigation",
    "If a rule is missing, omit instead of inventing",
}

REQUIRED_UC_PROMPT_LINES = {
    "Do not add fields not listed",
    "Do not add screens not listed",
    "Do not change top-level navigation",
    "If a rule is missing, omit instead of inventing",
    "Do not modify any other element",
}


def render_path(template: str, *, slug: str, date: str, module: str) -> str:
    return (
        template.replace("{slug}", slug)
        .replace("{date}", date)
        .replace("{module_slug}", module)
        .replace("{group}", "*")
        .replace("{option}", "*")
    )


def read_contract(repo: Path) -> dict:
    return json.loads((repo / "core" / "contract.yaml").read_text(encoding="utf-8"))


def detect_lane(path: Path) -> str:
    if not path.is_file():
        return "manual"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- Selected lane:"):
            return line.split(":", 1)[1].strip().strip("`") or "manual"
    return "manual"


def issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--lane", default="")
    parser.add_argument("--output")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    contract = read_contract(repo)
    paths = contract["paths"]

    tool_lane_state = repo / render_path(paths["tool_lane_state"], slug=args.slug, date=args.date, module=args.module)
    lane = args.lane or detect_lane(tool_lane_state)

    result = {
        "status": "skip",
        "lane": lane,
        "module": args.module,
        "issues": [],
        "message": "",
    }

    if lane in {"manual", "not-applicable"}:
        result["message"] = f"TOOL_CONTROL_PACK_SKIP: lane={lane}"
    elif lane != "figma-make":
        result["status"] = "fail"
        result["issues"].append(issue("error", "unsupported_lane", f"Unsupported lane: {lane}"))
        result["message"] = f"TOOL_CONTROL_PACK_FAIL: lane={lane} unsupported"
    else:
        required_files = {
            "screen_field_contract": repo / render_path(paths["screen_field_contract"], slug=args.slug, date=args.date, module=args.module),
            "make_guidelines": repo / render_path(paths["make_guidelines"], slug=args.slug, date=args.date, module=args.module),
            "make_prompt_pack": repo / render_path(paths["make_prompt_pack"], slug=args.slug, date=args.date, module=args.module),
            "prototype_conformance_checklist": repo / render_path(paths["prototype_conformance_checklist"], slug=args.slug, date=args.date, module=args.module),
            "figma_make_shared_rules": repo / render_path(paths["figma_make_shared_rules"], slug=args.slug, date=args.date, module=""),
            "figma_make_shared_prompt_skeleton": repo / render_path(paths["figma_make_shared_prompt_skeleton"], slug=args.slug, date=args.date, module=""),
            "figma_make_shared_component_contracts": repo / render_path(paths["figma_make_shared_component_contracts"], slug=args.slug, date=args.date, module=""),
        }
        for key, path in required_files.items():
            if not path.is_file():
                result["issues"].append(issue("error", "missing_artifact", f"{key} missing: {path.relative_to(repo).as_posix()}"))

        contract_path = required_files["screen_field_contract"]
        if contract_path.is_file():
            text = contract_path.read_text(encoding="utf-8")
            for token in (
                "artifact_set:",
                "shared_constraints:",
                "screens:",
                "screen_id:",
                "fields:",
                "states:",
                "constraints:",
                "trace:",
                "no_extra_fields: true",
                "no_nav_changes: true",
            ):
                if token not in text:
                    result["issues"].append(issue("error", "screen_field_contract_token_missing", f"Missing token '{token}' in screen field contract"))
            screen_ids = re.findall(r"^\s*-\s*screen_id:\s*([A-Z0-9-]+)\s*$", text, flags=re.MULTILINE)
            if not screen_ids:
                result["issues"].append(issue("error", "screen_field_contract_no_screens", "No screen_id entries found"))

        prompt_pack_path = required_files["make_prompt_pack"]
        if prompt_pack_path.is_file():
            prompt_text = prompt_pack_path.read_text(encoding="utf-8")
            for line in REQUIRED_PROMPT_LINES:
                if line not in prompt_text:
                    result["issues"].append(issue("error", "make_prompt_pack_missing_negative", f"Missing prompt constraint: {line}"))

            uc_prompt_refs = re.findall(r"uc-[a-z0-9-]+-make-prompt\.md", prompt_text)
            uc_prompts_dir = prompt_pack_path.parent / "usecases"
            for ref in sorted(set(uc_prompt_refs)):
                uc_prompt_path = uc_prompts_dir / ref
                if not uc_prompt_path.is_file():
                    result["issues"].append(issue("error", "uc_prompt_referenced_missing", f"Referenced UC prompt not found: {uc_prompt_path.relative_to(repo).as_posix()}"))
                    continue
                uc_text = uc_prompt_path.read_text(encoding="utf-8")
                for line in REQUIRED_UC_PROMPT_LINES:
                    if line not in uc_text:
                        result["issues"].append(issue("error", "uc_prompt_missing_negative", f"UC prompt {ref} missing constraint: {line}"))

        checklist_path = required_files["prototype_conformance_checklist"]
        if checklist_path.is_file():
            checklist_text = checklist_path.read_text(encoding="utf-8")
            for token in ("field-allowlist", "navigation-lock", "states", "validation-surface", "terminology"):
                if token not in checklist_text:
                    result["issues"].append(issue("error", "checklist_missing_check", f"Missing checklist check: {token}"))

        errors = [entry for entry in result["issues"] if entry["severity"] == "error"]
        if errors:
            result["status"] = "fail"
            result["message"] = f"TOOL_CONTROL_PACK_FAIL: lane={lane} errors={len(errors)}"
        else:
            result["status"] = "pass"
            result["message"] = f"TOOL_CONTROL_PACK_PASS: lane={lane}"

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
