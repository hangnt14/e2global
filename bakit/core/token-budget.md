# Token Budget Baseline

Muc tieu cua file nay la khoa tran kich thuoc cho instruction surface cua BA-kit sau refactor `contract + shared behavior + command shard + step files`.

- Don vi dung trong CI la `bytes`, khong phai token.
- `bytes` on dinh hon tokenization runtime va du tot de bat drift som.
- Cac nguong `max` la guardrail, khong phai muc tieu de lap day.
- Khi mo rong instruction surface co chu y, cap nhat `baseline` va `max`, roi chay lai budget check.

## Baseline hien tai

- Shared entry runtime: `core/contract.yaml` + `core/contract-behavior.md` + `skills/ba-start/SKILL.md` = `45,736 bytes`
- Runtime policies: `AGENTS.md` + `GEMINI.md` + `CLAUDE.md` = `12,491 bytes`
- Command runtime bundle lon nhat: `srs_runtime_bundle` = `64,414 bytes`
- Behavior base cap: `14,000 bytes`; moi behavior shard cap: `4,500 bytes`

## Guardrail source

```json
{
  "version": 13,
  "captured_at": "2026-05-28",
  "units": "bytes",
  "notes": "Baselines updated after new artifact architecture refactor (folder-based canon, userstories/, usecases/, ascii-screen/, srs/ source set).",
  "files": [
    {
      "path": "core/contract.yaml",
      "baseline": 25706,
      "max": 25706,
      "label": "machine contract"
    },
    {
      "path": "core/contract-behavior.md",
      "baseline": 19915,
      "max": 21000,
      "label": "shared behavior contract"
    },
    {
      "path": "core/behavior/intake.md",
      "baseline": 700,
      "max": 4500,
      "label": "intake behavior shard"
    },
    {
      "path": "core/behavior/backbone.md",
      "baseline": 2332,
      "max": 4500,
      "label": "backbone behavior shard"
    },
    {
      "path": "core/behavior/impact.md",
      "baseline": 4877,
      "max": 4877,
      "label": "impact behavior shard"
    },
    {
      "path": "core/behavior/module-authoring.md",
      "baseline": 1771,
      "max": 4500,
      "label": "module authoring behavior shard"
    },
    {
      "path": "core/behavior/srs.md",
      "baseline": 5992,
      "max": 6300,
      "label": "srs behavior shard"
    },
    {
      "path": "core/behavior/wireframes.md",
      "baseline": 3777,
      "max": 4500,
      "label": "wireframes behavior shard"
    },
    {
      "path": "core/behavior/package-status-next.md",
      "baseline": 2589,
      "max": 4500,
      "label": "package status next behavior shard"
    },
    {
      "path": "core/behavior/figma-sync.md",
      "baseline": 1700,
      "max": 4500,
      "label": "figma sync behavior shard"
    },
    {
      "path": "skills/ba-start/SKILL.md",
      "baseline": 4124,
      "max": 4124,
      "label": "ba-start stub"
    },
    {
      "path": "skills/ba-start/steps/intake.md",
      "baseline": 5323,
      "max": 6000,
      "label": "intake step"
    },
    {
      "path": "skills/ba-start/steps/impact.md",
      "baseline": 6796,
      "max": 7200,
      "label": "impact step"
    },
    {
      "path": "skills/ba-start/steps/backbone.md",
      "baseline": 5628,
      "max": 6000,
      "label": "backbone step"
    },
    {
      "path": "skills/ba-start/steps/frd.md",
      "baseline": 2548,
      "max": 2800,
      "label": "frd step"
    },
    {
      "path": "skills/ba-start/steps/stories.md",
      "baseline": 4611,
      "max": 4900,
      "label": "stories step"
    },
    {
      "path": "skills/ba-start/steps/srs.md",
      "baseline": 4675,
      "max": 5000,
      "label": "srs router step"
    },
    {
      "path": "skills/ba-start/steps/srs-core.md",
      "baseline": 3127,
      "max": 4200,
      "label": "srs core step"
    },
    {
      "path": "skills/ba-start/steps/srs-wireframes.md",
      "baseline": 4341,
      "max": 4600,
      "label": "srs wireframes step"
    },
    {
      "path": "skills/ba-start/steps/srs-assembly.md",
      "baseline": 3403,
      "max": 3600,
      "label": "srs assembly step"
    },
    {
      "path": "skills/ba-start/steps/wireframes.md",
      "baseline": 6095,
      "max": 6500,
      "label": "wireframes step"
    },
    {
      "path": "skills/ba-start/steps/package.md",
      "baseline": 4209,
      "max": 4400,
      "label": "package step"
    },
    {
      "path": "skills/ba-start/steps/status.md",
      "baseline": 4382,
      "max": 4600,
      "label": "status step"
    },
    {
      "path": "AGENTS.md",
      "baseline": 2767,
      "max": 3600,
      "label": "codex runtime policy"
    },
    {
      "path": "GEMINI.md",
      "baseline": 5304,
      "max": 5600,
      "label": "antigravity runtime policy"
    },
    {
      "path": "CLAUDE.md",
      "baseline": 7100,
      "max": 7100,
      "label": "claude runtime policy"
    }
  ],
  "bundles": [
    {
      "name": "runtime_policies",
      "baseline": 15171,
      "max": 15171,
      "paths": [
        "AGENTS.md",
        "GEMINI.md",
        "CLAUDE.md"
      ]
    },
    {
      "name": "shared_entry_runtime",
      "baseline": 50616,
      "max": 50616,
      "paths": [
        "core/contract.yaml",
        "core/contract-behavior.md",
        "skills/ba-start/SKILL.md"
      ]
    },
    {
      "name": "intake_runtime_bundle",
      "baseline": 54199,
      "max": 57000,
      "paths": [
        "core/contract.yaml",
        "core/contract-behavior.md",
        "core/behavior/intake.md",
        "skills/ba-start/SKILL.md",
        "skills/ba-start/steps/intake.md"
      ]
    },
    {
      "name": "backbone_runtime_bundle",
      "baseline": 56146,
      "max": 59000,
      "paths": [
        "core/contract.yaml",
        "core/contract-behavior.md",
        "core/behavior/backbone.md",
        "skills/ba-start/SKILL.md",
        "skills/ba-start/steps/backbone.md"
      ]
    },
    {
      "name": "impact_runtime_bundle",
      "baseline": 62357,
      "max": 62357,
      "paths": [
        "core/contract.yaml",
        "core/contract-behavior.md",
        "core/behavior/impact.md",
        "skills/ba-start/SKILL.md",
        "skills/ba-start/steps/impact.md"
      ]
    },
    {
      "name": "module_authoring_runtime_bundle",
      "baseline": 57614,
      "max": 60500,
      "paths": [
        "core/contract.yaml",
        "core/contract-behavior.md",
        "core/behavior/module-authoring.md",
        "skills/ba-start/SKILL.md",
        "skills/ba-start/steps/frd.md",
        "skills/ba-start/steps/stories.md"
      ]
    },
    {
      "name": "srs_core_bundle",
      "baseline": 65279,
      "max": 68600,
      "paths": [
        "core/contract.yaml",
        "core/contract-behavior.md",
        "core/behavior/srs.md",
        "skills/ba-start/SKILL.md",
        "skills/ba-start/steps/srs.md",
        "skills/ba-start/steps/srs-core.md",
        "skills/ba-start/steps/srs-assembly.md"
      ]
    },
    {
      "name": "srs_runtime_bundle",
      "baseline": 69538,
      "max": 73100,
      "paths": [
        "core/contract.yaml",
        "core/contract-behavior.md",
        "core/behavior/srs.md",
        "skills/ba-start/SKILL.md",
        "skills/ba-start/steps/srs.md",
        "skills/ba-start/steps/srs-core.md",
        "skills/ba-start/steps/srs-wireframes.md",
        "skills/ba-start/steps/srs-assembly.md"
      ]
    },
    {
      "name": "wireframes_runtime_bundle",
      "baseline": 51137,
      "max": 58500,
      "paths": [
        "core/contract.yaml",
        "core/contract-behavior.md",
        "core/behavior/wireframes.md",
        "skills/ba-start/SKILL.md",
        "skills/ba-start/steps/wireframes.md"
      ]
    },
    {
      "name": "package_status_next_runtime_bundle",
      "baseline": 59923,
      "max": 63000,
      "paths": [
        "core/contract.yaml",
        "core/contract-behavior.md",
        "core/behavior/package-status-next.md",
        "skills/ba-start/SKILL.md",
        "skills/ba-start/steps/package.md",
        "skills/ba-start/steps/status.md"
      ]
    }
  ]
}
```

## Cach chay

Windows:

```powershell
python scripts/check-token-budget.py .
```

Unix-like:

```bash
scripts/check-token-budget.sh
```

Neu budget fail, uu tien:

1. Go rule trung lap khoi runtime policy files.
2. Tach bot step file hoac behavior shard neu mot path phinh qua nhanh.
3. Dua phan deterministic sang CLI hoac manifest machine-readable thay vi prose.
