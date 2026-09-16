# YC deployment

The cheapest supported live layout is one small Compute Cloud VM:

```text
public IP :80 → Caddy → frontend:3000
                    └→ /api/* → backend:8020 → persistent SQLite volume
```

The backend image contains the current `backend/data/tracer.db` as a seed. On
the first start it is copied to the persistent Docker volume and upgraded with
Alembic. Later restarts keep user profiles, auth sessions and proftest data.

`compose.yaml` expects `BACKEND_IMAGE` and `FRONTEND_IMAGE` in `/opt/andromeda/.env`.
The frontend is built with `NEXT_PUBLIC_API_BASE_URL=/api`, so the public site
does not expose an internal VM address or need CORS for normal same-origin use.

This deployment intentionally uses SQLite and HTTP-only access by IP to keep
the bill low. For a public domain, add HTTPS in Caddy and move the database to
PostgreSQL before scaling beyond a single VM.
