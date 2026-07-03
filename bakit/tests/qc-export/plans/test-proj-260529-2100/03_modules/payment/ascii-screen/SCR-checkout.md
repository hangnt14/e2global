---
type: screen
screen_id: SCR-checkout
module: payment
status: draft
created: "2026-05-29"
owner: "@tester"
---

# SCR-checkout: Checkout Screen

## Field Table

| Field | Type | Validation Rules |
|-------|------|-----------------|
| Order Total | Display | Auto-calculated from cart |
| Payment Method | Select | Required, CR-VAL-01 applies |
| Confirm Button | Action | Enabled when method selected |

## Error States

- MSG-ERR-01: Cart is empty — cannot checkout.
- MSG-ERR-02: Payment failed — please try again.

## Behaviour Rules

- Confirm button is disabled until payment method is selected (CR-VAL-01).
