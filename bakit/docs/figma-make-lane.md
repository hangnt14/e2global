# Figma Make Lane

BA-kit vẫn coi `manual` là lane mặc định ở Step 9. Figma Make là lane opt-in cho team muốn prototype nhanh nhưng vẫn giữ hard guardrails ở upstream BA artifacts.

## Artifact flow

1. `srs` viết Group B + Group C như bình thường.
2. Step 8.1 sinh:
   - `03_modules/{module}/screen-field-contract.yaml`
3. `srs` sinh ASCII bắt buộc trong `03_modules/{module}/ascii-screen/*.md`.
4. Nếu lane là `figma-make`, tool lane sinh:
   - `05_tool-lanes/figma-make/shared-rules.md`
   - `05_tool-lanes/figma-make/shared-prompt-skeleton.md`
   - `05_tool-lanes/figma-make/shared-component-contracts.md`
   - `03_modules/{module}/tool-lanes/figma-make/make-guidelines.md`
   - `03_modules/{module}/tool-lanes/figma-make/make-prompt-pack.md`
   - `03_modules/{module}/tool-lanes/figma-make/usecases/uc-{usecase_slug}-make-prompt.md`
   - `03_modules/{module}/tool-lanes/figma-make/usecases/uc-{usecase_slug}-change-log.md`
   - `03_modules/{module}/tool-lanes/figma-make/prototype-conformance-checklist.md`
5. Sau khi Make tạo prototype, team dùng checklist + report để reject drift.

## Source of truth split

- `srs/spec.md`, `srs/flows.md`, `srs/states.md`, và `srs/erd.md`: source of truth nghiệp vụ theo lát cắt.
- `screen-field-contract.yaml`: bản normalize máy đọc được của screen truth.
- `ascii-screen/*.md`: source of truth cho ASCII wireframe.
- `DESIGN.md`: visual baseline và navigation schema baseline.
- `tool-lanes/figma-make/make-guidelines.md` + `tool-lanes/figma-make/make-prompt-pack.md`: downstream control artifacts, không phải source of truth.

## Per-UC prompts and change logs

Mỗi use case có hai file riêng dưới `tool-lanes/figma-make/usecases/`:

- `uc-{usecase_slug}-make-prompt.md`: paste-ready Figma Make prompt, scoped chặt vào screens/fields/states của một UC. File này kế thừa shared skeleton cho design system, color palette, typography — không định nghĩa lại.
- `uc-{usecase_slug}-change-log.md`: versioned incremental change prompts. Mỗi version ghi lại approved prototype change cho version đó, kèm paste-ready prompt riêng. Không dùng để smuggle requirement changes — material drift phải route qua `ba-start impact`.

### Quy tắc per-UC prompt

- UC-01 không phải style authority — `DESIGN.md` mới là visual baseline.
- Mỗi UC prompt chỉ describe screens/fields/states thuộc UC đó.
- Hard negatives bắt buộc: "Do not modify any other element outside this UC scope".
- Shared prompt skeleton dùng chung cho mọi UC — không copy-paste vào từng file.

### Quy tắc change log

- Change log là optional — chỉ tạo khi có approved prototype change đầu tiên.
- Mỗi version là một paste-ready prompt độc lập.
- Version cũ giữ lại để audit, version mới nhất là active Make prompt.
- "Do NOT modify any other element" luôn có trong mỗi version prompt.

## Hard rules

- Không dùng raw `srs.md` làm Make prompt chính.
- Không thêm field ngoài allowlist trong `screen-field-contract.yaml`.
- Không đổi `Portal ID`, `Nav Schema ID`, `Expected Active Menu Item`.
- Nếu rule thiếu, bỏ qua thay vì tự phát minh.
- Drift phát hiện sau prototype phải route qua `ba-start impact`.

## Pre-flight

Chạy:

```bash
python3 scripts/validate-tool-control-pack.py --repo . --slug <slug> --date <YYMMDD-HHmm> --module <module>
```

Nếu lane là `manual`, validator sẽ `skip`. Nếu lane là `figma-make`, validator fail khi thiếu:

- `screen-field-contract.yaml`
- shared rules / prompt skeleton / component contracts
- `tool-lanes/figma-make/make-prompt-pack.md`
- `tool-lanes/figma-make/prototype-conformance-checklist.md`

## Report

Sinh skeleton report:

```bash
python3 scripts/generate-prototype-conformance-report.py --repo . --slug <slug> --date <YYMMDD-HHmm> --module <module>
```

Report mặc định list từng `screen_id` để reviewer mark `pass`, `fail`, `blocked`, hoặc `needs-impact`.
