# QA Seed Data and Manual Testing Guide

This guide defines a repeatable dataset for manual QA across authentication, tenant management, restaurant operations, notifications, and payments.

## What Gets Seeded

Running the seed script creates or updates the following records (idempotent):

- Users and profiles:
  - `qaadmin` (superuser)
  - `qamanager`
  - `qahost`
  - `qawaiter`
  - `qachef`
  - `qacashier`
- IAM roles and assignments:
  - `admin`, `branch_manager`, `host`, `waiter`, `chef`, `cashier`
- Multitenancy:
  - Tenant `QA Tenant` with slug `qa-tenant`
  - Tenant memberships for all QA users
- Restaurant operations:
  - Branches `QA Downtown`, `QA Uptown`
  - Tables `QA-T1`, `QA-T2`, `QA-T3`
  - Menu items `QA Burger`, `QA Pasta`, `QA Lemonade`
  - Ingredients with stock quantities and reorder thresholds
  - Reservation, waitlist entry, submitted order, kitchen ticket, bill, settlement
  - Branch payment methods (`cash`, `card`, `wallet`)
- Finance and notifications:
  - One completed payment transaction (`QA-ORDER-001`)
  - Role-targeted operational notifications

## Seed Credentials

All QA users share the same password:

- Password: `QaPass1234`

Usernames:

- `qaadmin`
- `qamanager`
- `qahost`
- `qawaiter`
- `qachef`
- `qacashier`

## Prerequisites

- Backend dependencies installed (`cd backend && uv sync`)
- Backend environment configured (`backend/.env`)
- PostgreSQL and Redis running (Docker or Podman)
- Backend should run in local debug mode for schema bootstrap when migrations are not fully aligned

## Run the Seed

From repository root:

```bash
make backend-qa-seed
```

Direct command (equivalent):

```bash
cd backend
uv run task seed-qa
```

## Suggested QA Start Flow

1. Start infra and backend/frontend.
2. Run `make backend-qa-seed`.
3. Login as `qaadmin` and verify:
   - Admin dashboard pages load.
   - Tenant list contains `QA Tenant`.
4. Switch users by role to verify workflow boundaries:
   - `qahost`: reservation and waitlist actions.
   - `qawaiter`: quick order and table-linked order flow.
   - `qachef`: kitchen ticket progression.
   - `qacashier`: bill settlement and payment visibility.
   - `qamanager`: branch operations reporting and oversight.

## API-Oriented QA Checks

After seeding, validate key endpoint groups using UI flows or API client:

- Auth and profile endpoints (login, me, profile updates)
- Tenant and membership endpoints
- Restaurant endpoints:
  - branches
  - tables / seating
  - reservations / waitlist
  - orders / order items
  - kitchen tickets
  - bills / settlements
- Notifications endpoints
- Payment transaction endpoints

## Re-run and Reset Notes

- The seed is idempotent and safe to run repeatedly.
- Existing QA records are updated to expected baseline values on each run.
- If you need a clean slate, reset the database and run seed again.

Example reset (dangerous, local only):

```bash
# Example for local postgres container
# Drop and recreate schema/database as per your local setup, then re-run:
make backend-qa-seed
```

## Podman Local Example

If you run infra with custom Podman ports, ensure `backend/.env` points to those ports before seeding. Then run:

```bash
make backend-qa-seed
```

The script will connect using `DATABASE_URL` and seed whichever database is configured there.
