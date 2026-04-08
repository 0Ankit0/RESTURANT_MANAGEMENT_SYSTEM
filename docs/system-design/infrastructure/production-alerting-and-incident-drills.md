# Production Alerting Thresholds and Incident Drill Runbook

## Alerting thresholds

- **API error rate**: trigger warning at `>2%` over 5 minutes; critical at `>5%` over 5 minutes.
- **P95 API latency**: warning at `>800ms`; critical at `>1500ms`.
- **Database connections**: warning at `>80%` pool usage for 10 minutes.
- **Queue backlog** (kitchen/accounting workers): warning at `>500` jobs for 10 minutes; critical at `>1500`.
- **Failed accounting exports**: warning when retries exceed `3` attempts for same export.
- **Day-close blockers**: warning when open drawer sessions remain after close cut-off.

## Incident severities

- **SEV-1**: payment settlement failures, widespread order creation failures, data corruption risk.
- **SEV-2**: degraded kitchen updates, delayed exports, partial branch outage.
- **SEV-3**: non-critical reporting lag, single integration degradation.

## Drill cadence

- Weekly tabletop: 30 minutes (rotating scenarios).
- Monthly functional drill: restore backup + replay day-close.
- Quarterly full drill: simulated branch outage + failover + audit export reconciliation.

## Drill scenarios

1. **Kitchen telemetry outage**
   - Confirm `/api/v1/kitchen/events` freshness lag.
   - Switch KDS to polling fallback.
   - Verify order status catch-up.

2. **Settlement discrepancy spike**
   - Run drawer reconciliation report.
   - Compare settlement totals to drawer closure totals.
   - Trigger manager approval workflow and incident log.

3. **Accounting export queue failure**
   - Validate retry queue state.
   - Trigger manual rerun endpoint and capture audit trail.
   - Verify downstream ledger import completion.

4. **Database restore drill**
   - Run `scripts/ops/backup_postgres.sh`.
   - Run `scripts/ops/verify_backup_restore.sh` using latest backup.
   - Validate row counts for critical tables.

## Incident response checklist

- Assign incident commander and scribe.
- Freeze non-essential deploys.
- Capture timeline (`T+0`, `T+15`, `T+30`, etc.).
- Apply mitigation and verify KPI recovery.
- Publish postmortem within 48 hours with corrective actions.
