# Business Rules - Restaurant Management System

## Reservation and Table Rules
- A reservation may hold a table window only within configured grace and no-show periods.
- A table cannot be assigned to more than one active party unless explicitly merged by authorized staff.
- Waitlist promotion should consider party size, table fit, and reservation priority rules.

## Order and Service Rules
- Orders may be edited before kitchen fire without elevated approval, but post-fire changes require policy-driven control.
- Discounts, voids, or complimentary items above configured thresholds require manager approval.
- Seat-level or course-level ordering must preserve guest-level service context for billing and kitchen routing.

## Kitchen Rules

| Rule Area | Baseline Rule |
|-----------|---------------|
| Station routing | Each order item routes to one or more stations based on menu and recipe configuration |
| Ticket priority | Driven by service type, course timing, and branch policy |
| Stock shortage | Shortage must surface before or during prep with an auditable exception path |
| Refire | Refire events require cause capture and do not silently overwrite original preparation history |

## Inventory and Procurement Rules
- Ingredient stock must remain traceable through receipt, usage, wastage, transfer, and adjustment events.
- Negative stock should be blocked or escalated according to branch policy.
- Goods receipts that differ from purchase orders must remain auditable and visible for reconciliation.

## Billing and Accounting Rules
- Bill closure requires tax and payment totals to reconcile to order value after valid discounts and adjustments.
- Refunds, post-close voids, and reconciliation overrides require role-based approval and audit logs.
- Operational accounting exports must preserve traceability back to bills, settlements, and drawer sessions.

## Workforce Rules
- Shift schedules do not imply payroll but must support staffing visibility and attendance completeness.
- Day close should surface unresolved open shifts, unsettled orders, or unbalanced drawer sessions before final approval.
