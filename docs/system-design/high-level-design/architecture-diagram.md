# Architecture Diagram - Restaurant Management System

```mermaid
flowchart TB
    subgraph access[Access Channels]
        guestTouchpoints[Guest Touchpoints]
        pos[Staff POS / Backoffice]
        kds[Kitchen Display System]
    end

    subgraph platform[Core Platform]
        gateway[API Gateway]
        identity[Identity and Branch Access]
        seating[Reservation and Seating Service]
        menu[Menu and Pricing Service]
        order[Order and Service Service]
        kitchen[Kitchen Routing Service]
        inventory[Inventory and Recipe Service]
        procurement[Procurement Service]
        billing[Billing and Settlement Service]
        workforce[Workforce Scheduling Service]
        accounting[Accounting Export Service]
        notification[Notification Service]
        reporting[Reporting and Analytics Projection]
    end

    subgraph data[Data Layer]
        pg[(PostgreSQL)]
        bus[(Message Bus)]
        report[(Reporting Store)]
        object[(Object Storage)]
    end

    guestTouchpoints --> gateway
    pos --> gateway
    kds --> gateway
    gateway --> identity
    gateway --> seating
    gateway --> menu
    gateway --> order
    gateway --> kitchen
    gateway --> inventory
    gateway --> procurement
    gateway --> billing
    gateway --> workforce
    gateway --> accounting
    menu --> pg
    seating --> pg
    order --> pg
    kitchen --> pg
    inventory --> pg
    procurement --> pg
    billing --> pg
    workforce --> pg
    accounting --> pg
    order --> bus
    kitchen --> bus
    inventory --> bus
    billing --> bus
    workforce --> bus
    bus --> notification
    bus --> reporting
    reporting --> report
    procurement --> object
```

## Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Reservation and Seating Service | Reservations, walk-ins, waitlist, table assignment |
| Menu and Pricing Service | Menus, modifiers, taxes, discounts, availability |
| Order and Service Service | Guest checks, table orders, course timing, status tracking |
| Kitchen Routing Service | Ticket routing, station queues, prep status, refire handling |
| Inventory and Recipe Service | Ingredient stock, BOM usage, wastage, transfer and count logic |
| Procurement Service | Vendors, purchase orders, receiving, discrepancy handling |
| Billing and Settlement Service | Bills, taxes, split settlement, refunds, drawer sessions |
| Workforce Scheduling Service | Shift planning, attendance, operational staffing visibility |
| Accounting Export Service | Reconciliation outputs and external finance handoff |
