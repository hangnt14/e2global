<purpose>
Translate BA-friendly collaboration intent into safe module ownership, review, and optional GitHub handoff steps.

This workflow hides Git mechanics from non-technical BAs. It may update local collaboration artifacts, but external side effects require explicit approval.
</purpose>

<required_reading>
Read `contract.yaml`, `contract-behavior.md`, and the relevant `PROJECT-HOME.md` / `COLLAB-HOME.md` / `MODULE-HOME.md` when present.
</required_reading>

<process>

<step name="resolve">
Resolve slug/date/module exactly. If the user names a module, prefer that module. If multiple projects or modules match, stop and ask.
</step>

<step name="preflight">
After resolving slug/date, run a lightweight index preflight before broad reads:

1. Run: `ba-kit guardrail --command status --slug <slug> --date <date> [--module <module>]`.
2. If `status=block`:
   - Print compact advisory (≤150 chars):
     "BA-kit indexes missing. Run: python3 scripts/context-budget-bootstrap.py --repo . --slug {slug} --date {date} [--module {module}]"
   - Continue — do NOT block the collab request.
3. If `status=warn`:
   - Print: "Some indexes stale. Consider: python3 scripts/validate-index-quality.py --repo . --slug {slug} --date {date} --index-key <key> --writeback"
   - Continue.
4. If `status=ok`: proceed silently.

This step is advisory only (warn, don't block). The goal is to prevent accidental broad file reads in legacy projects, not to stop collaboration.
</step>

<step name="classify_intent">
Map the user text using the first matching intent:

| BA says | Internal action |
| --- | --- |
| create collaboration workspace / chia module / setup teamwork | initialize `COLLAB-HOME.md` with module inventory only. Do NOT create module directories or MODULE-HOME.md yet |
| tôi nhận module X / assign module X cho Y | claim module X. Create `03_modules/X/` directory + `MODULE-HOME.md` for X only. Do NOT pre-create subdirs — lifecycle steps create their own subdirs (stories → userstories/, srs → usecases/, ascii-screen/, srs/) |
| kiểm tra module X trước review / có conflict không | pre-review check |
| làm xong module X / gửi Lead BA review | create review packet; optional PR only after approval |
| cập nhật theo feedback / changes requested | mark changes-requested or in-progress |
| approve module X | mark approved; Lead BA only |
| tổng hợp module đã approve / integrated | mark integrated after assembly/merge confirmation |
| tạo PR / push lên GitHub / merge | external GitHub handoff; require explicit approval |
</step>

<step name="safe_execution">
Allowed local mutations:
- create or refresh `paths.collab_home` from `templates/collab-home-template.md` (setup teamwork only)
- create or refresh `paths.module_home` from `templates/module-home-template.md` ONLY when a specific module is claimed. Do NOT batch-create module homes during setup
- create `03_modules/{module_slug}/` directory + `paths.module_home` ONLY on claim, never during setup. Do NOT pre-create subdirs (screens/, userstories/, usecases/, ascii-screen/, srs/) — lifecycle steps own their subdirs
- create or refresh `paths.review_packet` from `templates/review-packet-template.md`
- update module status only as: unassigned, assigned, in-progress, ready-for-review, changes-requested, approved, integrated, blocked
- update review status only as: none, local-packet, draft-pr, review-requested, changes-requested, approved, merged, conflict

Never mutate lifecycle artifacts directly from collab intent. If the request changes requirements, route `impact` first.
</step>

<step name="ownership_checks">
Before marking ready-for-review or approved:
- verify the module has an owner
- verify changed paths are inside `03_modules/{module_slug}/` unless Lead BA approved escalation
- flag changes to backbone, hot/global memory, or other modules as cross-module escalation
- flag L2 nav-item additions to DESIGN.md and shared-shell-contract.md in review packet for Lead BA visibility (these are allowed with user confirmation, not blocked)
- flag L1 portal/nav-schema/shell-variant additions to DESIGN.md as cross-module escalation (these require Lead BA)
- flag possible duplicate `CR-*` / `MSG-*` codes when detectable
</step>

<step name="external_side_effect_gate">
Commit, push, PR creation, reviewer request, and merge are external side effects.

Before any of them:
1. Print the exact action plan.
2. Print files to be included.
3. Print proposed branch/commit/PR title when relevant.
4. Ask for explicit approval.
5. If approval is absent, stop after local review packet creation.
</step>

<step name="display">
Print a BA-friendly result:

```text
BA Collaboration

Project: {slug}
Module: {module}
Action: {friendly action}
Status: {collab_module status}
Review: {collab_review status}
Updated: {paths updated}
Next: {next BA-friendly step}
External GitHub action: {not requested | approval required | completed}
```
</step>

</process>

<success_criteria>
- [ ] Project/module resolved exactly or ambiguity surfaced
- [ ] Local collaboration artifacts updated only when safe
- [ ] Requirement changes routed through impact
- [ ] GitHub side effects gated by explicit approval
- [ ] BA-facing statuses shown without requiring Git vocabulary
</success_criteria>
