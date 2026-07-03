<purpose>
Run BA change-impact triage for an existing project set.

This command is the safe landing zone for:
- new requirements
- changed rules
- removed scope items
- bare correction statements such as "Khong co nhom admin user"

It must not mutate artifacts. It analyzes impact first, then returns the next commands.

Reverse lane note: when the project has an active reverse lane (`reverse_baseline_lock` exists),
impact classification must distinguish between:
- `as_built_drift` — behavior exists in code but is absent from or contradicts the documented baseline
- `future_state_request` — desired behavior not yet implemented in code
- `mixed_change` — contains both as-built and future-state elements

Route `as_built_drift` to `ba-start reverse promote`. Route `future_state_request` to the forward
lifecycle. Never merge the two lanes in a single rerun recommendation.
</purpose>

<required_reading>
Read the installed BA playbook, `contract.yaml`, and `contract-behavior.md` before doing anything else.
</required_reading>

<process>

<step name="load_contract">
Read:
- the installed `ba-start` skill from the same runtime
- `contract.yaml` from the installed BA core
- `contract-behavior.md` from the installed BA core

Use the `impact` subcommand contract in `ba-start` as the authoritative decision logic.
</step>

<step name="validate_input">
If the command arguments or the attached user text do not contain any change statement, ask one concise question:

"What changed? Paste the new requirement, correction, or rule update and I will analyze the impact."
</step>

<step name="resolve_project">
Resolve the target slug and dated set using the artifact contract.

Rules:
- Prefer explicit `--slug` when present
- Otherwise inspect the current workspace for exact BA-kit artifacts
- If slug or dated set is ambiguous, stop and ask the user to choose
- If only legacy artifacts exist, stop and report that the project must be migrated or rerun under the current contract
</step>

<step name="triage">
Execute the equivalent of `/ba-start impact --slug <slug>` using the resolved project set and the change statement.

Follow the `impact` logic from `ba-start` exactly:
- determine the current source of truth
- classify the change
- list affected and unaffected artifacts
- recommend the narrowest safe rerun path
- print exact commands

Reverse lane classification (apply when `reverse_baseline_lock` exists):
- Inspect whether the change describes behavior already present in committed source code (`as_built_drift`),
  desired behavior not yet in code (`future_state_request`), or both (`mixed_change`).
- `as_built_drift` → next command: `ba-start reverse promote --slug <slug> --evidence-ids <ids>`
- `future_state_request` → next command: forward lifecycle (backbone / stories / srs as appropriate)
- `mixed_change` → must be split first: `ba-start reverse impact --slug <slug> --evidence-ids <ids>`
- If a reverse guardrail is the blocker, print its exact code before any rerun command:
  `FOCUS_SELECTION_REQUIRED`, `REVERSE_REFRESH_REQUIRED`, `REVERSE_TRACE_COVERAGE_REQUIRED`, or `REVERSE_READ_SCOPE_ESCALATION`.
- Never recommend a single rerun path that merges as-built and future-state changes.
- Do not mutate canonical artifacts (backbone, SRS, FRD) during classification.

Do not apply edits during this command.
</step>

<step name="finish">
Return only the impact analysis and next commands.
Do not ask a generic "what do you want me to do next?" question unless the triage itself requires clarification.
</step>

</process>

<success_criteria>
- [ ] Project set resolved exactly or ambiguity surfaced explicitly
- [ ] Change classified without mutating artifacts
- [ ] Current source of truth identified
- [ ] Reverse lane classification applied when reverse_baseline_lock exists
- [ ] as_built_drift and future_state_request never merged into a single rerun path
- [ ] Affected and unaffected artifacts listed
- [ ] Exact next commands printed
</success_criteria>
