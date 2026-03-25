# Deployment Diagram - Restaurant Management System

```mermaid
flowchart TB
    guestNet[Guest Internet / Mobile] --> edge[WAF / CDN]
    branchLan[Branch LAN / POS Network] --> branchAccess[Branch Access Gateway]
    edge --> guestUI[Guest Touchpoints]
    branchAccess --> posUI[POS and Backoffice Apps]
    branchAccess --> kdsUI[Kitchen Display System]
    branchAccess --> printer[Receipt / Kitchen Printers]
    guestUI --> api[Application API Cluster]
    posUI --> api
    kdsUI --> api
    api --> workers[Background Worker Cluster]
    api --> db[(Managed PostgreSQL)]
    api --> queue[(Managed Queue / Bus)]
    api --> report[(Reporting Store)]
    api --> object[(Object Storage)]
    workers --> db
    workers --> queue
    workers --> report
```

## Deployment Notes

- Branch devices may include tablets, POS terminals, kitchen displays, and receipt printers with branch-local connectivity constraints.
- Workers handle notifications, accounting exports, reconciliation jobs, inventory projections, and operational reporting updates.
- Degraded-mode branch operation should be considered where connectivity to the central platform is intermittent.
