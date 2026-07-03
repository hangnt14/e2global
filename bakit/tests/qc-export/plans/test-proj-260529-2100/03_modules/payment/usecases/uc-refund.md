---
type: use-case
module: payment
usecase_id: UC-refund
slug: refund
actor: Admin
status: draft
linked_stories:
  - us-002
linked_screens: []
source_backbone_ids: []
created: "2026-05-29"
owner: "@tester"
changelog:
  - 2026-05-29 | /srs | initial draft
---

# UC-refund: Process Refund

## Actors

- Primary: Admin
- Secondary: Payment Gateway

## Preconditions

- Order exists with status "paid".
- Admin has refund permission.

## Trigger

Admin selects "Refund" on order details screen.

## Main Flow

1. Admin selects Refund action.
2. System confirms refund amount.
3. Admin confirms.
4. System processes refund via Payment Gateway.
5. System shows CR-VAL-01 confirmation.

## Postconditions

- Order status updated to "refunded".
- Customer receives refund notification.

## Cross-Function Impact

### Within Module

| Direction | UC | Data / State | Type |
|-----------|-----|--------------|------|
| Depends on | UC-checkout | order_id, order_status | Input |

### Across Modules

| Direction | Target Module | Expected UC / Backbone Ref | Data / State | Type |
|-----------|---------------|---------------------------|--------------|------|
| None | — | — | — | — |

## Trace

- User stories: US-002
- Backbone feature: FEAT-PAY-02

## Open Questions

- [ ] OQ-1: What is the refund SLA?
