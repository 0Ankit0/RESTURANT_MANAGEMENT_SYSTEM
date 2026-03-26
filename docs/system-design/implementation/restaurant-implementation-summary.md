# Restaurant Implementation Summary

## Missing items identified and completed in this phase

- Added branch discovery endpoint for client selectors (`GET /api/v1/branches`).
- Added reservation retrieval and cancellation endpoints:
  - `GET /api/v1/reservations/{reservation_id}`
  - `POST /api/v1/reservations/{reservation_id}/cancel`
- Extended integration test to verify reservation retrieval and cancel flow.
- Continued web/mobile client alignment with branch-driven selectors and operational actions.

## Current implemented scope

Backend APIs currently include:
- Branches, tables, seating
- Reservations + waitlist
- Orders + kitchen tickets
- Inventory adjustments
- Purchase orders + receipts
- Bills + settlements + drawer close
- Shift create/update
- Accounting exports + branch reports
- Branch policy admin update
- Idempotency key handling on critical writes
- Cursor pagination on activity collections

Web client currently includes:
- Restaurant dashboard
- Branch selector from API
- Reservation creation
- Quick seating / waitlist promotion / quick order
- Orders, kitchen, tables, waitlist, reservations and metrics views

Mobile client currently includes:
- Restaurant operations page
- Dynamic branch selector from API
- Reservation create
- Seat first available table
- Promote first waitlist entry
- Tables, waitlist, orders and metric summaries

## Remaining non-functional follow-ups

- Run full lint/format/test pipelines in an environment with:
  - frontend Node dependencies (`eslint-config-next`, etc.)
  - Dart/Flutter SDK installed.
- Add formal Alembic migration scripts for all restaurant tables if migration-first deployment is required.
