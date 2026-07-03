#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


def load_budget(root: Path) -> dict:
    budget_doc = root / "core" / "token-budget.md"
    text = budget_doc.read_text(encoding="utf-8")
    match = re.search(r"```json\n(.*?)\n```", text, re.S)
    if not match:
        raise SystemExit(f"Could not find JSON budget block in {budget_doc}")
    return json.loads(match.group(1))


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    budget = load_budget(root)
    failures = []

    def size_of(rel_path: str) -> int:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing path: {rel_path}")
            return 0
        return path.stat().st_size

    print("Token budget check")
    print("")

    for item in budget.get("files", []):
        actual = size_of(item["path"])
        maximum = item["max"]
        baseline = item["baseline"]
        label = item.get("label", item["path"])
        status = "fail" if actual > maximum else "ok"
        if status == "fail":
            failures.append(f"file budget exceeded: {item['path']} actual={actual} max={maximum}")
        print(f"- [{status}] {label}: {actual} bytes (baseline {baseline}, max {maximum})")

    print("")

    for bundle in budget.get("bundles", []):
        actual = sum(size_of(path) for path in bundle["paths"])
        maximum = bundle["max"]
        baseline = bundle["baseline"]
        status = "fail" if actual > maximum else "ok"
        if status == "fail":
            failures.append(f"bundle budget exceeded: {bundle['name']} actual={actual} max={maximum}")
        print(f"- [{status}] {bundle['name']}: {actual} bytes (baseline {baseline}, max {maximum})")

    if failures:
        print("")
        print("Budget failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("")
    print("Token budget checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
