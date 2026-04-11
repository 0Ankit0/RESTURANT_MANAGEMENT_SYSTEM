# Docker/VPS Release Runbook

## Topology

Production targets the following services:

- Reverse proxy (Nginx)
- Web app (Next.js)
- API (FastAPI)
- Background worker (Celery worker)
- Scheduler (Celery beat)
- PostgreSQL
- Redis
- S3-compatible object storage (MinIO)

Reference Compose stacks:

- `deploy/compose.dev.yml`
- `deploy/compose.staging.yml`
- `deploy/compose.prod.yml`

## Environment Profiles

Create non-checked-in environment files before deployment:

- `backend/.env.staging`
- `backend/.env.production`
- `frontend/.env.staging`
- `frontend/.env.production`
- `mobile/.env.staging`
- `mobile/.env.production`

Do not commit secrets. Use secure secret injection on VPS or CI.

Mobile payment environments must include:

- `WEBSITE_URL`
- `PAYMENT_RETURN_URL_BASE`

Reference contract: `mobile/env.production.contract.md`.

## Migration-first Startup

API startup now enforces Alembic migration parity in non-dev/test profiles.

Release step:

```bash
cd backend
uv run alembic upgrade head
```

If DB revision differs from Alembic head, startup fails fast.

## Health and Readiness Checks

- Liveness: `/api/v1/system/health/`
- Readiness: `/api/v1/system/ready/`

For production cutover:

1. Deploy image tags.
2. Run DB migrations.
3. Bring API + workers up.
4. Verify readiness.
5. Route proxy traffic.

## Backup and Restore

Minimum backup coverage:

- PostgreSQL logical backup (`pg_dump`) per day.
- MinIO bucket sync/replication.
- Weekly restore verification in staging.

Suggested verification cadence:

- Daily backup job success checks.
- Weekly restore drill in staging with readiness validation.

## Rollback

1. Keep previous image tags for web/api/worker/scheduler.
2. If release fails post-migration, evaluate migration backward compatibility.
3. Roll back app image tags first when schema is backward-compatible.
4. For schema-breaking releases, restore DB backup and redeploy previous images.

## Operational Runbooks (Required)

- Day-close blockers and checklist handling
- Refund/approval workflow escalation
- Accounting export retry and manual rerun
- Incident response for API degradation and queue lag


## References

- `backup-restore-operations.md`
