# Frontend production environment contract (`frontend/.env.production`)

This file is consumed by the `web` service in `deploy/compose.prod.yml`.

## Required keys

| Key | Purpose | Secrets source |
| --- | --- | --- |
| `NEXT_PUBLIC_APP_NAME` | Display name in UI metadata and headers. | Non-secret; set directly in env file. |
| `NEXT_PUBLIC_API_URL` | Public HTTPS API base URL (for browser requests). | Non-secret; set directly in env file. |
| `NEXT_PUBLIC_WS_URL` | Public WSS websocket endpoint URL. | Non-secret; set directly in env file. |

## Optional keys

| Key | Purpose | Secrets source |
| --- | --- | --- |
| `NEXT_PUBLIC_ANALYTICS_ENABLED` | Enables browser analytics SDK initialization. | Non-secret; set directly in env file. |
| `NEXT_PUBLIC_ANALYTICS_PROVIDER` | Analytics provider selector (for example `posthog`). | Non-secret; set directly in env file. |
| `NEXT_PUBLIC_POSTHOG_KEY` | Public PostHog project key. | Public/browser-safe value from analytics console. |
| `NEXT_PUBLIC_POSTHOG_HOST` | PostHog ingest host URL. | Non-secret; set directly in env file. |

## Notes

- Only browser-safe `NEXT_PUBLIC_*` values belong in this file.
- Do **not** place private service credentials in the frontend env file; keep them in `backend/.env.production` or a secret manager.
