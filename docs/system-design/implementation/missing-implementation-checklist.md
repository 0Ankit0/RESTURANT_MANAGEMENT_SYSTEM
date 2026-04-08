# Missing Implementation Checklist (Docs vs Current Code)

This checklist maps major items from the system design docs to current implementation status.

## Implemented in backend API

- [x] Service zones
- [x] Table groups
- [x] Menu categories
- [x] Modifier groups/options
- [x] Tax rule versioning
- [x] Vendors
- [x] Goods receipts
- [x] Attendance
- [x] Day-close open/finalize/list
- [x] Discount approvals
- [x] Refunds
- [x] Recipes (basic versioned recipe + items)
- [x] Stock transfers (create/approve/list)

## Remaining (high priority)

- [x] Full kitchen station routing rules and post-fire edit approvals
- [x] Real-time KDS eventing and pass-time telemetry
- [x] Full recipe depletion + compensating reversal automation on order lifecycle
- [x] Stock count sessions and variance approval workflow
- [x] Branch transfer lifecycle states (requested/in_transit/received) and discrepancy handling
- [x] Drawer reconciliation reports and day-close checklist enforcement screens
- [x] Accounting export retry queue + manual rerun audit trail

## Remaining (client surfaces)

- [x] Web role-based shells (guest touchpoint, POS, KDS, backoffice)
- [x] Mobile role-specific operations flows parity with web API workflows
- [x] E2E tests by role journey across guest→host→waiter→chef→cashier→manager

## Remaining (release hardening)

- [x] Staging release rehearsal script with seeded UAT data and rollback verification
- [x] Automated backup restore verification in CI/staging pipeline
- [x] Production alerting thresholds and incident drill runbooks

## Domain module coverage

- [x] Seating domain module utilities
- [x] Menu domain module utilities
- [x] Orders domain module utilities
- [x] Kitchen domain module utilities
- [x] Inventory domain module utilities
- [x] Procurement domain module utilities
- [x] Billing domain module utilities
- [x] Workforce domain module utilities
- [x] Reporting domain module utilities
