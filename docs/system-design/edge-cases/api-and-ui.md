# Edge Cases - API and UI

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| POS tablet briefly loses connectivity during order submission | Duplicate or missing orders | Use offline queueing and idempotent order submission |
| Table map lags behind real seating updates | Staff make wrong decisions | Reconcile critical seating state from authoritative store and show freshness indicators |
| Kitchen display receives stale tickets after void or change | Prep waste and confusion | Push ticket invalidation events and require explicit state refresh |
| Backoffice dashboards become slow during peak traffic | Managers lose visibility | Use projected summaries and paginated drill-down queries |
| Guest-facing status page shows incorrect order phase | Trust drops | Limit external status exposure to well-defined, audited states |
