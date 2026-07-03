# Antigravity Manual Runtime Certification

Antigravity currently exposes `antigravity chat`, but local CLI help does not expose a
headless stdout/JSON mode equivalent to `claude -p` or `codex exec`.

Until a deterministic adapter exists, certify each fixture manually:

1. Open Antigravity with BA-kit installed.
2. Submit the fixture Input Command from `tests/runtime-parity/fixtures/fXX-*.md`.
3. Normalize the result into a JSON object with the exact keys from the matching golden's
   `## Behavior Envelope`.
4. Save it as `tests/runtime-parity/certifications/antigravity/fXX.json`.
5. Run `bash scripts/test-runtime-parity.sh --run-adapters --runtime antigravity fXX`.

Manual certification JSON values must be strings.

## Template Scaffolding

Use the scaffolder to generate fill-in templates from existing goldens:

```bash
python3 scripts/scaffold-antigravity-certification.py f21 f22 f23 f24 f25 f26
```

That creates `fXX.template.json` files in this folder. Copy the matching template to
`fXX.json`, fill it from an actual Antigravity run, then execute the parity harness.

Recommended reverse-fixture certification order:

1. `f21` baseline entry focus gate
2. `f22` focus selection block
3. `f23` stale reverse status
4. `f24` mixed-change promotion block
5. `f25` source-only reverse scan
6. `f26` reverse-backed SRS without design/wireframes
