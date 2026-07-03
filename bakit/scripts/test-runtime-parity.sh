#!/bin/sh
# test-runtime-parity.sh
#
# Parity harness entry point for BA-kit Adaptive Runtime Memory.
# Gates Phase 01/02/03 closure by verifying golden contracts exist and
# match fixture definitions across Claude Code, Codex, and Antigravity.
#
# Usage:
#   test-runtime-parity.sh [--list] [--check-structure] [--run-adapters] [--runtime <name>] [fixture-id]
#
# Adapter execution is opt-in because it may call external LLM runtimes.
# Claude Code and Codex use headless CLI adapters. Antigravity uses manual
# certification JSON until a deterministic headless adapter exists.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FIXTURES_DIR="$REPO_ROOT/tests/runtime-parity/fixtures"
GOLDENS_DIR="$REPO_ROOT/tests/runtime-parity/goldens"
ADAPTER_SCRIPT="$REPO_ROOT/scripts/runtime-parity-adapter.sh"
NORMALIZER_SCRIPT="$REPO_ROOT/scripts/runtime-parity-normalize.py"
RUN_ADAPTERS="${BA_KIT_RUNTIME_PARITY_RUN_ADAPTERS:-0}"
RUNTIME_FILTER="${BA_KIT_RUNTIME_PARITY_RUNTIME:-all}"
TARGET_FIXTURE="ALL"

# Fixture registry: id -> fixture_file:golden_file:description
# Add new fixtures here as phases progress.
FIXTURES="
f01:f01-summary-only-compact.md:g01-summary-only-compact.md:Summary-only compact mode (no shard tree)
f02:f02-freeform-routing-do.md:g02-freeform-routing-do.md:Freeform routing via ba-do → ba-impact
f03:f03-freeform-routing-impact.md:g03-freeform-routing-impact.md:Explicit ba-impact read scope and stop conditions
f04:f04-explicit-ba-start-step.md:g04-explicit-ba-start-step.md:Explicit ba-start backbone command
f05:f05-compact-fallback-missing-index.md:g05-compact-fallback-missing-index.md:Compact fallback on missing index.md
f06:f06-shard-index-routing.md:g06-shard-index-routing.md:Shard mode reads index first and targeted shards only
f07:f07-optional-log-excluded.md:g07-optional-log-excluded.md:Optional log exists but is excluded from default reads
f08:f08-approved-fileback-promotion.md:g08-approved-fileback-promotion.md:Approved file-back promotion requires authority and trace
f09:f09-activation-freeze-mismatch.md:g09-activation-freeze-mismatch.md:Runtime activation mismatch freezes to Base
f10:f10-freeform-router-explicit-fallback.md:g10-freeform-router-explicit-fallback.md:Freeform router mismatch falls back to explicit ba-start
f11:f11-multiba-governance-conflict.md:g11-multiba-governance-conflict.md:Multi-BA governance conflict escalates instead of mutating
f12:f12-packet-needs-repartition.md:g12-packet-needs-repartition.md:Underspecified packet returns NEEDS_REPARTITION without broad reads
f13:f13-options-step.md:g13-options-step.md:Explicit ba-start options generation command
f14:f14-next-recommends-options.md:g14-next-recommends-options.md:ba-next recommends options after intake recommendation
f15:f15-backbone-blocked-unresolved-options.md:g15-backbone-blocked-unresolved-options.md:backbone blocked while options decision is unresolved
f16:f16-frd-guardrail-index-first.md:g16-frd-guardrail-index-first.md:frd guardrail enforces backbone index-first discovery
f17:f17-stories-guardrail-index-first.md:g17-stories-guardrail-index-first.md:stories guardrail enforces backbone index-first discovery
f18:f18-package-guardrail-escalated-exact-content.md:g18-package-guardrail-escalated-exact-content.md:package guardrail tracks escalated exact-content reads
f19:f19-status-project-home-conflict.md:g19-status-project-home-conflict.md:status trusts canonical artifacts over PROJECT-HOME conflict
f20:f20-next-project-home-conflict.md:g20-next-project-home-conflict.md:next recommends canonical step despite PROJECT-HOME conflict
f21:f21-reverse-baseline-entry-focus-gate.md:g21-reverse-baseline-entry-focus-gate.md:reverse baseline entry blocks at HITL focus-selection gate
f22:f22-reverse-focus-selection-blocks.md:g22-reverse-focus-selection-blocks.md:reverse focus selection blocks without explicit confirmation
f23:f23-reverse-drift-stale-block.md:g23-reverse-drift-stale-block.md:reverse status surfaces stale index and recommends refresh
f24:f24-reverse-mixed-change-blocks-promotion.md:g24-reverse-mixed-change-blocks-promotion.md:reverse promote blocks mixed_change evidence requiring split
f25:f25-reverse-source-only-no-runtime-probes.md:g25-reverse-source-only-no-runtime-probes.md:reverse source-only regression blocks runtime probes in v1
f26:f26-reverse-srs-skips-design-and-wireframes.md:g26-reverse-srs-skips-design-and-wireframes.md:reverse-backed srs bypasses forward design and wireframe gating
f27:f27-srs-post-gate-module-qc.md:g27-srs-post-gate-module-qc.md:srs auto-triggers module QC with module-scoped outputs
f28:f28-wireframes-does-not-trigger-qc.md:g28-wireframes-does-not-trigger-qc.md:wireframes stays downstream and does not auto-trigger qc-review
"

REGISTRY_FILE="${TMPDIR:-/tmp}/ba-kit-runtime-parity-fixtures.$$"
trap 'rm -f "$REGISTRY_FILE"' EXIT HUP INT TERM
printf '%s\n' "$FIXTURES" | sed '/^$/d' > "$REGISTRY_FILE"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] [fixture-id]

Options:
  --list              List all available fixtures and their status
  --check-structure   Verify harness directory and file integrity
  --run-adapters      Execute runtime adapters and compare normalized output
  --runtime <name>    Limit adapter execution to claude, codex, or antigravity
  fixture-id          Run parity check for a single fixture (e.g. f01)
  (no args)           Run all fixtures

Exit codes:
  0  All parity checks pass
  1  Structure missing, golden absent, or parity failure detected
  2  Parity pending because runtime adapters/certifications are absent
EOF
}

require_exact_line() {
    path="$1"
    expected="$2"
    label="$3"

    if grep -Fqx "$expected" "$path"; then
        return 0
    fi

    echo "  FAIL: $label missing in $path: $expected"
    return 1
}

require_table_field() {
    path="$1"
    field="$2"
    label="$3"

    if grep -Eq "^\| ${field} \|" "$path"; then
        return 0
    fi

    echo "  FAIL: $label missing field in $path: $field"
    return 1
}

require_runtime_status_row() {
    path="$1"
    runtime="$2"
    label="$3"

    if grep -Eq "^\| ${runtime} \| (PENDING|PASS|FAIL|EXEMPT)( .*)? \|$" "$path"; then
        return 0
    fi

    echo "  FAIL: $label missing runtime row in $path: $runtime"
    return 1
}

check_fixture_contract() {
    path="$1"
    id="$2"
    fixture_failed=0

    for heading in "## Scenario" "## Input State" "## Input Command" "## Expected Behavior" "## Expected Outcome"; do
        require_exact_line "$path" "$heading" "fixture $id" || fixture_failed=1
    done

    for field in resolved_command source_of_truth_artifact write_target approval_gate activation_level fallback_code; do
        require_table_field "$path" "$field" "fixture $id expected outcome" || fixture_failed=1
    done

    case "$id" in
        f13|f14|f15)
            require_table_field "$path" "read_scope" "fixture $id expected outcome" || fixture_failed=1
            ;;
        f16|f17|f18|f19|f20)
            require_table_field "$path" "read_scope" "fixture $id expected outcome" || fixture_failed=1
            require_exact_line "$path" "## Guardrail Evidence" "fixture $id" || fixture_failed=1
            for field in evidence_source preflight_status audit_status; do
                require_table_field "$path" "$field" "fixture $id guardrail evidence" || fixture_failed=1
            done
            ;;
    esac

    if [ "$fixture_failed" -eq 0 ]; then
        echo "  OK:   fixture $id contract fields"
        return 0
    fi
    return 1
}

check_golden_contract() {
    path="$1"
    id="$2"
    golden_failed=0

    require_exact_line "$path" "## Behavior Envelope" "golden $id" || golden_failed=1
    require_exact_line "$path" "| Field | Expected Value |" "golden $id behavior envelope" || golden_failed=1
    require_exact_line "$path" "## Runtime Parity Check" "golden $id" || golden_failed=1

    for field in resolved_command resolved_slug source_of_truth_artifact read_scope write_target approval_gate activation_level fallback_code; do
        require_table_field "$path" "$field" "golden $id behavior envelope" || golden_failed=1
    done

    case "$id" in
        f13)
            for field in option_artifact_count comparison_rule; do
                require_table_field "$path" "$field" "golden $id behavior envelope" || golden_failed=1
            done
            ;;
        f14)
            require_table_field "$path" "recommendation_summary" "golden $id behavior envelope" || golden_failed=1
            ;;
        f15)
            for field in visible_warning required_decision; do
                require_table_field "$path" "$field" "golden $id behavior envelope" || golden_failed=1
            done
            require_exact_line "$path" "| required_decision | selected option or skipped |" "golden $id behavior envelope" || golden_failed=1
            ;;
        f16|f17|f18|f19|f20)
            require_exact_line "$path" "## Guardrail Preflight" "golden $id" || golden_failed=1
            require_exact_line "$path" "## Guardrail Audit" "golden $id" || golden_failed=1
            for field in status command guardrail_mode allow_reads_includes message; do
                require_table_field "$path" "$field" "golden $id guardrail preflight" || golden_failed=1
            done
            for field in status actual_reads_includes violations.count warnings.count message; do
                require_table_field "$path" "$field" "golden $id guardrail audit" || golden_failed=1
            done
            ;;
    esac

    case "$id" in
        f16|f17)
            for field in "indexes.backbone_index.state" deny_reads_includes excerpt_plan; do
                require_table_field "$path" "$field" "golden $id guardrail section" || golden_failed=1
            done
            require_table_field "$path" "actual_reads_excludes" "golden $id guardrail audit" || golden_failed=1
            ;;
        f18)
            for field in "indexes.backbone_index.state" "indexes.userstories_index.state" "indexes.usecases_index.state" "indexes.ascii_screen_index.state" deny_reads_includes; do
                require_table_field "$path" "$field" "golden $id guardrail section" || golden_failed=1
            done
            require_table_field "$path" "warnings.types_includes" "golden $id guardrail audit" || golden_failed=1
            require_table_field "$path" "warnings.paths_includes" "golden $id guardrail audit" || golden_failed=1
            ;;
        f19)
            for field in visible_warning canonical_state_summary; do
                require_table_field "$path" "$field" "golden $id behavior envelope" || golden_failed=1
            done
            require_table_field "$path" "project_home_override" "golden $id guardrail preflight" || golden_failed=1
            require_table_field "$path" "actual_reads_excludes" "golden $id guardrail audit" || golden_failed=1
            ;;
        f20)
            for field in visible_warning recommendation_summary; do
                require_table_field "$path" "$field" "golden $id behavior envelope" || golden_failed=1
            done
            require_table_field "$path" "project_home_override" "golden $id guardrail preflight" || golden_failed=1
            require_table_field "$path" "actual_reads_excludes" "golden $id guardrail audit" || golden_failed=1
            ;;
    esac

    for runtime in "Claude Code" "Codex" "Antigravity"; do
        require_runtime_status_row "$path" "$runtime" "golden $id runtime parity" || golden_failed=1
    done

    if grep -Eq '^\| [a-zA-Z_]+ \|[[:space:]]*\|$' "$path"; then
        echo "  FAIL: golden $id has an empty behavior-envelope value: $path"
        golden_failed=1
    fi

    if [ "$golden_failed" -eq 0 ]; then
        echo "  OK:   golden $id behavior envelope"
        return 0
    fi
    return 1
}

check_structure() {
    echo "Checking harness directory structure..."
    failed=0

    if [ ! -d "$FIXTURES_DIR" ]; then
        echo "  FAIL: fixtures dir missing: $FIXTURES_DIR"
        failed=1
    else
        echo "  OK:   $FIXTURES_DIR"
    fi

    if [ ! -d "$GOLDENS_DIR" ]; then
        echo "  FAIL: goldens dir missing: $GOLDENS_DIR"
        failed=1
    else
        echo "  OK:   $GOLDENS_DIR"
    fi

    while IFS=: read -r id fixture golden desc; do
        fpath="$FIXTURES_DIR/$fixture"
        gpath="$GOLDENS_DIR/$golden"
        if [ ! -f "$fpath" ]; then
            echo "  FAIL: fixture missing: $fpath"
            failed=1
        else
            echo "  OK:   fixture $id: $fixture"
            check_fixture_contract "$fpath" "$id" || failed=1
        fi
        if [ ! -f "$gpath" ]; then
            echo "  FAIL: golden missing: $gpath"
            failed=1
        else
            echo "  OK:   golden $id: $golden"
            check_golden_contract "$gpath" "$id" || failed=1
        fi
    done < "$REGISTRY_FILE"

    if [ "$failed" -eq 0 ]; then
        echo "Structure OK."
        return 0
    else
        echo "Structure check FAILED."
        return 1
    fi
}

list_fixtures() {
    echo "Available fixtures:"
    echo ""
    printf "  %-6s %-45s %s\n" "ID" "Fixture File" "Description"
    printf "  %-6s %-45s %s\n" "------" "---------------------------------------------" "-----------"
    while IFS=: read -r id fixture golden desc; do
        gpath="$GOLDENS_DIR/$golden"
        if [ -f "$gpath" ]; then
            status="golden present"
        else
            status="GOLDEN MISSING"
        fi
        printf "  %-6s %-45s %s [%s]\n" "$id" "$fixture" "$desc" "$status"
    done < "$REGISTRY_FILE"
}

runtime_selected() {
    runtime="$1"
    [ "$RUNTIME_FILTER" = "all" ] || [ "$RUNTIME_FILTER" = "$runtime" ]
}

golden_runtime_status() {
    path="$1"
    runtime_label="$2"

    awk -F'|' -v runtime="${runtime_label}" '
      {
        field=$2
        status=$3
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", field)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", status)
        if (field == runtime) {
          split(status, parts, /[[:space:]]+/)
          print parts[1]
          exit
        }
      }
    ' "$path"
}

report_golden_runtime_status() {
    runtime="$1"
    label="$2"
    gpath="$3"
    row_status="$(golden_runtime_status "$gpath" "$label")"

    if ! runtime_selected "$runtime"; then
        return 0
    fi

    case "$row_status" in
        PASS|EXEMPT)
            echo "  $label: $row_status"
            return 0
            ;;
        FAIL)
            echo "  $label: FAIL (golden runtime row)"
            return 1
            ;;
        *)
            echo "  $label: PENDING (use --run-adapters or mark golden row PASS/EXEMPT)"
            return 2
            ;;
    esac
}

run_one_runtime_adapter() {
    runtime="$1"
    label="$2"
    id="$3"
    fpath="$4"
    gpath="$5"
    output_path="${TMPDIR:-/tmp}/ba-kit-runtime-parity-${id}-${runtime}.$$"

    if ! runtime_selected "$runtime"; then
        return 0
    fi

    if "$ADAPTER_SCRIPT" "$runtime" "$fpath" "$gpath" "$output_path"; then
        if python3 "$NORMALIZER_SCRIPT" compare \
            --golden "$gpath" \
            --actual "$output_path" \
            --runtime "$label" \
            --fixture-id "$id"; then
            rm -f "$output_path"
            return 0
        fi
        rm -f "$output_path"
        return 1
    else
        adapter_status=$?
        rm -f "$output_path"
        if [ "$adapter_status" -eq 2 ]; then
            if [ "$runtime" = "antigravity" ]; then
                echo "  $label: PENDING (manual certification JSON missing)"
            else
                echo "  $label: PENDING (CLI adapter unavailable)"
            fi
            return 2
        fi
        echo "  $label: FAIL (adapter execution failed)"
        return 1
    fi
}

run_fixture_parity() {
    id="$1"
    fpath="$2"
    gpath="$3"
    fixture_status=0

    if [ "$RUN_ADAPTERS" != "1" ]; then
        report_golden_runtime_status "claude" "Claude Code" "$gpath" || runtime_status=$?
        runtime_status="${runtime_status:-0}"
        if [ "$runtime_status" -eq 1 ]; then
            fixture_status=1
        elif [ "$runtime_status" -eq 2 ] && [ "$fixture_status" -eq 0 ]; then
            fixture_status=2
        fi
        unset runtime_status

        report_golden_runtime_status "codex" "Codex" "$gpath" || runtime_status=$?
        runtime_status="${runtime_status:-0}"
        if [ "$runtime_status" -eq 1 ]; then
            fixture_status=1
        elif [ "$runtime_status" -eq 2 ] && [ "$fixture_status" -eq 0 ]; then
            fixture_status=2
        fi
        unset runtime_status

        report_golden_runtime_status "antigravity" "Antigravity" "$gpath" || runtime_status=$?
        runtime_status="${runtime_status:-0}"
        if [ "$runtime_status" -eq 1 ]; then
            fixture_status=1
        elif [ "$runtime_status" -eq 2 ] && [ "$fixture_status" -eq 0 ]; then
            fixture_status=2
        fi
        unset runtime_status

        return "$fixture_status"
    fi

    run_one_runtime_adapter "claude" "Claude Code" "$id" "$fpath" "$gpath" || runtime_status=$?
    runtime_status="${runtime_status:-0}"
    if [ "$runtime_status" -eq 1 ]; then
        fixture_status=1
    elif [ "$runtime_status" -eq 2 ] && [ "$fixture_status" -eq 0 ]; then
        fixture_status=2
    fi
    unset runtime_status

    run_one_runtime_adapter "codex" "Codex" "$id" "$fpath" "$gpath" || runtime_status=$?
    runtime_status="${runtime_status:-0}"
    if [ "$runtime_status" -eq 1 ]; then
        fixture_status=1
    elif [ "$runtime_status" -eq 2 ] && [ "$fixture_status" -eq 0 ]; then
        fixture_status=2
    fi
    unset runtime_status

    run_one_runtime_adapter "antigravity" "Antigravity" "$id" "$fpath" "$gpath" || runtime_status=$?
    runtime_status="${runtime_status:-0}"
    if [ "$runtime_status" -eq 1 ]; then
        fixture_status=1
    elif [ "$runtime_status" -eq 2 ] && [ "$fixture_status" -eq 0 ]; then
        fixture_status=2
    fi
    unset runtime_status

    return "$fixture_status"
}

# Checks fixture/golden availability and returns aggregate parity status.
run_fixture() {
    target_id="$1"
    matched=0
    status=0

    while IFS=: read -r id fixture golden desc; do
        if [ "$target_id" != "ALL" ] && [ "$id" != "$target_id" ]; then
            continue
        fi
        matched=1

        fpath="$FIXTURES_DIR/$fixture"
        gpath="$GOLDENS_DIR/$golden"

        echo "---"
        echo "Fixture [$id]: $desc"

        if [ ! -f "$fpath" ]; then
            echo "  ERROR: fixture file not found: $fpath"
            return 1
        fi

        if [ ! -f "$gpath" ]; then
            echo "  ERROR: golden file not found: $gpath"
            echo "  Cannot verify parity without a golden contract."
            return 1
        fi

        if run_fixture_parity "$id" "$fpath" "$gpath"; then
            fixture_status=0
        else
            fixture_status=$?
        fi

        if [ "$fixture_status" -eq 1 ]; then
            status=1
        elif [ "$fixture_status" -eq 2 ]; then
            if [ "$status" -eq 0 ]; then
                status=2
            fi
        elif [ "$fixture_status" -ne 0 ]; then
            echo "  ERROR: unexpected parity status for $id: $fixture_status"
            status=1
        fi
    done < "$REGISTRY_FILE"

    if [ "$matched" -eq 0 ] && [ "$target_id" != "ALL" ]; then
        echo "ERROR: unknown fixture id '$target_id'. Use --list to see available fixtures."
        return 1
    fi

    return "$status"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --help|-h)
            usage
            exit 0
            ;;
        --list)
            list_fixtures
            exit 0
            ;;
        --check-structure)
            check_structure
            exit $?
            ;;
        --run-adapters)
            RUN_ADAPTERS=1
            ;;
        --runtime)
            shift
            [ "$#" -gt 0 ] || {
                echo "Missing value for --runtime" >&2
                exit 1
            }
            RUNTIME_FILTER="$1"
            case "$RUNTIME_FILTER" in
                all|claude|codex|antigravity) ;;
                *)
                    echo "Unsupported runtime filter: $RUNTIME_FILTER" >&2
                    exit 1
                    ;;
            esac
            ;;
        f[0-9]*)
            TARGET_FIXTURE="$1"
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
    shift
done

check_structure || exit 1
echo ""
if run_fixture "$TARGET_FIXTURE"; then
    fixture_status=0
else
    fixture_status=$?
fi
echo ""
if [ "$fixture_status" -eq 0 ]; then
    echo "All fixture checks complete. Status: PASS."
elif [ "$fixture_status" -eq 2 ]; then
    echo "All fixture checks complete. Status: PENDING (runtime adapters or manual certifications incomplete)."
    echo "NOTE: Exiting 2 - parity not fully verified yet. 0=pass, 1=structural/parity error, 2=pending."
fi
exit "$fixture_status"
