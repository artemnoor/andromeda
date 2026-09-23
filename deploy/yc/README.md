# YC deployment

The cheapest supported live layout is one small Compute Cloud VM:

```text
domain :443 → Caddy (automatic HTTPS) → frontend:3000
                         └→ /api/* → backend:8020 → PostgreSQL
Telegram long polling → telegram-bot → backend/frontend (internal only)
```

Staging uses PostgreSQL through `ANDROMEDA_DATABASE_URL`; schema upgrades run
through Alembic before the backend starts. Keep database credentials only in
the deployment environment, never in this repository.

`compose.yaml` expects `BACKEND_IMAGE`, `FRONTEND_IMAGE` and
`TELEGRAM_BOT_IMAGE` in `/opt/andromeda/.env`. The bot also requires
`TELEGRAM_BOT_TOKEN`, `ANDROMEDA_RENDER_HMAC_SECRET`,
`ANDROMEDA_SESSION_ENCRYPTION_KEY` and `ANDROMEDA_WEB_APP_URL` as secret
environment inputs. It has no public port and uses long polling.
The backend trusted browser origin defaults to `https://${ANDROMEDA_DOMAIN}`;
set `ANDROMEDA_FRONTEND_ORIGIN` explicitly when a reverse proxy exposes a
non-default origin or port (for example, a local TLS smoke).
Jev next-action control is optional and remains off unless `JEV_ENABLED=true`
and its production calibration gate/key are configured; see
[`docs/deployment.md`](../../docs/deployment.md#optional-jev-next-action-runtime).
The image carries the pinned SDK, question registry and matching calibration
lock. Keep the provider key only in `/opt/andromeda/.env` or the secret manager.
The frontend is built with `NEXT_PUBLIC_API_BASE_URL=/api`, so the public site
does not expose an internal VM address or need CORS for normal same-origin use.
Server-side OG routes use the explicit runtime variable
`ANDROMEDA_INTERNAL_API_URL=http://backend:8020`; they never use the public
browser path or a `backend:8000` fallback.

The local/demo compose profile may use SQLite for a cheap single-process run,
but it is not the staging target. Staging requires a domain configured in
Caddy, automatic HTTPS, PostgreSQL backups, and the readiness check at
`/api/health/ready`. Bot transport sessions remain in a separate encrypted volume;
canonical programs, profiles and scoring remain backend-owned.
