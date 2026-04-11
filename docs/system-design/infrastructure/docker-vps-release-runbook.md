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

## Production Startup Invariants (Fail-fast)

When `APP_ENV=production`, backend bootstrap performs strict configuration validation and exits before serving traffic if any invariant is violated.

Required invariants:

- Runtime hardening
  - `DEBUG=false`
  - `SECRET_KEY` must be non-default and strong (random, minimum 32 chars)
  - `SECURE_COOKIES=true`
- Host/proxy trust hardening
  - `TRUSTED_HOSTS` must be explicitly set (no `*`, no localhost/test hosts)
  - `PROXY_TRUSTED_HOSTS` must be explicitly set (no `*`)
  - `FORWARDED_ALLOW_IPS` must be explicitly set (no `*`)
- Feature toggle prerequisites
  - `FEATURE_WEBSOCKETS=true` requires `REDIS_URL`
  - `FEATURE_SOCIAL_AUTH=true` requires `SOCIAL_AUTH_REDIRECT_URL`
  - Enabled social providers require their client ID/secret:
    - `GOOGLE_ENABLED=true` => `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
    - `GITHUB_ENABLED=true` => `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
    - `FACEBOOK_ENABLED=true` => `FACEBOOK_CLIENT_ID`, `FACEBOOK_CLIENT_SECRET`
  - `EMAIL_ENABLED=true` requires valid provider-specific secrets (`smtp`, `resend`, or `ses`)
  - `PUSH_ENABLED=true` requires valid provider-specific secrets (`webpush`, `fcm`, or `onesignal`)
  - `SMS_ENABLED=true` requires valid provider-specific secrets (`twilio` or `vonage`)
  - `ANALYTICS_ENABLED=true` requires provider-specific credentials (`posthog` or `mixpanel`)
  - `STRIPE_ENABLED=true` requires `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`
  - `PAYPAL_ENABLED=true` requires `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, and valid `PAYPAL_MODE`

Operational recommendation:

- Treat these as release gates in CI/CD by validating production env files before deployment.

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
