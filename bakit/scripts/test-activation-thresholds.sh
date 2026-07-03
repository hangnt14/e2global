#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "${ROOT_DIR}/core/contract.yaml" <<'PY'
import json
import sys
from pathlib import Path

contract_path = Path(sys.argv[1])
contract = json.loads(contract_path.read_text(encoding="utf-8"))
activation = contract["activation"]
thresholds = activation["thresholds"]


def eval_rule(rule, signals):
    if "any_of" in rule:
        return any(eval_rule(child, signals) for child in rule["any_of"])
    if "all_of" in rule:
        return all(eval_rule(child, signals) for child in rule["all_of"])

    signal = rule["signal"]
    operator = rule["operator"]
    expected = rule["value"]
    actual = signals[signal]

    if operator == "gte":
        return actual >= expected
    if operator == "equals":
        return actual == expected
    raise AssertionError(f"Unsupported operator: {operator}")


def resolve_level(signals):
    # Program intentionally wins over Modular when both match.
    if eval_rule(thresholds["program"], signals):
        return "Program"
    if eval_rule(thresholds["modular"], signals):
        return "Modular"
    return activation["default"]


cases = [
    (
        "compact fallback remains Base",
        {
            "module_count": 1,
            "owner_count": 1,
            "cross_module_dependency": False,
            "delegation_slice_count": 0,
        },
        "Base",
    ),
    (
        "one temporary delegation slice does not escalate alone",
        {
            "module_count": 1,
            "owner_count": 1,
            "cross_module_dependency": False,
            "delegation_slice_count": 1,
        },
        "Base",
    ),
    (
        "two modules activate Modular",
        {
            "module_count": 2,
            "owner_count": 1,
            "cross_module_dependency": False,
            "delegation_slice_count": 0,
        },
        "Modular",
    ),
    (
        "two owners activate Modular",
        {
            "module_count": 1,
            "owner_count": 2,
            "cross_module_dependency": False,
            "delegation_slice_count": 0,
        },
        "Modular",
    ),
    (
        "cross-module dependency activates Program",
        {
            "module_count": 1,
            "owner_count": 1,
            "cross_module_dependency": True,
            "delegation_slice_count": 0,
        },
        "Program",
    ),
    (
        "two delegation slices activate Program",
        {
            "module_count": 1,
            "owner_count": 1,
            "cross_module_dependency": False,
            "delegation_slice_count": 2,
        },
        "Program",
    ),
    (
        "multi-owner delegated work activates Program",
        {
            "module_count": 1,
            "owner_count": 2,
            "cross_module_dependency": False,
            "delegation_slice_count": 1,
        },
        "Program",
    ),
    (
        "Program wins over Modular",
        {
            "module_count": 2,
            "owner_count": 2,
            "cross_module_dependency": True,
            "delegation_slice_count": 0,
        },
        "Program",
    ),
]

for name, signals, expected in cases:
    actual = resolve_level(signals)
    if actual != expected:
        raise SystemExit(
            f"Activation threshold case failed: {name}: expected {expected}, got {actual}; signals={signals}"
        )

print(f"Activation threshold validation passed ({len(cases)} cases).")
PY
