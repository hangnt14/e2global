---
type: screen
module: auth
screen_id: SCR-01
slug: login
portal_id: PORTAL-WEB
nav_schema_id: NAV-MAIN
expected_active_menu: Login
actor: End User
ascii_status: current
status: completed
linked_usecases: [UC-login]
linked_stories: [US-001]
source_backbone_ids: [auth-login]
created: 2026-05-28
owner: "@ba"
changelog:
  - 2026-05-28 | /srs | initial draft
---

# SCR-01: Login Screen

## Overview

| Field | Value |
|---|---|
| Portal ID | PORTAL-WEB |
| Nav Schema ID | NAV-MAIN |
| Expected Active Menu Item | Login |
| Navigation Region Visible | No |
| Entry Conditions | User is not authenticated |
| Exit Conditions | Login success or cancel |
| Actor | End User |
| Linked Use Cases | UC-login |
| Linked Stories | US-001 |

## Fields

| Field Name | Display Rules | Behaviour Rules | Validation Rules |
|---|---|---|---|
| Email | Label: Email, placeholder: email@example.com | On submit, validate format | Required, valid email format, MSG-ERR-01 on invalid |
| Password | Label: Password, type: password | On submit, validate not empty | Required, MSG-ERR-01 on invalid |

## User Actions

| Action | Trigger | Outcome |
|---|---|---|
| Submit | Click Login button | System validates credentials, redirects to dashboard or shows error |

## States

| State ID | Name | Description |
|---|---|---|
| SCR-01-DEFAULT | Default | Empty form |
| SCR-01-ERROR | Error | Invalid credentials shown |

## ASCII Wireframe

### Default State

```
+--------------------------------------------------+
| Login                                            |
+--------------------------------------------------+
| Email:    [________________________]             |
| Password: [________________________]             |
|                                                  |
|           [        Login         ]               |
+--------------------------------------------------+
```

### Error State

```
+--------------------------------------------------+
| Login                                            |
+--------------------------------------------------+
| Email:    [________________________]             |
| Password: [________________________]             |
| ! Invalid email or password.                     |
|           [        Login         ]               |
+--------------------------------------------------+
```
