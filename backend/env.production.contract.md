# Backend production environment contract (`backend/.env.production`)

This file is consumed by `api`, `worker`, `scheduler`, `postgres`, and `minio` in `deploy/compose.prod.yml`.

## Required keys

| Key | Purpose | Secrets source |
| --- | --- | --- |
| `APP_ENV` | Runtime environment selector (must be `production`). | Non-secret; set directly in env file. |
| `SECRET_KEY` | JWT/signing and security secret. | Secret manager (1Password/Vault/GitHub Environment secret). |
| `PASSWORD_PEPPER` | Extra credential-hardening secret. | Secret manager (same source as `SECRET_KEY`). |
| `BACKEND_CORS_ORIGINS` | Allowed frontend origins for API requests. | Non-secret; set directly in env file. |
| `POSTGRES_SERVER` | Postgres host/service name. | Non-secret; set directly in env file. |
| `POSTGRES_USER` | Postgres application username. | Secret manager or secure infra variable store. |
| `POSTGRES_PASSWORD` | Postgres application password. | Secret manager. |
| `POSTGRES_DB` | Postgres database name. | Non-secret; set directly in env file. |
| `DATABASE_URL` | Async SQLAlchemy DSN for API. | Secret manager (contains credentials). |
| `SYNC_DATABASE_URL` | Sync SQLAlchemy DSN for migrations/tasks. | Secret manager (contains credentials). |
| `REDIS_HOST` | Redis host/service name. | Non-secret; set directly in env file. |
| `REDIS_PORT` | Redis TCP port. | Non-secret; set directly in env file. |
| `MINIO_ROOT_USER` | MinIO admin/access user. | Secret manager. |
| `MINIO_ROOT_PASSWORD` | MinIO admin/access password. | Secret manager. |
| `FRONTEND_URL` | Public frontend URL used in emails/auth callbacks. | Non-secret; set directly in env file. |
| `SERVER_HOST` | Public API base URL. | Non-secret; set directly in env file. |
| `SECURE_COOKIES` | Must be `True` in production. | Non-secret; set directly in env file. |

## Optional keys (common production additions)

| Key | Purpose | Secrets source |
| --- | --- | --- |
| `CELERY_BROKER_URL` | Explicit broker URL (otherwise composed from redis keys). | Secret manager if credentials embedded. |
| `CELERY_RESULT_BACKEND` | Explicit result backend URL. | Secret manager if credentials embedded. |
| `S3_BUCKET` / `S3_ENDPOINT_URL` / `S3_REGION` | Object storage settings when using S3-compatible backend. | Endpoint: non-secret; credentials: secret manager. |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3/SES credentials. | Secret manager. |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP credentials. | Secret manager. |
| `RESEND_API_KEY` | Resend email provider API key. | Secret manager. |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | Stripe payments credentials. | Secret manager. |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` | SMS provider credentials. | Secret manager. |
| `GOOGLE_CLIENT_SECRET` / `GITHUB_CLIENT_SECRET` / `FACEBOOK_CLIENT_SECRET` | OAuth provider credentials. | Secret manager. |

## Notes

- Keep production secrets out of git; inject via your deployment secret store and materialize into `backend/.env.production` at deploy time.
- Avoid test/example values in production (`*_test_*`, `changeme`, `example`).
