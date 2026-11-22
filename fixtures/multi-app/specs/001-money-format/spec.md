---
spec: 001-money-format
tier_declared: high
owner_role: platform
principles: [P-1]
paths: ["packages/shared-lib/*"]
touches: [shop-shared-lib]
---
# Feature Specification: Currency-aware money formatting

## Requirements
- **FR-001**: The shared library MUST format an amount with its currency code.

## Acceptance Criteria
- **AC-001** (verifies FR-001): Given 1250 cents and "USD", When formatted, Then the result is "12.50 USD".
