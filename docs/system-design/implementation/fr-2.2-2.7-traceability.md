# FR-RES/FR-MEN/FR-ORD/FR-KIT/FR-INV/FR-BIL Delivery Trace (Sections 2.2–2.7)

This document provides an implementation and behavior trace for requirement groups **FR-RES, FR-MEN, FR-ORD, FR-KIT, FR-INV, FR-BIL** in dependency order, including edge-case validation and approval/audit controls.

## 1) Reservations, Waitlist, Seating, and Table State (FR-RES)

- **Reservations**: create/get/list/update/cancel endpoints exist for branch-scoped reservations, including party size, contact fields, table assignment, and status lifecycle.  
  - Endpoints: `/reservations`, `/reservations/{id}`, `/reservations/{id}/cancel`, `/reservations/{id}` (PATCH).
- **Walk-in queue / waitlist**: create/list/promote flow with status management and cursor pagination.  
  - Endpoints: `/waitlist`, `/waitlist/{id}/promote`.
- **Seating + table state**: seat and release endpoints enforce capacity checks and status transitions (`available`, `occupied`, `reserved`, `out_of_service`) with seating decision logic.
- **Edge-case coverage**:
  - party exceeds table capacity -> seat blocked.
  - host/waiter conflict mitigation via state checks and explicit seat/release transitions.
  - walk-in queue promotion + table occupancy synchronization.

## 2) Menu, Pricing, Modifiers, Tax Versions (FR-MEN)

- **Branch-aware menu and modifiers**:
  - menu items, categories, modifier groups/options are branch or menu scoped and queryable.
- **Pricing/tax**:
  - line totals are computed from price × quantity.
  - bill generation applies branch tax + service charge.
  - explicit tax-rule entity supports **versioned tax definitions** and effective timestamps.
- **Recipe/BOM mapping**:
  - recipe + recipe-items connect menu items to ingredient depletion logic.
- **Availability and historical continuity**:
  - menu items support availability flags; historical records remain immutable through order/bill references.

## 3) Order Lifecycle, Seat/Course Controls, Approvals (FR-ORD)

- **Order lifecycle**:
  - order creation/update/listing includes source distinction (`dine_in`, `takeaway`, `delivery`) and status transitions.
- **Course controls**:
  - order items support course numbers and notes/special requests.
- **Post-fire edit approval controls**:
  - editing fired items requires approved `OrderEditApproval`.
- **Void/cancel controls**:
  - cancelling submitted/in-progress/ready/served orders now requires approved `OrderEditApproval` (controlled void workflow).
- **Edge-case coverage**:
  - kitchen-fired edits blocked unless approval exists.
  - delivery-source order path validated distinctly from dine-in/takeaway.

## 4) Kitchen Routing and Ticket State Machine (FR-KIT)

- **Kitchen ticket routing**:
  - order submission emits kitchen tickets with status, station, and priority metadata.
- **Ticket state machine**:
  - allowed transitions are validated before status mutation.
  - ticket events persist `from_status -> to_status` history.
- **Preparation exceptions**:
  - delayed/voided/ready/served states are represented and queryable.
- **Edge-case coverage**:
  - stale or invalid transitions are rejected.
  - post-fire change controls prevent silent desync between FOH and KDS.

## 5) Recipe Depletion, Receiving, Counts, Transfers (FR-INV)

- **Recipe depletion**:
  - order submission depletes ingredients using active recipe versions.
  - order cancellation reversal compensates stock through explicit ledger entries.
- **Receiving/procurement**:
  - purchase order + line receiving + goods receipt support discrepancy workflows.
- **Stock counts and variance**:
  - stock count sessions/lines track expected vs counted vs variance; approvals apply final counted quantities and ledger variance events.
- **Transfers**:
  - transfer lifecycle supports requested -> in_transit -> received/rejected with discrepancy notes and mirrored stock ledger movement.
- **Sensitive controls**:
  - manual inventory adjustments require `approved_by` and emit privileged audit records with actor attribution.

## 6) Billing, Splits, Refunds, Cash Sessions, Day-Close, Reconciliation (FR-BIL)

- **Billing and settlements**:
  - bill generation supports tax/service computation and multi-settlement updates with partial/full paid statuses.
- **Refund controls**:
  - refunds enforce amount <= paid amount, require a reason, require approver attribution, and are audited.
  - post-close refunds are flagged in audit payload as supervised adjustments.
- **Drawer sessions and reconciliation override**:
  - open/close drawer session workflow.
  - reconciliation overrides require explicit reason + approver and are fully audited.
- **Daily close and accounting export**:
  - day-close blocks closure when drawers/bills are open and enforces checklist completion.
  - accounting exports are generated and retry-tracked (idempotent create path supported).

## 7) End-to-End Trace: Reservation/Walk-in to Settlement + Accounting Trail

Implemented trace path now includes:

1. Reservation or walk-in waitlist creation.
2. Seating and table occupancy state update.
3. Order creation with source + course metadata.
4. Kitchen ticket generation and state transitions.
5. Recipe-based depletion and stock ledger writes.
6. Bill generation and settlement application.
7. Sensitive operations (void, refund, stock adjustments, reconciliation overrides) gated by approval fields and privileged audit writes.
8. Day-close and accounting export/retry records for accounting-ready handoff.

## 8) Edge-Case Validation Focus

The integration suite now explicitly validates:

- kitchen-fired edit/cancel approval enforcement,
- stock adjustment approval attribution,
- refund reason + post-close supervision signal,
- reconciliation override approval requirement,
- delivery-source differentiation in order flow,
- privileged audit visibility for sensitive events.
