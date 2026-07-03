# Maintainer Release Checklist

Use this checklist before marking adaptive runtime memory work as release-ready.

## Contract And Runtime Distribution

| Check | Status | Evidence |
| --- | --- | --- |
| Contract sync validation | PASS | `bash scripts/test-contract-sync.sh` |
| Token budget validation | PASS | `bash scripts/check-token-budget.sh` |
| Claude installer syntax | PASS | `bash -n install.sh` |
| Codex installer syntax | PASS | `bash -n scripts/install-codex-ba-kit.sh` |
| Antigravity installer syntax | PASS | `bash -n scripts/install-antigravity-ba-kit.sh` |
| Shared CLI syntax | PASS | `bash -n scripts/ba-kit` |
| Codex generated asset check | PASS | covered by `scripts/test-contract-sync.sh` |
| Guardrail core script syntax | PASS | `python3 -m py_compile scripts/guardrail-preflight.py scripts/guardrail-build-excerpts.py scripts/guardrail-audit.py scripts/guardrail_common.py scripts/validate-index-quality.py` |
| Index-quality validator smoke | PASS | `bash scripts/test-index-quality.sh` |
| Guardrail hardening smoke | PASS | `bash scripts/test-guardrail-hardening.sh` |
| Activation threshold validation | PASS | `bash scripts/test-activation-thresholds.sh` |
| Runtime install smoke | PASS | `bash scripts/test-runtime-install-smoke.sh` |
| Reverse script syntax/smoke | PASS | `bash scripts/test-reverse-guardrails.sh` |
| Reverse index validation smoke | PASS | `bash scripts/test-index-quality.sh` with reverse fixtures |

## Parity Harness

| Check | Status | Evidence |
| --- | --- | --- |
| Fixture/golden structure | PASS | `bash scripts/test-runtime-parity.sh --check-structure` |
| Normalized behavior envelopes | PASS | `tests/runtime-parity/goldens/*.md` f01-f12 |
| Guardrail fixture/golden coverage | PASS | `tests/runtime-parity/goldens/*.md` f16-f20 |
| Reverse parity fixture coverage | PASS | reverse fixtures/goldens cover baseline lock, reverse status, reverse impact, and reverse promote flows |
| Runtime adapter execution | EXEMPT | v1 maintainer decision; adapters remain available for future release evidence |
| Claude Code headless adapter | EXEMPT | `bash scripts/test-runtime-parity.sh --run-adapters --runtime claude fXX` remains available |
| Codex headless adapter | EXEMPT | `bash scripts/test-runtime-parity.sh --run-adapters --runtime codex fXX` remains available |
| Antigravity manual adapter | EXEMPT | manual JSON certification remains available under `tests/runtime-parity/certifications/antigravity/` |
| Antigravity CLI capability scout | PASS | `docs/runtime-antigravity-capability-spike.md` records local `antigravity chat --help` constraints |

## Upgrade And Rollback

| Check | Status | Evidence |
| --- | --- | --- |
| Summary-only compact fallback fixture | COVERED | F01 |
| Missing index compact fallback fixture | COVERED | F05 |
| Activation freeze fixture | COVERED | F09 |
| Explicit-step fallback fixture | COVERED | F10 |
| Guardrail index-first FRD fixture | COVERED | F16 |
| Guardrail index-first stories fixture | COVERED | F17 |
| Guardrail package escalation fixture | COVERED | F18 |
| Guardrail PROJECT-HOME conflict fixtures | COVERED | F19-F20 |
| Producer-side validator downgrade fixture | COVERED | `scripts/test-index-quality.sh` incomplete-coverage case |
| Producer-side validator promotion fixture | COVERED | `scripts/test-index-quality.sh` writeback case |
| Packet-disable fallback | OPERATIONAL CONTROL | disable runtime-specific packet enforcement until adapter parity exists |
| Installer-freeze fallback | OPERATIONAL CONTROL | do not publish installer rollout if this checklist has blocking FAIL items |
| Installed-runtime upgrade path | PASS | `bash scripts/test-runtime-install-smoke.sh` installs all 3 runtimes into a temporary `HOME` and runs installed `ba-kit doctor` |

## Distribution Strategy

Current decision: maintain the three installers with strict validation.

Rationale:
- The installers have different runtime targets and side effects.
- `scripts/test-contract-sync.sh`, syntax checks, and `ba-kit doctor/update` provide practical drift detection today.
- Single-source installer generation is deferred until repeated drift appears in release maintenance.

## Phase Close Rule

Phase 4 is closed for v1 by maintainer decision:
- runtime adapter execution is `EXEMPT`
- Antigravity live spike is `EXEMPT`
- structural parity, fixture/golden, installer smoke, and threshold checks remain required

Future releases may reopen runtime execution as a blocking gate.

## Commercial Access Checks

- verify `LICENSE` is the BA-kit Commercial License and does not contain MIT wording
- verify repo access for any legal entity that purchased or was granted access is read-only unless an exception is approved
- verify customer use rights are limited to a single legal entity
- verify any affiliate, contractor, or client access request has a separate written commercial approval
- verify the active order form, invoice, or MSA does not conflict with the root `LICENSE`
- verify README licensing language matches the current commercial model before each release or sales handoff
