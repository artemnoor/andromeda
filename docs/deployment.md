# Staging deployment

Andromeda local/demo runs may use SQLite. Staging must use PostgreSQL and an
external domain; serving the application directly on an IP over HTTP is not a
production deployment.

## Required staging configuration

Set these values outside the repository (for example in the deployment
environment file or secret manager):

| Variable | Purpose |
| --- | --- |
| `ANDROMEDA_ENV=staging` | Enables staging safety checks. |
| `ANDROMEDA_DATABASE_URL=postgresql+psycopg://...` | PostgreSQL connection. |
| `ANDROMEDA_DOMAIN=andromeda.example.org` | Caddy hostname and HTTPS. |
| `ANDROMEDA_OPS_API_KEY` | Protected Ops endpoints. |
| `ANDROMEDA_SECRET_KEY` | Session and application secret. |

The `deploy/yc/compose.yaml` stack runs PostgreSQL, the backend, the Next
frontend and Caddy. Caddy obtains and renews the certificate automatically
once DNS points the domain to the host and ports 80/443 are reachable.

Apply migrations before starting the application image:

```bash
docker compose --env-file /etc/andromeda/backend.env -f deploy/yc/compose.yaml run --rm backend python -m alembic upgrade head
docker compose --env-file /etc/andromeda/backend.env -f deploy/yc/compose.yaml up -d
```

## Smoke checks

`/health/live` checks that the process is running. `/health/ready` checks only
database reachability and migration compatibility; it intentionally does not
depend on BMSTU/HSE availability.

```bash
curl --fail https://andromeda.example.org/health/live
curl --fail https://andromeda.example.org/health/ready
curl --fail https://andromeda.example.org/programs
```

Then check one program, curriculum/admissions, a comparison and an anonymous
DecisionContext session in the browser. The scheduled `source-health` workflow
is a separate operational check and does not block pull requests during a
temporary university-site outage.

## Backup and restore

Run backups from a host that can reach PostgreSQL. Keep encrypted copies and
retain at least daily backups for the agreed staging retention window.

```bash
pg_dump --format=custom --file=andromeda-$(date +%Y%m%d-%H%M).dump "$ANDROMEDA_DATABASE_URL"
createdb andromeda_restore
pg_restore --clean --if-exists --dbname="$ANDROMEDA_RESTORE_URL" andromeda-YYYYMMDD-HHMM.dump
```

Never put connection strings or dump files in Git. Verify restores regularly
by running `alembic upgrade head`, `/health/ready`, and a catalog/decision smoke
check against the restored database.

## Rollback

1. Keep the previous container image tag available.
2. Before a schema migration, take a PostgreSQL dump.
3. Deploy the previous image only when the new migration is backward-compatible
   with that image; otherwise restore the database backup in an isolated
   rollback procedure.
4. Do not edit or delete an applied Alembic revision. Forward-fix with a new
   migration and record the compatibility boundary in the release notes.
