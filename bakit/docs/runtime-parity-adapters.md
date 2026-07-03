# Runtime Parity Adapters

BA-kit parity execution is opt-in because it may call external LLM runtimes.

Guardrail design for low-token runtime enforcement lives in [runtime-hard-guardrails.md](./runtime-hard-guardrails.md).

## Commands

Structure only:

```bash
bash scripts/test-runtime-parity.sh --check-structure
```

Run all available adapters:

```bash
bash scripts/test-runtime-parity.sh --run-adapters
```

Run one fixture on one runtime:

```bash
bash scripts/test-runtime-parity.sh --run-adapters --runtime claude f01
bash scripts/test-runtime-parity.sh --run-adapters --runtime codex f01
bash scripts/test-runtime-parity.sh --run-adapters --runtime antigravity f01
```

## Runtime Strategy

| Runtime | Adapter Mode | Command |
| --- | --- | --- |
| Claude Code | Headless | `claude -p` with read-only tool set |
| Codex | Headless | `codex exec` with read-only sandbox |
| Antigravity | Manual certification | JSON files under `tests/runtime-parity/certifications/antigravity/` |

## Guardrail Fixture Shape

Legacy fixtures still use only `## Behavior Envelope`.

Guardrail fixtures (`f16`-`f20`) add:

- `## Guardrail Preflight`
- `## Guardrail Audit`

The parity harness accepts either:

1. the legacy flat JSON object for behavior-envelope-only fixtures
2. a sectioned JSON object for guardrail fixtures

Sectioned JSON shape:

```json
{
  "behavior_envelope": {
    "resolved_command": "ba-start frd"
  },
  "guardrail_preflight": {
    "status": "ok",
    "command": "frd"
  },
  "guardrail_audit": {
    "status": "pass",
    "actual_reads": "core/contract.yaml, plans/test-project-20260424/02_backbone/backbone-index.md"
  }
}
```

All leaf values should be strings for headless adapter output and Antigravity manual certifications.

## Guardrail Evidence Rules

- `guardrail_preflight` should mirror the portable-core verdict from `scripts/guardrail-preflight.py`.
- `guardrail_audit` should reflect runtime-trace or adapter-manifest evidence from `scripts/guardrail-audit.py`.
- `actual_reads` should list repo-relative governed reads in runtime order.
- Generated excerpt temp files are adapter-specific and should be omitted from parity goldens unless the adapter emits a stable repo-relative alias.
- Compile-time full reads that are still legal in context should be represented as explicit warning/escalation evidence, not hidden broad reads.

Goldens may use matcher fields instead of strict full-list equality:

- `allow_reads_includes`
- `deny_reads_includes`
- `actual_reads_includes`
- `actual_reads_excludes`
- `warnings.types_includes`
- `warnings.paths_includes`

These matcher fields compare against the adapter's canonical fields (`allow_reads`, `deny_reads`, `actual_reads`, `warnings.types`, `warnings.paths`) and let parity stay strict about guardrail behavior without overfitting to adapter-only noise.

## Antigravity Manual Certification

Antigravity local CLI exposes `antigravity chat`, but no deterministic stdout/JSON mode is
available from `antigravity chat --help`.

For each fixture:

1. Run the fixture manually in Antigravity.
2. Normalize the result into the matching golden fields.
3. For guardrail fixtures, use the same sectioned JSON shape as the headless adapters.
4. Prefer runtime-trace or adapter-manifest evidence for `guardrail_audit.actual_reads`. If only a summarized evidence packet exists, keep it explicit in warning/status fields instead of inventing precision.
5. Save `tests/runtime-parity/certifications/antigravity/fXX.json`.
6. Run `bash scripts/test-runtime-parity.sh --run-adapters --runtime antigravity fXX`.

Manual certification values must be strings.
