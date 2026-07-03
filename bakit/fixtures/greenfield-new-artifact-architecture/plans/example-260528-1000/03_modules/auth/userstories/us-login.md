---
type: user-story
module: auth
story_id: US-001
slug: login
actor: End User
priority: P0
status: completed
source_backbone_ids: [auth-login]
linked_usecases: [UC-login]
linked_screens: [SCR-01]
created: 2026-05-28
owner: "@ba"
changelog:
  - 2026-05-28 | /stories | initial draft
---

# US-001: Login

## Story Statement

As an **End User**, I want to **log in with email and password**, so that **I can access my account**.

## Acceptance Criteria

- [ ] AC-001: User can enter email and password and submit the login form.
- [ ] AC-002: System shows error message MSG-ERR-01 when credentials are invalid.
- [ ] AC-003: User is redirected to dashboard on successful login.

## Trace

- Backbone feature/scope: auth-login
- FRD reference: FR-auth-001
