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

- [ ] Full kitchen station routing rules and post-fire edit approvals
- [ ] Real-time KDS eventing and pass-time telemetry
- [ ] Full recipe depletion + compensating reversal automation on order lifecycle
- [ ] Stock count sessions and variance approval workflow
- [ ] Branch transfer lifecycle states (requested/in_transit/received) and discrepancy handling
- [ ] Drawer reconciliation reports and day-close checklist enforcement screens
- [ ] Accounting export retry queue + manual rerun audit trail

## Remaining (client surfaces)

- [ ] Web role-based shells (guest touchpoint, POS, KDS, backoffice)
- [ ] Mobile role-specific operations flows parity with web API workflows
- [ ] E2E tests by role journey across guest→host→waiter→chef→cashier→manager

## Remaining (release hardening)

- [ ] Staging release rehearsal script with seeded UAT data and rollback verification
- [ ] Automated backup restore verification in CI/staging pipeline
- [ ] Production alerting thresholds and incident drill runbooks
