# Restaurant Delivery Phases (Execution Plan)

## Phase 1 — Platform Stabilization (current)

- Rebrand template remnants to restaurant naming and docs tree.
- Enforce migration-first startup outside dev/test.
- Introduce Docker/VPS runbook and environment-specific compose stacks.
- Add branch-scoped RBAC enforcement primitive for restaurant APIs.
- Scaffold domain package boundaries under `src/apps/restaurant/domains/*`.

## Phase 2 — Domain Completion

- Seating + waitlist: service zones, table groups, conflict detection.
- Menu + pricing: categories, modifiers, tax/version rules, discount policy versions.
- Kitchen + orders: station routing, course fire/release, post-fire approvals.
- Inventory + procurement: recipes/BOM, goods receipts, count variance approvals, transfers.
- Billing + cashiering: split/mixed settlements, refunds, post-close adjustments, day-close blockers.
- Workforce + operations: attendance, staffing readiness, operational alerts.

## Phase 3 — Public API Standardization + UI Surfaces

- Add resource families listed in API design docs.
- Standardize pagination and error payloads across modules.
- Move web into role-based surfaces (guest, POS, KDS, backoffice).
- Keep mobile focused on live operations roles.

## Phase 4 — Release and Operations Hardening

- CI gates: docs validation, lint/tests, type/build, image builds.
- Staging rehearsal with migrations, backup/restore verification, and role-based UAT.
- Production runbooks: day close, refund approvals, export retries, incident response.
