# YC deployment

The cheapest supported live layout is one small Compute Cloud VM:

```text
public IP :80 → Caddy → frontend:3000
                    └→ /api/* → backend:8020 → persistent SQLite volume
Telegram long polling → telegram-bot → backend/frontend (internal only)
```

The backend image contains the current `backend/data/tracer.db` as a seed. On
the first start it is copied to the persistent Docker volume and upgraded with
Alembic. Later restarts keep user profiles, auth sessions and proftest data.

`compose.yaml` expects `BACKEND_IMAGE`, `FRONTEND_IMAGE` and
`TELEGRAM_BOT_IMAGE` in `/opt/andromeda/.env`. The bot also requires
`TELEGRAM_BOT_TOKEN`, `ANDROMEDA_RENDER_HMAC_SECRET`,
`ANDROMEDA_SESSION_ENCRYPTION_KEY` and `ANDROMEDA_WEB_APP_URL` as secret
environment inputs. It has no public port and uses long polling.
The frontend is built with `NEXT_PUBLIC_API_BASE_URL=/api`, so the public site
does not expose an internal VM address or need CORS for normal same-origin use.

This deployment intentionally uses SQLite and HTTP-only access by IP to keep
the bill low. Bot transport sessions are stored in a separate encrypted SQLite
volume; canonical programs, profiles and scoring remain backend-owned. For a
public domain, add HTTPS in Caddy and move the database to PostgreSQL before
scaling beyond a single VM.
