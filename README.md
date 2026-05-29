# Restaurant Management System

A production-oriented restaurant operations platform built with **FastAPI (backend)**, **Next.js (web)**, and **Flutter (mobile ops app)**.

The system targets multi-branch restaurant workflows across guest service, front-of-house, kitchen, inventory, cashiering, and operational reporting.

## Product Surfaces

- **Web:** guest touchpoints, staff POS, kitchen display workflows, and backoffice/admin surfaces.
- **Mobile:** host, waiter, cashier, manager, and inventory operations for live service roles.
- **Backend API:** branch-scoped domain services and compatibility endpoints under `/api/v1`.

## Quick Start

1. Install project dependencies and copy environment templates:
   - `make copy-env`
   - `make setup`
2. Start infra dependencies:
   - `make infra-up`
3. Run migrations:
   - `make backend-migrate`
4. Seed reusable QA data:
   - `make backend-qa-seed`
5. Run apps in separate terminals:
   - `make backend-dev`
   - `make frontend-dev`
   - `make mobile-dev`

## Quality Gates

- Backend lint/tests: `make backend-lint` / `make backend-test`
- Frontend lint/typecheck/tests/build: `make frontend-lint` / `make frontend-test`
- Mobile analyze/tests: `make mobile-lint` / `make mobile-test`
- System design docs validation: `make docs`
- End-to-end local gate: `make ci`

## Documentation

- System design source of truth: `docs/system-design/README.md`
- Implementation planning: `docs/system-design/implementation/implementation-playbook.md`
- Release checklist: `TEMPLATE_RELEASE_CHECKLIST.md`
- QA seed data + manual role workflows: `docs/qa-testing-seed-data.md`
