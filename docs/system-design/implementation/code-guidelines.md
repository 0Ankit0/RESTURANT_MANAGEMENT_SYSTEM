# Code Guidelines - Restaurant Management System

## Reference Implementation Stack
- Frontend: React + TypeScript for staff POS, backoffice, kitchen display, and limited guest touchpoints
- Backend: TypeScript service layer (for example NestJS) with modular domain packages
- Persistence: PostgreSQL for transactional data, reporting store for projections, object storage for exports and print artifacts
- Async processing: queue + workers for kitchen/status fanout, notifications, accounting exports, and reporting updates

## Suggested Repository Structure

```text
restaurant-platform/
├── apps/
│   ├── guest-touchpoints/
│   ├── staff-pos/
│   ├── kitchen-display/
│   ├── backoffice/
│   ├── api/
│   └── worker/
├── packages/
│   ├── domain/
│   │   ├── access/
│   │   ├── seating/
│   │   ├── menu/
│   │   ├── orders/
│   │   ├── kitchen/
│   │   ├── inventory/
│   │   ├── procurement/
│   │   ├── billing/
│   │   ├── workforce/
│   │   └── reporting/
│   ├── ui/
│   └── shared/
├── infra/
└── tests/
```

## Domain Boundaries
- Keep seating, orders, kitchen, inventory, procurement, billing, workforce, and access control in separate domain modules.
- Use domain events for reporting, low-stock notifications, KDS fanout, and accounting exports instead of overloading synchronous transaction paths.
- Avoid exposing cashier, accounting, or approval-only fields through waiter or guest-facing DTOs.

## Backend Guidelines
- Treat branch scoping and shift/session context as first-class concerns on every command and query.
- Keep tax, discount, approval, and settlement calculations inside explicit policy services.
- Preserve immutable ledger-style histories for stock movements, settlements, refunds, and reconciliation adjustments.
- Model recipe versions explicitly so inventory consumption remains historically interpretable.

## Frontend Guidelines
- Optimize POS interactions for fast tablet use with minimal steps and strong conflict handling.
- Optimize KDS for glanceability, station routing, and rapid status transitions.
- Optimize backoffice screens for filtering, reconciliation, procurement, and branch visibility.

## Example Domain Types

```ts
export type OrderStatus =
  | 'draft'
  | 'submitted'
  | 'in_preparation'
  | 'ready'
  | 'served'
  | 'billed'
  | 'settled'
  | 'voided';

export interface CreateOrderCommand {
  branchId: string;
  orderSource: 'dine_in' | 'takeaway' | 'delivery';
  tableId?: string;
  waiterId: string;
  items: Array<{
    menuItemId: string;
    quantity: number;
    courseNo?: number;
    modifierIds: string[];
    notes?: string;
  }>;
}
```

## Testing Expectations
- Unit tests for tax, discount, routing, recipe-consumption, and reconciliation logic.
- Integration tests for reservation-to-seat, order-to-kitchen, prep-to-serve, bill-to-settlement, and PO-to-stock workflows.
- API contract tests for guest, waiter, kitchen, cashier, and backoffice endpoints.
- E2E tests for full-service dine-in, takeaway, stockout handling, refund/void approval, and branch day-close flows.
