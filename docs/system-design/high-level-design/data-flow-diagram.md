# Data Flow Diagram - Restaurant Management System

```mermaid
flowchart LR
    guest[Guest Touchpoints] --> api[Application API]
    staff[Staff POS and Backoffice] --> api
    kitchen[KDS / Kitchen Display] --> api
    api --> seating[Reservation and Seating Service]
    api --> order[Order and Service Service]
    api --> inventory[Inventory and Recipe Service]
    api --> billing[Billing and Settlement Service]
    api --> workforce[Workforce Service]
    seating --> db[(PostgreSQL)]
    order --> db
    inventory --> db
    billing --> db
    workforce --> db
    order --> bus[(Event Bus)]
    inventory --> bus
    billing --> bus
    workforce --> bus
    bus --> notify[Notification Service]
    bus --> reporting[Reporting and Analytics]
    reporting --> warehouse[(Reporting Store)]
```

## Data Flow Notes

1. Service, kitchen, inventory, settlement, and workforce events are treated as operationally linked streams.
2. Transactional consistency remains in the primary database while reporting and analytics consume projected events.
3. Inventory visibility should be fast enough to influence order capture and kitchen execution before settlement time.
