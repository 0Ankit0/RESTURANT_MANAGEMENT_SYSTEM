# API Design - Restaurant Management System

## API Style
- RESTful JSON APIs with branch-aware authorization and role-based access checks.
- Cursor pagination for activity-heavy collections such as orders, tickets, stock movements, and settlements.
- Idempotency keys for order submission, bill closure, goods receipt, and accounting export generation.
- Operational dashboards may use projected reads, but order, bill, and stock decisions should rely on authoritative transactional data.

## Core Endpoints

| Area | Method | Endpoint | Purpose |
|------|--------|----------|---------|
| Reservations | POST | `/api/v1/reservations` | Create reservation |
| Seating | POST | `/api/v1/tables/{tableId}/seat` | Seat party at table |
| Orders | POST | `/api/v1/orders` | Create or submit order |
| Orders | PATCH | `/api/v1/orders/{orderId}` | Update order items or status |
| Kitchen | GET | `/api/v1/kitchen/tickets` | Retrieve station queue |
| Kitchen | PATCH | `/api/v1/kitchen/tickets/{ticketId}` | Update preparation state |
| Inventory | GET | `/api/v1/inventory/ingredients` | List ingredient stock |
| Inventory | POST | `/api/v1/inventory/adjustments` | Record adjustment or wastage |
| Procurement | POST | `/api/v1/purchase-orders` | Create purchase order |
| Procurement | POST | `/api/v1/purchase-orders/{poId}/receipts` | Record goods receipt |
| Billing | POST | `/api/v1/bills/{billId}/settlements` | Record settlement |
| Cashier | POST | `/api/v1/drawer-sessions/{sessionId}/close` | Close drawer session |
| Workforce | POST | `/api/v1/shifts` | Create shift |
| Reports | GET | `/api/v1/reports/branch-operations` | Branch operational summary |
| Admin | PATCH | `/api/v1/admin/branch-policies/{policyId}` | Update branch or global policy |

## Example: Create Order

```json
{
  "branchId": "br_01",
  "orderSource": "dine_in",
  "tableId": "tbl_12",
  "waiterId": "usr_waiter_4",
  "items": [
    {
      "menuItemId": "item_pasta",
      "quantity": 2,
      "courseNo": 1,
      "modifierIds": ["mod_no_cheese"],
      "notes": "One spicy, one mild"
    }
  ]
}
```

## Example: Close Bill

```json
{
  "billId": "bill_2001",
  "settlements": [
    { "paymentMethod": "card", "amount": 58.50 },
    { "paymentMethod": "cash", "amount": 10.00 }
  ],
  "cashierId": "usr_cash_7"
}
```

## Authorization Notes
- Guest-facing APIs are limited to reservations, waitlists, and scoped order-status touchpoints.
- Waiters, hosts, chefs, cashiers, and inventory managers operate within branch-scoped permissions.
- Refunds, post-close adjustments, accounting exports, and policy changes require elevated roles and audit logging.
