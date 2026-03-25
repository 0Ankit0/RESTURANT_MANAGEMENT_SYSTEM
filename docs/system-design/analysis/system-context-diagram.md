# System Context Diagram - Restaurant Management System

```mermaid
flowchart LR
    guests[Guests / Customers]
    staff[Hosts, Waiters, Chefs, Cashiers, Managers]
    payment[Payment Provider]
    accounting[External Accounting System]
    vendors[Suppliers / Vendors]
    delivery[Delivery Aggregator / Channel]
    devices[POS Devices, KDS, Printers]

    subgraph rms[Restaurant Management System]
        guestTouchpoints[Guest Touchpoints]
        staffApps[Staff POS and Backoffice]
        api[Application API]
        reporting[Reporting and Analytics]
    end

    guests --> guestTouchpoints
    staff --> staffApps
    guestTouchpoints --> api
    staffApps --> api
    api --> payment
    api --> accounting
    api --> vendors
    api --> delivery
    api --> devices
    api --> reporting
```

## Context Notes

- Guests interact through lightweight reservation, waitlist, and order-status touchpoints rather than a full guest application stack.
- Staff use branch operational tools for front-of-house, kitchen, inventory, cashiering, and management workflows.
- The system integrates with payments, accounting exports, supplier processes, delivery channels, and restaurant devices.
