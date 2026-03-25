# Component Diagram - Restaurant Management System

```mermaid
flowchart LR
    ui[Guest Touchpoints / POS / Backoffice / KDS] --> api[API Layer]
    api --> auth[Access Control Component]
    api --> seating[Reservation and Seating Component]
    api --> menu[Menu and Pricing Component]
    api --> order[Order and Service Component]
    api --> kitchen[Kitchen Routing Component]
    api --> inventory[Inventory and Recipe Component]
    api --> procurement[Procurement Component]
    api --> billing[Billing and Settlement Component]
    api --> workforce[Shift and Attendance Component]
    api --> reporting[Reporting Component]
    order --> kitchen
    order --> inventory
    billing --> reporting
```

## Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Access Control | Authentication, branch scoping, approval gates |
| Reservation and Seating | Reservations, walk-ins, waitlist, table assignment |
| Menu and Pricing | Menus, modifiers, taxes, discounts, availability |
| Order and Service | Order capture, table checks, service events |
| Kitchen Routing | Station routing, prep states, readiness signals |
| Inventory and Recipe | Ingredients, recipe usage, stock movements |
| Procurement | Vendors, POs, receipts, discrepancies |
| Billing and Settlement | Bills, payments, refunds, drawer sessions |
| Shift and Attendance | Scheduling, attendance, staffing visibility |
| Reporting | Sales, delays, variance, operational dashboards |
