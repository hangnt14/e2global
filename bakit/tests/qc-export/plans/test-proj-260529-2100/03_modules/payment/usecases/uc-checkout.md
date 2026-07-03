---
type: use-case
module: payment
usecase_id: UC-checkout
slug: checkout
actor: Customer
status: draft
linked_stories:
  - us-001
linked_screens:
  - SCR-checkout
source_backbone_ids: []
created: "2026-05-29"
owner: "@tester"
changelog:
  - 2026-05-29 | /srs | initial draft
---

# UC-checkout: Customer Checkout

## Actors

- Primary: Customer
- Secondary: Payment Gateway

## Preconditions

- Customer is logged in
- Cart has at least one item

## Trigger

Customer taps "Checkout" button on cart screen.

## Main Flow

1. Customer taps Checkout.
2. System displays order summary with total amount.
3. Customer confirms payment.
4. System processes payment via Payment Gateway.
5. System shows order confirmation screen.

## Alternate Flows

### AF-01: Empty Cart

1. Customer taps Checkout with empty cart.
2. System shows MSG-ERR-01.

## Error / Exception Flows

### EF-01: Payment Failed

1. System calls Payment Gateway.
2. Payment Gateway returns failure.
3. System shows MSG-ERR-02 and retains cart state.

## Postconditions

- Order is created with status "paid".
- Cart is cleared.

## Cross-Function Impact

### Within Module

| Direction | UC | Data / State | Type |
|-----------|-----|--------------|------|
| Depends on | UC-cart | cart_id, cart_items | Input |
| Produces for | UC-tracking | order_id, order_status | Output |

### Across Modules

| Direction | Target Module | Expected UC / Backbone Ref | Data / State | Type |
|-----------|---------------|---------------------------|--------------|------|
| Consumes from | auth | FEAT-AUTH-03 | user_id, token | Input |
| Produces for | shipping | FEAT-SHP-01 | order_id, order_status | Output |

**Dependency Types:** `Input` (this UC needs data from another), `Output` (this UC produces data another needs), `Shared State` (both read/write same entity).

## Trace

- User stories: US-001
- Backbone feature: FEAT-PAY-01
- Screens: SCR-checkout

## Open Questions

- [ ] OQ-1: Should we support multiple payment methods in v1?
