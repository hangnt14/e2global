# BA-kit Step-by-Step Guide

Guide này viết cho người mới. Không cần nhớ hết command. Chỉ cần đi đúng flow, đọc trạng thái, rồi chạy bước tiếp theo.

## Các Actor Trong BA-kit

Trước khi đi vào chi tiết, hiểu rõ ai làm gì trong một dự án BA-kit:

| Actor | Vai Trò Chính | Bắt Đầu Từ Đâu |
|-------|---------------|----------------|
| **Lead BA / Solo BA** | Khởi tạo dự án, intake, backbone, chia module, review cross-module, package bàn giao | `./install.sh` → `/ba-start intake` |
| **Module BA** | Nhận 1 module, viết stories + SRS canon, gửi review | `/ba-collab Tôi nhận module <tên>` |
| **Stakeholder** | Cung cấp yêu cầu, trả lời gap, review milestone, phê duyệt | Gửi file/text yêu cầu cho BA |
| **UI/UX Designer** | Đọc DESIGN.md + shared shell, sync Figma downstream | `designs/{slug}/DESIGN.md` |
| **QC / Test Lead** | QC review module SRS, chấm điểm readiness | `qc-uc-review` |
| **Developer** | Nhận compiled SRS, đọc use case + screen spec, implement | `04_compiled/compiled-srs.html` |

**Flow tổng quan theo actor:**

```text
Stakeholder → [cung cấp yêu cầu]
Lead BA → [cài đặt → intake → options → backbone → chia module]
    ├── Solo: Lead BA tự viết stories → SRS → package
    └── Multi: Module BA viết stories → SRS → gửi review → Lead BA review → package
Designer → [đọc DESIGN.md + canon → sync Figma] (downstream, không sửa canon)
QC → [QC review module SRS → report] (gate cứng score < 70)
Developer → [nhận compiled SRS → implement]
```

Chi tiết từng bước cho mỗi actor: xem [README.md](../README.md#các-actor-và-các-bước).

## 0. Cách nghĩ trước khi dùng

BA-kit không phải tool tạo file markdown rời rạc. Nó là một flow làm BA:

```text
Input yêu cầu
-> chuẩn hóa intake
-> chốt scope/backbone
-> chia module nếu cần
-> viết stories / FRD / SRS
-> compile SRS đầy đủ
-> package bàn giao
```

Quy tắc quan trọng:

- Nếu không chắc chạy gì tiếp theo, dùng `next`.
- Nếu muốn xem hiện dự án đang có gì, dùng `status`.
- Nếu sửa requirement, đừng sửa file cuối trực tiếp. Chạy `impact` trước.
- Nếu làm UI/SRS, sửa canon trước, rồi compile `srs.md` sau.
- Nếu nhiều BA cùng làm, mỗi BA chỉ sửa module mình nhận.

## 1. Cài và kiểm tra nhanh

Sau khi clone repo BA-kit:

```bash
./install.sh
```

Nếu dùng Codex:

```bash
bash scripts/install-codex-ba-kit.sh
```

Nếu dùng Antigravity:

```bash
bash scripts/install-antigravity-ba-kit.sh
```

Kiểm tra runtime:

```bash
ba-kit doctor
```

Nếu cần render PlantUML trong HTML:

```bash
ba-kit install-plantuml
```

## 2. Cách bắt đầu dễ nhất

Nếu bạn là BA mới, đừng bắt đầu bằng command phức tạp. Hãy nói bằng ngôn ngữ tự nhiên:

```text
/ba-do Tôi có tài liệu yêu cầu mới, hãy tạo dự án BA
```

Hoặc nếu đã có file yêu cầu:

```text
/ba-start intake /path/to/requirements.pdf
```

Kết quả thường có:

```text
plans/{slug}-{date}/PROJECT-HOME.md
plans/{slug}-{date}/01_intake/intake.md
plans/{slug}-{date}/01_intake/plan.md
```

`PROJECT-HOME.md` là trang điều phối để người đọc biết dự án đang ở đâu. Tài liệu gốc vẫn là các artifact trong `01_intake`, `02_backbone`, `03_modules`.

## 3. Luôn biết bước tiếp theo

Sau khi có project, dùng:

```text
/ba-start status --slug warehouse-rfp
```

Hoặc CLI:

```bash
ba-kit status --slug warehouse-rfp
```

Status trả lời kiểu:

```text
[Core]
- [x] intake.md
- [x] backbone.md

[Module: auth-flow]
- [x] user-stories.md
- [ ] srs.md
```

Nếu không biết làm gì tiếp:

```text
/ba-start next --slug warehouse-rfp
```

Hoặc:

```bash
ba-kit next --slug warehouse-rfp
```

`next` sẽ đề xuất command kế tiếp. Làm theo command đó.

## 4. Flow solo BA từ đầu đến cuối

### Bước 1: Intake

Mục tiêu: biến input thô thành yêu cầu có cấu trúc.

Chạy:

```text
/ba-start intake /path/to/source-file.pdf
```

Nếu chỉ có text:

```text
/ba-do Đây là yêu cầu: ...
```

Bạn review:

```text
plans/{slug}-{date}/01_intake/intake.md
```

Kiểm tra:

- stakeholder là ai
- business goal là gì
- scope có gì, out of scope có gì
- câu hỏi mở nào còn thiếu
- mode là `lite`, `hybrid`, hay `formal`

Default thực tế nên dùng `hybrid`.

### Bước 2: Options nếu bài toán có nhiều hướng

Không phải dự án nào cũng cần options. Dùng khi còn nhiều hướng solution, ví dụ build mới, mua SaaS, tích hợp bên thứ ba, hoặc scope còn tranh luận.

Chạy:

```text
/ba-start options --slug warehouse-rfp
```

Review:

```text
plans/{slug}-{date}/01_intake/options/index.md
plans/{slug}-{date}/01_intake/options/comparison.md
```

Nếu chọn phương án 2:

```text
/ba-start options --slug warehouse-rfp --select option-02
```

Nếu team thống nhất không cần options:

```text
/ba-start options --slug warehouse-rfp --skip
```

Không nên sang backbone khi options còn lửng.

### Bước 3: Backbone

Mục tiêu: chốt phạm vi và tạo tài liệu gốc cấp dự án.

Chạy:

```text
/ba-start backbone --slug warehouse-rfp
```

Kết quả:

```text
plans/{slug}-{date}/02_backbone/backbone.md
plans/{slug}-{date}/02_backbone/backbone-index.md
plans/{slug}-{date}/02_backbone/project-memory.md
```

Backbone nên chốt:

- business goals
- actors
- feature map
- module split
- assumptions
- constraints
- UI portal matrix nếu có UI
- shared shell/menu nếu có nhiều màn hình

Từ đây trở đi, các artifact sau phải đi theo backbone.

### Bước 4: Chia module

Nếu dự án nhỏ, có thể chỉ có một module, ví dụ `auth-flow`.

Nếu dự án lớn, chia module rõ:

```text
auth-flow
catalog-management
checkout-payment
reporting
admin-portal
```

Module artifact nằm ở:

```text
plans/{slug}-{date}/03_modules/{module_slug}/
```

Ví dụ:

```text
plans/warehouse-rfp-260525-1018/03_modules/auth-flow/
```

### Bước 5: User stories

Mục tiêu: viết user stories và acceptance criteria cho module.

Chạy:

```text
/ba-start stories --slug warehouse-rfp --module auth-flow
```

Kết quả:

```text
03_modules/auth-flow/user-stories.md
03_modules/auth-flow/user-stories-index.md
```

Review:

- mỗi story có actor rõ
- acceptance criteria test được
- không bundle nhiều intent trong một story
- priority rõ
- trace về business goal hoặc requirement

### Bước 6: FRD nếu cần

FRD không phải lúc nào cũng bắt buộc. Dùng khi stakeholder/business cần review chức năng theo module.

Chạy:

```text
/ba-start frd --slug warehouse-rfp --module auth-flow
```

Kết quả:

```text
03_modules/auth-flow/frd.md
```

FRD nên đọc được bởi business, không nên quá kỹ thuật.

### Bước 7: SRS

SRS là bước quan trọng nhất nếu module có behavior phức tạp, UI, validation, integration, hoặc cần handoff cho dev/test.

Chạy:

```text
/ba-start srs --slug warehouse-rfp --module auth-flow
```

Kết quả canon-first:

```text
03_modules/auth-flow/usecases/*.md
03_modules/auth-flow/screens/*.md
03_modules/auth-flow/data/erd.md
03_modules/auth-flow/flows/*.md
03_modules/auth-flow/srs-index.md
03_modules/auth-flow/srs.md
03_modules/auth-flow/srs-compile-receipt.json
```

Cách đọc:

- `usecases/*.md`: use case gốc, flow chính, alternate flow, diagram.
- `screens/*.md`: screen spec có cấu trúc, states, fields, actions, ASCII wireframe.
- `srs-index.md`: bản đồ để agent biết đọc file nào.
- `srs.md`: bản compiled đầy đủ cho reader/stakeholder/dev.
- `srs-compile-receipt.json`: bằng chứng `srs.md` được compile từ canon nào.

Quy tắc sửa:

```text
Sửa canon trước -> compile lại srs.md sau
```

Không sửa `srs.md` như tài liệu nguồn chuẩn nếu đã có `screens/` và `usecases/`.

### Bước 8: UI, ASCII wireframe, state màn hình

Trong flow mới, ASCII wireframe nằm trong screen canon:

```text
03_modules/auth-flow/screens/scr-login.md
```

Một screen nên mô tả đủ:

- default state
- empty state nếu có
- loading state nếu có
- validation error
- system error
- success message
- modal/drawer/dialog nếu ảnh hưởng flow

Nếu có modal có logic riêng, coi nó là screen riêng hoặc overlay screen riêng, không viết qua loa trong một dòng.

Ví dụ:

```text
SCR-LOGIN
SCR-FORGOT-PASSWORD-MODAL
SCR-LOGIN-ERROR
```

Nếu cần kiểm tra SRS canon:

```bash
ba-kit doctor-srs plans/warehouse-rfp-260525-1018/03_modules/auth-flow
```

Nếu output block, sửa canon rồi chạy lại `ba-start srs`.

### Bước 9: Wireframes legacy

Command này còn để tương thích project cũ:

```text
/ba-start srs --slug warehouse-rfp --module auth-flow
```

Nó chuẩn bị screen canon với ASCII bắt buộc:

```text
screens/*.md
```

Trong flow mới, đừng coi các file này là tài liệu nguồn chuẩn. Tài liệu nguồn chuẩn là:

```text
ascii-screen/*.md
usecases/*.md
srs/spec.md, srs/flows.md, srs/states.md, srs/erd.md
usecases/index.md
ascii-screen/index.md
srs.md (bản tổng hợp)
```

### Bước 10: Figma sync

Figma sync là downstream. Nghĩa là Figma không được định nghĩa requirement mới.

Command trực tiếp:

```text
/ba-figma-sync --slug warehouse-rfp --module auth-flow
```

Hoặc qua router tự nhiên:

```text
/ba-do Đồng bộ Figma cho module auth-flow của dự án warehouse-rfp
```

Input đúng cho Figma:

```text
srs-index.md
screens/*.md
DESIGN.md
shared-shell-contract.md
```

Nếu Figma khác canon, xử lý đúng là:

```text
sửa canon -> compile SRS -> sync Figma lại
```

Không làm ngược:

```text
sửa Figma -> coi đó là requirement mới
```

Guardrail kiểm tra write scope:

```bash
ba-kit check-write-scope --command figma-sync plans/{slug}-{date}/03_modules/auth-flow/screens/scr-login.md
```

Kết quả đúng là block, vì `figma-sync` không được sửa screen canon.

### Bước 11: Package bàn giao

Khi artifact đã ổn:

```text
/ba-start package --slug warehouse-rfp
```

Kết quả:

```text
04_compiled/compiled-frd.html
04_compiled/compiled-srs.html
```

HTML là bản stakeholder review/edit trong browser. Nếu muốn sửa requirement, quay lại source markdown/canon, không sửa HTML rồi coi là source chính.

## 5. Khi có thay đổi requirement

Đừng nhảy thẳng vào sửa SRS. Chạy impact trước:

```text
/ba-start impact --slug warehouse-rfp "Export CSV phải có audit log"
```

Hoặc:

```text
/ba-impact --slug warehouse-rfp "Export CSV phải có audit log"
```

Impact sẽ nói thay đổi chạm vào đâu:

- backbone
- stories
- FRD
- SRS
- screen
- wireframe/Figma downstream
- package

Sau đó chạy đúng command được đề xuất.

Ví dụ nếu impact nói chạm SRS module reporting:

```text
/ba-start srs --slug warehouse-rfp --module reporting
```

Sau cùng package lại nếu cần:

```text
/ba-start package --slug warehouse-rfp
```

## 6. Reverse BA: khi muốn dựng as-built từ hệ thống hiện có

Dùng reverse khi bạn có code/hệ thống hiện tại và muốn document lại “đang chạy như thế nào”.

Chạy:

```text
/ba-start reverse --slug warehouse-rfp
```

Sau đó xem trạng thái:

```text
/ba-start reverse status --slug warehouse-rfp
```

Nếu có drift/change cần phân loại:

```text
/ba-start reverse impact --slug warehouse-rfp
```

Lưu ý:

- Reverse chỉ ghi nhận evidence.
- Reverse không tự biến suy đoán thành requirement.
- Muốn đưa evidence vào canon thì phải promote có chủ đích.
- Future-state request không đi reverse. Dùng `impact` hoặc lifecycle forward.

## 7. Multi-BA collaboration: nhiều BA, mỗi người một module

Flow này dùng khi Lead BA chia module cho nhiều BA.

Ví dụ team có:

```text
Lead BA: giữ backbone, shared shell, package
BA A: auth-flow
BA B: checkout-payment
BA C: reporting
```

### Bước 1: Lead BA tạo project và backbone

Lead chạy:

```text
/ba-start intake /path/to/requirements.pdf
/ba-start options --slug warehouse-rfp
/ba-start options --slug warehouse-rfp --select option-02
/ba-start backbone --slug warehouse-rfp
```

Lead phải chốt trước:

- module list
- actor list
- portal matrix
- shared menu/layout
- terminology
- cross-module dependencies

Shared shell/menu phải nằm ở system layer:

```text
02_backbone/shared-shell-contract.md
02_backbone/shared-shell-index.md
designs/{slug}/DESIGN.md
```

Module BA không tự viết lại menu global trong module của mình.

### Bước 2: Mỗi BA nhận module

BA A nói:

```text
/ba-collab Tôi nhận module auth-flow
```

BA B nói:

```text
/ba-collab Tôi nhận module checkout-payment
```

BA C nói:

```text
/ba-collab Tôi nhận module reporting
```

BA-kit sẽ dùng:

```text
COLLAB-HOME.md
03_modules/{module}/MODULE-HOME.md
```

để biết ai đang làm gì.

### Bước 3: Module BA chỉ làm trong module của mình

BA A làm:

```text
/ba-start stories --slug warehouse-rfp --module auth-flow
/ba-start srs --slug warehouse-rfp --module auth-flow
```

BA B làm:

```text
/ba-start stories --slug warehouse-rfp --module checkout-payment
/ba-start srs --slug warehouse-rfp --module checkout-payment
```

BA C làm:

```text
/ba-start stories --slug warehouse-rfp --module reporting
/ba-start srs --slug warehouse-rfp --module reporting
```

Không làm:

```text
BA A sửa module checkout-payment
BA B sửa shared-shell-contract.md
BA C đổi menu global trong screen reporting
```

Nếu module cần đổi shared menu/layout, escalate cho Lead BA.

### Bước 4: Kiểm tra module trước khi gửi review

Module BA chạy:

```text
/ba-start status --slug warehouse-rfp --module auth-flow
```

Kiểm tra SRS canon:

```bash
ba-kit doctor-srs plans/warehouse-rfp-260525-1018/03_modules/auth-flow
```

Nếu pass, gửi review:

```text
/ba-collab Gửi module auth-flow cho Lead BA review
```

Kết quả thường có:

```text
delegation/review-packets/auth-flow.md
```

### Bước 5: Lead BA review cross-module

Lead xem:

```text
/ba-start status --slug warehouse-rfp
/ba-collab status --slug warehouse-rfp
```

Hoặc CLI:

```bash
ba-kit status --slug warehouse-rfp
ba-kit collab status --slug warehouse-rfp
```

Lead kiểm tra:

- module nào xong
- module nào còn blocker
- rule/message code có đụng nhau không
- shared screen có bị mô tả khác nhau không
- menu/global navigation có bị module tự định nghĩa lại không
- terminology có lệch không

Nếu phát hiện conflict, Lead sửa ở đúng layer:

- conflict global: sửa backbone/shared shell
- conflict module: trả review packet về module BA
- conflict requirement: chạy `impact`

### Bước 6: Package cuối

Khi các module đã được approve:

```text
/ba-start package --slug warehouse-rfp
```

Lead là người nên package cuối, không nên để từng module BA tự package bản final.

## 8. Git/PR trong collaboration

BA có thể dùng câu tự nhiên:

```text
Đồng bộ module reporting với main
Tạo PR cho module reporting
```

Hoặc:

```text
/ba-collab Đồng bộ module reporting với main
/ba-collab Tạo PR cho module reporting
```

Nguyên tắc:

- Commit/push/PR/merge cần user approve rõ.
- Không force push.
- Không merge khi review packet còn blocker.
- Không sửa module của người khác để “tiện”.
- Nếu conflict Git hoặc conflict nghiệp vụ, dừng và báo Lead BA.

## 9. Command cheat sheet

### Dễ nhất

```text
/ba-do Tôi có tài liệu yêu cầu mới, hãy tạo dự án BA
/ba-do Tiếp tục dự án warehouse-rfp
/ba-do Đánh giá thay đổi: ...
```

### Lifecycle chính

```text
/ba-start intake <file>
/ba-start options --slug <slug>
/ba-start options --slug <slug> --select option-02
/ba-start options --slug <slug> --skip
/ba-start backbone --slug <slug>
/ba-start stories --slug <slug> --module <module>
/ba-start frd --slug <slug> --module <module>
/ba-start srs --slug <slug> --module <module>
/ba-start package --slug <slug>
```

### Xem trạng thái

```text
/ba-start status --slug <slug>
/ba-start next --slug <slug>
```

CLI tương ứng:

```bash
ba-kit status --slug <slug>
ba-kit next --slug <slug>
```

### Change request

```text
/ba-start impact --slug <slug> "Nội dung thay đổi"
/ba-impact --slug <slug> "Nội dung thay đổi"
```

### Collaboration

```text
/ba-collab Tôi nhận module <module>
/ba-collab Gửi module <module> cho Lead BA review
/ba-collab Đồng bộ module <module> với main
/ba-collab Tạo PR cho module <module>
```

### Figma sync

```text
/ba-figma-sync --slug <slug> --module <module>
/ba-do Đồng bộ Figma cho module <module> của dự án <slug>
```

### Reverse

```text
/ba-start reverse --slug <slug>
/ba-start reverse status --slug <slug>
/ba-start reverse impact --slug <slug>
```

### Guardrails

```bash
ba-kit doctor
ba-kit doctor-srs plans/{slug}-{date}/03_modules/{module}
ba-kit check-prereq srs --slug <slug> --module <module>
ba-kit check-write-scope --command figma-sync <path>
```

## 10. Những lỗi người mới hay mắc

### Lỗi 1: Sửa thẳng `srs.md`

Nếu đã có `screens/` và `usecases/`, đừng sửa `srs.md` như tài liệu nguồn chuẩn.

Làm đúng:

```text
sửa screen/usecase canon
-> /ba-start srs --slug <slug> --module <module>
```

### Lỗi 2: Mỗi module tự định nghĩa menu

Menu/global layout phải ở shared shell:

```text
02_backbone/shared-shell-contract.md
```

Module chỉ reference, không redefine.

### Lỗi 3: Bỏ qua state màn hình

Screen không chỉ có happy path. Phải nghĩ đến:

- empty
- loading
- validation error
- permission denied
- server error
- success
- modal/drawer/dialog

Nếu state quan trọng không có trong ASCII/Figma, người xem sẽ hiểu sai.

### Lỗi 4: Dùng `wireframes` như flow chính

`wireframes` là legacy transitional. Flow chính là SRS canon + ASCII + optional Figma downstream.

### Lỗi 5: Có thay đổi nhưng không chạy impact

Nếu stakeholder đổi ý, chạy impact trước. Đừng tự sửa một file rồi quên các file liên quan.

### Lỗi 6: Multi-BA nhưng không có owner rõ

Mỗi module cần owner rõ. Nếu không, hai BA rất dễ sửa đè nhau hoặc dùng thuật ngữ khác nhau.

## 11. Flow mẫu hoàn chỉnh

Solo BA:

```text
/ba-start intake requirements.pdf
/ba-start options --slug warehouse-rfp
/ba-start options --slug warehouse-rfp --select option-02
/ba-start backbone --slug warehouse-rfp
/ba-start stories --slug warehouse-rfp --module auth-flow
/ba-start srs --slug warehouse-rfp --module auth-flow
/ba-start status --slug warehouse-rfp
/ba-start package --slug warehouse-rfp
```

Multi-BA:

```text
Lead:
/ba-start intake requirements.pdf
/ba-start backbone --slug warehouse-rfp

BA A:
/ba-collab Tôi nhận module auth-flow
/ba-start stories --slug warehouse-rfp --module auth-flow
/ba-start srs --slug warehouse-rfp --module auth-flow
/ba-collab Gửi module auth-flow cho Lead BA review

BA B:
/ba-collab Tôi nhận module checkout-payment
/ba-start stories --slug warehouse-rfp --module checkout-payment
/ba-start srs --slug warehouse-rfp --module checkout-payment
/ba-collab Gửi module checkout-payment cho Lead BA review

Lead:
/ba-collab status --slug warehouse-rfp
/ba-start package --slug warehouse-rfp
```

Change request sau khi đã có SRS:

```text
/ba-start impact --slug warehouse-rfp "Admin cần export report CSV có audit log"
/ba-start srs --slug warehouse-rfp --module reporting
/ba-start package --slug warehouse-rfp
```

## 12. Rule cuối cùng

Nếu bối rối, chạy theo thứ tự này:

```text
/ba-start status --slug <slug>
/ba-start next --slug <slug>
```

Sau đó làm đúng command mà `next` đề xuất. Đừng đoán.
