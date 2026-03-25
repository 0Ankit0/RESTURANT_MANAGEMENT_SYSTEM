# Domain Model - Restaurant Management System

## Core Domain Areas

| Domain Area | Key Concepts |
|-------------|--------------|
| Branch and Workforce | Branch, ServiceZone, StaffUser, Shift, AttendanceRecord |
| Guest Service | Reservation, WaitlistEntry, Table, Order, OrderItem |
| Kitchen Execution | KitchenTicket, Station, FireRule, PreparationState |
| Menu and Pricing | MenuItem, Category, ModifierGroup, PriceRule, TaxRule |
| Inventory and Procurement | Ingredient, Recipe, StockLedgerEntry, PurchaseOrder, GoodsReceipt |
| Billing and Accounting | Bill, Settlement, CashDrawerSession, AccountingExport |
| Operations | Notification, AuditLog, DashboardMetric |

## Relationship Summary
- A **branch** owns tables, shifts, stock, orders, bills, and drawer sessions.
- An **order** contains many order items and may generate many kitchen tickets and settlements.
- A **menu item** may depend on a recipe composed of many ingredients.
- **Accounting exports** aggregate settlement and reconciliation outcomes without becoming a full general ledger.

```mermaid
erDiagram
    BRANCH ||--o{ TABLE : contains
    BRANCH ||--o{ STAFF_USER : employs
    BRANCH ||--o{ ORDER : serves
    BRANCH ||--o{ INGREDIENT : stocks
    BRANCH ||--o{ CASH_DRAWER_SESSION : runs
    TABLE ||--o{ ORDER : hosts
    ORDER ||--o{ ORDER_ITEM : contains
    ORDER_ITEM ||--o{ KITCHEN_TICKET : routes
    MENU_ITEM ||--o{ ORDER_ITEM : sells
    MENU_ITEM ||--o{ RECIPE : defines
    RECIPE ||--o{ INGREDIENT : consumes
    BILL ||--o{ SETTLEMENT : settles
```
