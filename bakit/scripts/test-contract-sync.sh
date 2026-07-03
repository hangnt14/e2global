#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

legacy_hits="$(
  cd "${ROOT_DIR}" &&
    if command -v rg >/dev/null 2>&1; then
      rg -n "artifact-contract\\.md|plans/reports/final|plans/reports/drafts|plans/\\{date\\}-\\{slug\\}" \
        AGENTS.md GEMINI.md CLAUDE.md skills core scripts codex templates \
        --glob '!core/contract.yaml' \
        --glob '!rules/ba-workflow.md' \
        --glob '!scripts/test-contract-sync.sh' \
        || true
    else
      grep -rn -E "artifact-contract\.md|plans/reports/final|plans/reports/drafts|plans/\{date\}-\{slug\}" \
        AGENTS.md GEMINI.md CLAUDE.md skills core scripts codex templates \
        --exclude='core/contract.yaml' \
        --exclude='rules/ba-workflow.md' \
        --exclude='scripts/test-contract-sync.sh' \
        || true
    fi
)"

if [[ -n "${legacy_hits}" ]]; then
  echo "Unexpected legacy contract references found:" >&2
  echo "${legacy_hits}" >&2
  exit 1
fi

python3 - "${ROOT_DIR}/templates/manifest.json" "${ROOT_DIR}/templates" <<'PY'
import json
import re
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
templates_dir = Path(sys.argv[2])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
heading_re = re.compile(r"^(#{1,6})\s+(.+)$")

for template_name, info in manifest.items():
    template_path = templates_dir / template_name
    if not template_path.exists():
        raise SystemExit(f"Missing template from manifest: {template_path}")
    raw_lines = template_path.read_text(encoding="utf-8").splitlines()
    headings = {
        line.strip()
        for line in raw_lines
        if heading_re.match(line.strip())
    }
    for group_name, group_info in info.get("groups", {}).items():
        for heading in group_info.get("headings", []):
            if template_path.suffix in {".yaml", ".yml"}:
                if heading not in {line.strip() for line in raw_lines}:
                    raise SystemExit(
                        f"Manifest heading not found: template={template_name} group={group_name} heading={heading}"
                    )
                continue
            if heading not in headings:
                raise SystemExit(
                    f"Manifest heading not found: template={template_name} group={group_name} heading={heading}"
                )
PY

python3 - "${ROOT_DIR}/core/contract.yaml" <<'PY'
import json
import sys
from pathlib import Path

contract_path = Path(sys.argv[1])
contract = json.loads(contract_path.read_text(encoding="utf-8"))
paths = contract.get("paths", {})
commands = contract.get("commands", {})
required_paths = {
    "source_chunk_index",
    "backbone_index",
    "userstories_index",
    "userstory_item",
    "usecases_index",
    "usecase_item",
    "usecase_diagrams",
    "ascii_screen_index",
    "ascii_screen_item",
    "srs_spec",
    "srs_flows",
    "srs_states",
    "srs_erd",
    "srs_compile_receipt",
    "shared_traceability",
    "shared_staleness",
    "shared_definitions",
    "screen_field_contract",
    "common_rules",
    "message_list",
    "shared_rule_message_index",
    "tool_lane_state",
    "make_guidelines",
    "make_prompt_pack",
    "make_uc_prompt",
    "make_uc_change_log",
    "prototype_conformance_checklist",
    "prototype_conformance_report",
    "figma_make_shared_rules",
    "figma_make_shared_prompt_skeleton",
    "figma_make_shared_component_contracts",
}
missing_paths = sorted(required_paths - set(paths))
if missing_paths:
    raise SystemExit(f"Missing token optimization path(s): {', '.join(missing_paths)}")

required_outputs = {
    "intake": {"source_summary", "source_chunks_dir", "source_chunk_index"},
    "backbone": {"backbone", "backbone_index", "common_rules", "message_list", "shared_rule_message_index"},
    "stories": {"userstories_index", "userstory_item"},
    "srs": {"srs", "srs_spec", "srs_compile_receipt", "screen_field_contract", "usecases_index", "ascii_screen_index"},
    "wireframes": set(),
}
for command, expected in required_outputs.items():
    outputs = set(commands.get(command, {}).get("outputs", []))
    missing = sorted(expected - outputs)
    if missing:
        raise SystemExit(
            f"Command '{command}' missing token optimization output(s): {', '.join(missing)}"
        )

profiles = contract.get("artifact_profiles", {})
allowed_profiles = {"user_facing", "agent_facing", "machine_facing"}
required_profile_keys = {
    "source_manifest",
    "source_summary",
    "source_chunk_index",
    "project_home",
    "collab_home",
    "module_home",
    "review_packet",
    "intake",
    "plan",
    "options_index",
    "option_item",
    "options_comparison",
    "backbone",
    "backbone_index",
    "frd",
    "userstories_index",
    "userstory_item",
    "usecases_index",
    "usecase_item",
    "usecase_diagrams",
    "ascii_screen_index",
    "ascii_screen_item",
    "srs_spec",
    "srs_flows",
    "srs_states",
    "srs_erd",
    "srs",
    "srs_compile_receipt",
    "shared_traceability",
    "shared_staleness",
    "shared_definitions",
    "screen_field_contract",
    "common_rules",
    "message_list",
    "shared_rule_message_index",
    "tool_lane_state",
    "make_guidelines",
    "make_prompt_pack",
    "make_uc_prompt",
    "make_uc_change_log",
    "prototype_conformance_checklist",
    "prototype_conformance_report",
    "figma_make_shared_rules",
    "figma_make_shared_prompt_skeleton",
    "figma_make_shared_component_contracts",
    "compiled_frd",
    "compiled_srs",
    "design_doc",
    "project_memory",
    "memory_index",
    "memory_log",
    "memory_hot_vocabulary",
    "memory_hot_decisions",
    "memory_hot_pushback",
    "memory_module_warm",
}
missing_profiles = sorted(required_profile_keys - set(profiles))
if missing_profiles:
    raise SystemExit(f"Missing artifact profile(s): {', '.join(missing_profiles)}")
invalid_profiles = {
    key: value
    for key, value in profiles.items()
    if value not in allowed_profiles
}
if invalid_profiles:
    details = ", ".join(f"{key}={value}" for key, value in sorted(invalid_profiles.items()))
    raise SystemExit(f"Invalid artifact profile value(s): {details}")
unknown_profile_keys = sorted(set(profiles) - set(paths))
if unknown_profile_keys:
    raise SystemExit(f"Artifact profiles reference unknown path key(s): {', '.join(unknown_profile_keys)}")

expected_profiles = {
    "source_manifest": "machine_facing",
    "compiled_frd": "user_facing",
    "compiled_srs": "user_facing",
    "backbone_index": "agent_facing",
    "userstories_index": "agent_facing",
    "usecases_index": "agent_facing",
    "ascii_screen_index": "agent_facing",
    "srs_compile_receipt": "machine_facing",
    "shared_traceability": "agent_facing",
    "shared_staleness": "agent_facing",
    "shared_definitions": "agent_facing",
    "screen_field_contract": "machine_facing",
    "common_rules": "agent_facing",
    "message_list": "agent_facing",
    "shared_rule_message_index": "agent_facing",
    "tool_lane_state": "machine_facing",
    "make_guidelines": "agent_facing",
    "make_prompt_pack": "agent_facing",
    "make_uc_prompt": "agent_facing",
    "make_uc_change_log": "agent_facing",
    "prototype_conformance_checklist": "agent_facing",
    "prototype_conformance_report": "user_facing",
    "figma_make_shared_rules": "agent_facing",
    "figma_make_shared_prompt_skeleton": "agent_facing",
    "figma_make_shared_component_contracts": "agent_facing",
}
for key, expected in expected_profiles.items():
    actual = profiles.get(key)
    if actual != expected:
        raise SystemExit(f"Artifact profile mismatch for {key}: expected {expected}, got {actual}")

activation = contract.get("activation", {})
signals = set(activation.get("signals", {}))
thresholds = activation.get("thresholds", {})
operators = {"gte", "equals"}


def validate_rule(rule, path):
    if not isinstance(rule, dict):
        raise SystemExit(f"Activation threshold rule must be an object: {path}")

    branch_keys = {"any_of", "all_of"} & set(rule)
    if branch_keys:
        if len(branch_keys) != 1 or len(rule) != 1:
            raise SystemExit(f"Activation threshold branch must contain only one branch key: {path}")
        key = next(iter(branch_keys))
        children = rule[key]
        if not isinstance(children, list) or not children:
            raise SystemExit(f"Activation threshold branch must be a non-empty list: {path}.{key}")
        for index, child in enumerate(children):
            validate_rule(child, f"{path}.{key}[{index}]")
        return

    required = {"signal", "operator", "value"}
    if set(rule) != required:
        raise SystemExit(f"Activation threshold leaf must contain exactly signal/operator/value: {path}")
    if rule["signal"] not in signals:
        raise SystemExit(f"Activation threshold references unknown signal '{rule['signal']}': {path}")
    if rule["operator"] not in operators:
        raise SystemExit(f"Activation threshold uses unsupported operator '{rule['operator']}': {path}")
    if rule["operator"] == "gte" and (not isinstance(rule["value"], (int, float)) or isinstance(rule["value"], bool)):
        raise SystemExit(f"Activation threshold gte value must be numeric: {path}")


for level in ("modular", "program"):
    if level not in thresholds:
        raise SystemExit(f"Missing activation threshold level: {level}")
    validate_rule(thresholds[level], f"activation.thresholds.{level}")
PY

python3 - "${ROOT_DIR}/templates/manifest.json" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
required_templates = {
    "source-chunk-index-template.md",
    "backbone-index-template.md",
    "userstories-index-template.md",
    "userstory-item-template.md",
    "usecases-index-template.md",
    "usecase-item-template.md",
    "usecase-diagrams-template.md",
    "ascii-screen-index-template.md",
    "ascii-screen-template.md",
    "srs-spec-template.md",
    "srs-flows-template.md",
    "srs-states-template.md",
    "srs-erd-template.md",
    "change-request-template.md",
    "impact-report-template.md",
    "shared-traceability-template.md",
    "shared-staleness-template.md",
    "shared-definitions-template.md",
    "screen-field-contract-template.yaml",
    "common-rules-template.md",
    "message-list-template.md",
    "shared-rule-message-index-template.md",
    "tool-lane-state-template.md",
    "figma-make-shared-rules-template.md",
    "figma-make-shared-prompt-skeleton-template.md",
    "figma-make-shared-component-contracts-template.md",
    "make-guidelines-template.md",
    "make-prompt-pack-template.md",
    "figma-make-uc-prompt-template.md",
    "figma-make-uc-change-log-template.md",
    "prototype-conformance-checklist-template.md",
    "prototype-conformance-report-template.md",
}
missing = sorted(required_templates - set(manifest))
if missing:
    raise SystemExit(f"Missing token optimization template(s): {', '.join(missing)}")
PY

python3 - "${ROOT_DIR}/templates/manifest.json" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
required_reverse_templates = {
    "reverse-baseline-lock-template.md",
    "reverse-index-template.md",
}
missing = sorted(required_reverse_templates - set(manifest))
if missing:
    raise SystemExit(f"Missing reverse lane template(s): {', '.join(missing)}")
PY

python3 - "${ROOT_DIR}/core/contract.yaml" <<'PY'
import json
import sys
from pathlib import Path

contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
paths = contract.get("paths", {})
commands = contract.get("commands", {})
profiles = contract.get("artifact_profiles", {})
reverse_section = contract.get("reverse", {})

# Verify reverse path keys exist
required_reverse_paths = {
    "reverse_root",
    "reverse_baseline_lock",
    "reverse_index",
    "reverse_focus_excerpts",
    "reverse_evidence_ledger",
    "reverse_drift_state",
    "reverse_read_manifest",
    "behavior_reverse",
}
missing_paths = sorted(required_reverse_paths - set(paths))
if missing_paths:
    raise SystemExit(f"Missing reverse lane path(s): {', '.join(missing_paths)}")

# Verify reverse commands exist
required_reverse_commands = {
    "reverse",
    "reverse_status",
    "reverse_refresh",
    "reverse_promote",
    "reverse_impact",
}
missing_commands = sorted(required_reverse_commands - set(commands))
if missing_commands:
    raise SystemExit(f"Missing reverse lane command(s): {', '.join(missing_commands)}")

# Verify reverse artifact profiles
required_reverse_profiles = {
    "reverse_baseline_lock": "machine_facing",
    "reverse_index": "agent_facing",
    "reverse_focus_excerpts": "agent_facing",
    "reverse_evidence_ledger": "agent_facing",
    "reverse_drift_state": "machine_facing",
    "reverse_read_manifest": "machine_facing",
}
for key, expected in required_reverse_profiles.items():
    actual = profiles.get(key)
    if actual != expected:
        raise SystemExit(
            f"Reverse artifact profile mismatch for {key}: expected {expected}, got {actual}"
        )

# Verify reverse section exists and canonical=false
if not reverse_section:
    raise SystemExit("Missing 'reverse' section in contract.yaml")
if reverse_section.get("canonical") is not False:
    raise SystemExit("contract.yaml reverse.canonical must be false")
if not reverse_section.get("evidence_zone"):
    raise SystemExit("contract.yaml reverse.evidence_zone must be true")

# Verify reverse artifacts are NOT in source_of_truth_order
sot_order = contract.get("source_of_truth_order", [])
reverse_keys = set(required_reverse_profiles.keys())
sot_violations = sorted(reverse_keys & set(sot_order))
if sot_violations:
    raise SystemExit(
        f"Reverse artifact(s) must not appear in source_of_truth_order: {', '.join(sot_violations)}"
    )

# Verify behavior_shards entries for reverse commands
shards = contract.get("behavior_shards", {})
for cmd in required_reverse_commands:
    if cmd not in shards:
        raise SystemExit(f"Missing behavior_shards entry for reverse command: {cmd}")
    if "behavior_reverse" not in shards[cmd]:
        raise SystemExit(
            f"behavior_shards.{cmd} must include behavior_reverse"
        )

print("Reverse lane contract checks passed.")
PY

python3 - "${ROOT_DIR}/templates" <<'PY'
import sys
from pathlib import Path

templates_dir = Path(sys.argv[1])
max_bytes = {
    "source-chunk-index-template.md": 1800,
    "backbone-index-template.md": 1800,
    "userstories-index-template.md": 2200,
    "usecases-index-template.md": 2200,
    "ascii-screen-index-template.md": 2200,
    "shared-rule-message-index-template.md": 2200,
    "project-memory-index-template.md": 2600,
    "project-memory-template.md": 2600,
    "project-memory-hot-canonical-vocabulary-template.md": 2200,
    "project-memory-hot-approved-decisions-template.md": 2200,
    "project-memory-hot-pushback-triggers-template.md": 2200,
    "project-memory-module-template.md": 2200,
    "review-packet-template.md": 2600,
    "sub-agent-handoff-template.md": 2600,
}
required_tokens = {
    "source-chunk-index-template.md": ["index_type", "source_artifact", "generated_at", "stale_status"],
    "backbone-index-template.md": ["index_type", "source_artifact", "generated_at", "stale_status", "validated_at", "validated_by"],
    "userstories-index-template.md": ["index_type", "source_artifact", "generated_at", "stale_status", "validated_at", "validated_by"],
    "usecases-index-template.md": ["index_type", "source_artifact", "generated_at", "stale_status", "validated_at", "validated_by"],
    "ascii-screen-index-template.md": ["index_type", "source_artifact", "generated_at", "stale_status", "validated_at", "validated_by"],
    "shared-rule-message-index-template.md": ["index_type", "source_common_rules", "source_message_list", "generated_at", "stale_status", "validated_at", "validated_by"],
}
for name, limit in max_bytes.items():
    path = templates_dir / name
    if not path.exists():
        raise SystemExit(f"Missing compact internal template: {name}")
    size = len(path.read_bytes())
    if size > limit:
        raise SystemExit(f"Internal template too large: {name} actual={size} max={limit}")
for name, tokens in required_tokens.items():
    text = (templates_dir / name).read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        raise SystemExit(f"Internal template missing freshness token(s): {name}: {', '.join(missing)}")
PY

python3 - "${ROOT_DIR}" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
checks = {
    "core/contract-behavior.md": ["paths.backbone_index", "paths.userstories_index", "paths.ascii_screen_index"],
    "skills/ba-start/steps/backbone.md": ["paths.backbone_index"],
    "skills/ba-start/steps/frd.md": ["paths.backbone_index"],
    "skills/ba-start/steps/stories.md": ["paths.backbone_index", "paths.userstories_index"],
    "skills/ba-start/steps/srs.md": ["paths.backbone_index", "paths.userstories_index", "paths.design_doc"],
    "skills/ba-start/steps/srs-core.md": ["validate-navigation-consistency.py", "MENU_SCHEMA_GAP", "paths.screen_field_contract"],
    "skills/ba-start/steps/srs-assembly.md": ["validate-navigation-consistency.py", "MENU_SCHEMA_MISMATCH"],
    "skills/ba-start/steps/wireframes.md": ["paths.ascii_screen_index", "ASCII"],
    "skills/ba-start/steps/package.md": ["paths.backbone_index", "paths.userstories_index", "paths.usecases_index"],
    "skills/ba-start/steps/impact.md": ["affected_node_ids", "owner_artifact", "stale_artifacts", "read_escalation", "screen_field_contract", "tool_lane_state"],
    "skills/ba-start/steps/reverse.md": ["blocking HITL gate", "unverifiable_in_v1", "source files"],
    "skills/ba-start/steps/reverse-status.md": ["reverse_baseline_lock", "stale_status"],
    "skills/ba-start/steps/reverse-impact.md": ["as_built_drift", "future_state_request", "mixed_change"],
}
for rel_path, tokens in checks.items():
    text = (root / rel_path).read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        raise SystemExit(f"{rel_path} missing index-first token(s): {', '.join(missing)}")
PY

SOURCE_FIXTURE="${TMP_DIR}/large-source.md"
{
  printf '# Large Source\n\n'
  for i in $(seq 1 24); do
    printf '## Section %02d\n\n' "${i}"
    printf 'Requirement %02d explains actor behavior, validation rules, workflow constraints, and reporting expectations for the BA source extraction test.\n\n' "${i}"
  done
} >"${SOURCE_FIXTURE}"

SOURCE_CACHE_ROOT="${TMP_DIR}/source-cache/{source_hash}"
SOURCE_EXTRACT_MANIFEST="${TMP_DIR}/source-extract-manifest.json"
python3 "${ROOT_DIR}/scripts/source-extract.py" "${SOURCE_FIXTURE}" \
  --cache-root "${SOURCE_CACHE_ROOT}" \
  --chunk-chars 900 >"${SOURCE_EXTRACT_MANIFEST}"
SOURCE_CACHE_DIR="$(python3 - "${SOURCE_EXTRACT_MANIFEST}" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(manifest["cache_dir"])
PY
)"
if [[ ! -f "${SOURCE_CACHE_DIR}/chunk-index.md" ]]; then
  echo "Missing source chunk index: ${SOURCE_CACHE_DIR}/chunk-index.md" >&2
  exit 1
fi

python3 -m py_compile \
  "${ROOT_DIR}/scripts/guardrail_common.py" \
  "${ROOT_DIR}/scripts/guardrail-preflight.py" \
  "${ROOT_DIR}/scripts/guardrail-build-excerpts.py" \
  "${ROOT_DIR}/scripts/guardrail-audit.py" \
  "${ROOT_DIR}/scripts/validate-index-quality.py" \
  "${ROOT_DIR}/scripts/source-extract.py" \
  "${ROOT_DIR}/scripts/context-budget.py" \
  "${ROOT_DIR}/scripts/design-snapshot.py" \
  "${ROOT_DIR}/scripts/validate-tool-control-pack.py" \
  "${ROOT_DIR}/scripts/generate-prototype-conformance-report.py" \
  "${ROOT_DIR}/scripts/validate-navigation-consistency.py" \
  "${ROOT_DIR}/scripts/stitch-state.py" \
  "${ROOT_DIR}/scripts/runtime-parity-normalize.py" \
  "${ROOT_DIR}/scripts/reverse_guardrail_common.py" \
  "${ROOT_DIR}/scripts/reverse-preflight.py" \
  "${ROOT_DIR}/scripts/reverse-validate-index.py" \
  "${ROOT_DIR}/scripts/reverse-build-excerpts.py" \
  "${ROOT_DIR}/scripts/reverse-trace-audit.py" \
  "${ROOT_DIR}/scripts/reverse-drift-check.py" \
  "${ROOT_DIR}/scripts/reverse-read-audit.py"

CONTEXT_BUDGET_OUTPUT="$(
  python3 "${ROOT_DIR}/scripts/context-budget.py" --repo "${ROOT_DIR}" --command status
)"
if [[ "${CONTEXT_BUDGET_OUTPUT}" != *"| Profile |"* ]]; then
  echo "context-budget output missing Profile column" >&2
  exit 1
fi

bash -n "${ROOT_DIR}/scripts/ba-kit"
bash -n "${ROOT_DIR}/scripts/check-token-budget.sh"
bash -n "${ROOT_DIR}/install.sh"
bash -n "${ROOT_DIR}/scripts/install-codex-ba-kit.sh"
bash -n "${ROOT_DIR}/scripts/install-antigravity-ba-kit.sh"
bash -n "${ROOT_DIR}/scripts/install-plantuml.sh"
bash -n "${ROOT_DIR}/scripts/generate-codex-assets.sh"
bash -n "${ROOT_DIR}/scripts/test-activation-thresholds.sh"
bash -n "${ROOT_DIR}/scripts/test-runtime-parity.sh"
bash -n "${ROOT_DIR}/scripts/test-index-quality.sh"
bash -n "${ROOT_DIR}/scripts/runtime-parity-adapter.sh"
bash -n "${ROOT_DIR}/scripts/test-runtime-install-smoke.sh"
bash -n "${ROOT_DIR}/scripts/test-navigation-consistency.sh"
bash "${ROOT_DIR}/scripts/check-token-budget.sh" >/dev/null
bash "${ROOT_DIR}/scripts/test-activation-thresholds.sh" >/dev/null
bash "${ROOT_DIR}/scripts/test-options-flow-contract.sh" >/dev/null
bash "${ROOT_DIR}/scripts/test-navigation-consistency.sh" >/dev/null
bash "${ROOT_DIR}/scripts/test-index-quality.sh" >/dev/null
bash "${ROOT_DIR}/scripts/test-runtime-parity.sh" --check-structure >/dev/null
bash "${ROOT_DIR}/scripts/test-runtime-parity.sh" >/dev/null

cp "${ROOT_DIR}/codex/skills/ba-start/SKILL.md" "${TMP_DIR}/ba-start.before"
bash "${ROOT_DIR}/scripts/generate-codex-assets.sh" >"${TMP_DIR}/generator.log"
cmp "${TMP_DIR}/ba-start.before" "${ROOT_DIR}/codex/skills/ba-start/SKILL.md" >/dev/null
bash "${ROOT_DIR}/scripts/test-runtime-install-smoke.sh" >/dev/null

echo "Contract sync checks passed."
