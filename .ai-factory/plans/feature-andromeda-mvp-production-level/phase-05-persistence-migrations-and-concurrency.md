# Phase 5: Persistence, migrations, and concurrency

Plan: [index.md](index.md)

Tasks: MVP-040, MVP-041, MVP-042, MVP-043

Depends on: MVP-010, MVP-022, MVP-023, MVP-030

Priority: P0

## Objective

Make PostgreSQL, Alembic, canonical projection, profile/decision persistence,
and ingestion run lifecycle safe under production-like concurrency. Keep
database ownership in infrastructure and preserve the existing repository
ports and module boundaries.

## Current-Code Evidence

> Historical baseline captured before this phase was implemented. Retain it
> for traceability; use current repository state, executable tests, and the
> release ledger for present-tense status.

| Finding | Status | Evidence |
| --- | --- | --- |
| Schema constraints | CONFIRMED strong baseline | backend/src/andromeda/infrastructure/database/models/* has PK/FK/unique/check/index definitions; backend/tests/infrastructure/test_db_constraints.py and test_alembic_migrations.py cover them |
| Migration chain | INTENTIONAL / mostly sound | backend/alembic/versions/0001_tracer_bullet through 0016_ingestion_source_health are linear with downgrade functions; migration 0015 has explicit university identity compatibility logic |
| Atomic projection | PARTIALLY CONFIRMED | infrastructure/repositories/ingestion.py wraps canonical sync in a transaction, but run metadata/start/completion are separate transactions |
| Concurrent ingestion/retry | CONFIRMED GAP / future risk | no per-university advisory lock or unique active-run constraint; admin retry is check-then-act; stale running recovery is absent |
| Last-good protection | PARTIALLY CONFIRMED | coarse live drift check exists; no staged/quarantine projection or complete quality gate yet |
| Readiness | CONFIRMED GAP | api/routes/health.py verifies SELECT 1 and existence of alembic_version, not equality with current migration head |
| Production bootstrap | PARTIALLY CONFIRMED | docs/deployment.md and deploy/yc/compose.yaml define staging shape, but image seed/fallback and internal port contract are inconsistent |
| Documentation head | OUTDATED | docs/testing.md refers to migration 0014 while current head is 0016 |

## Files to Change

| Future change | Path |
| --- | --- |
| Models/constraints/indexes | backend/src/andromeda/infrastructure/database/models/*.py |
| Alembic | backend/alembic/versions/0017+ and backend/alembic/env.py |
| Ingestion transaction/lock | backend/src/andromeda/infrastructure/repositories/ingestion.py |
| Admin run service | backend/src/andromeda/modules/admin_ops/services/ingestion_runs.py |
| Health/readiness | backend/src/andromeda/api/routes/health.py and schemas |
| Database tests | backend/tests/infrastructure/, backend/tests/integration/ |
| Deployment | backend/Dockerfile, backend/docker-entrypoint.sh, deploy/yc/compose.yaml, docs/deployment.md |

## Task MVP-040: Complete schema and constraint audit

### Intent

Move correctness that belongs to PostgreSQL from application-only checks into
constraints, indexes, and explicit migrations, without inventing constraints
that reject legitimate source gaps or multi-university identities.

### Implementation Steps

1. Inventory canonical uniqueness for university, direction, program,
   curriculum/year, curriculum item identity, admission offering/route,
   source snapshot, raw record, profile scope, account/session, decision
   context, proftest session, and ingestion run.
2. Identify every repository check that prevents duplicate/stale rows and
   decide whether it is a database invariant, a domain rule, or a
   source-quality gate.
3. Add missing composite indexes based on actual query predicates:
   university/program/year, offering filters, active session/expiry, decision
   owner/revision, ingestion run status/time, source hash/run.
4. Validate check constraints for canonical ID shape, normalized weights,
   admission score ranges, date ranges, and status transitions.
5. Use a forward Alembic migration with backward-compatible deployment
   sequencing for production. Do not edit applied revisions.
6. Keep downgrade behavior explicit; if a downgrade is unsafe for non-BMSTU
   data, preserve the existing fail-closed behavior and document it.

### Required Interfaces and Contracts

- Database constraints support all current university-scoped IDs.
- Repository ports expose domain errors rather than SQLAlchemy exceptions.
- Source gaps remain representable without violating required canonical
  identity constraints.

### Error Handling and Logging

- Constraint violations map to stable domain/API errors.
- Migration failures log revision and safe database target class, never the
  full connection URL.
- DDL timing/lock failures are surfaced as deployment failures, not hidden by
  create_all fallback.

### Tests

- backend/tests/infrastructure/test_db_constraints.py
- backend/tests/infrastructure/test_alembic_migrations.py
- new backend/tests/infrastructure/test_repository_invariants.py
- Add explicit tests for each newly promoted database invariant.
- Run Alembic upgrade from empty database and from current 0016 state.

### Acceptance Criteria

- Every safety-critical uniqueness/range/status invariant has a database or
  explicitly justified domain owner.
- Duplicate ingestion cannot create duplicate canonical identities.
- All migration upgrades are forward-compatible with the documented rollout.
- No application-only invariant is silently assumed in concurrent operation.

### Verification

- Run tests on SQLite where supported and PostgreSQL for real constraint,
  index, transaction, and lock semantics.
- Inspect migration SQL/downgrade path.
- Update docs to the actual head.

## Task MVP-041: Add ingestion locks, idempotency, and crash recovery

### Intent

Prevent concurrent BMSTU/HSE runs from interleaving stale-row deletion,
projection, and audit state. Current canonical projection is atomic within one
run, but the control plane is not atomic across workers.

### Implementation Steps

1. Define active-run identity as university + source profile + projection
   target and add a database-enforced or advisory-lock policy.
2. Make start-run acquire the lock atomically and return a safe conflict
   including existing run ID.
3. Make retry use a single atomic transition rather than check-then-act.
4. Add heartbeat/lease timestamps and stale-running recovery with explicit
   operator-visible reason.
5. Ensure projection and terminal run update have a recoverable protocol:
   either commit in one transaction or record a reconciliation state that
   startup/admin repair can detect.
6. Make repeated same-source run idempotency explicit by content hash/source
   identity, while allowing new run metadata to remain auditable.
7. Add failure injection at capture, validation, projection, completion, and
   process crash boundaries.

### Required Interfaces and Contracts

- IngestionRun status transitions are finite and validated.
- A running conflict is a typed conflict, not an unhandled IntegrityError.
- A stale run cannot silently be treated as completed.
- Repository methods expose idempotency and transaction boundaries to the
  service via typed ports.

### Error Handling and Logging

- Each state transition logs old/new state, run ID, lock key class, and actor.
- Crash recovery records recovery reason and prior worker identity only if
  safe; do not log host secrets.
- Duplicate/idempotent outcomes are visible as such, not reported as a new
  data refresh.

### Tests

- backend/tests/infrastructure/test_atomic_ingest.py
- backend/tests/integration/test_postgresql_ingestion.py
- backend/tests/integration/test_admin_ops_vertical_slice.py
- New concurrency tests using two PostgreSQL sessions/workers:
  duplicate starts, concurrent retry, stale lease, crash after projection,
  crash before projection, and repeated content hash.

### Acceptance Criteria

- At most one active projection per university/profile is possible.
- A worker crash yields a diagnosable recoverable state.
- Repeated ingestion is idempotent and does not interleave stale deletion.
- Last-good canonical data remains available after failed new run.

### Verification

- Run against PostgreSQL 16, not just SQLite.
- Inspect run rows and canonical counts after each injected failure.
- Run API/admin tests against the same concurrency-aware repository.

## Task MVP-042: Make bootstrap and readiness production-safe

### Intent

Ensure a process cannot report ready when it is using the wrong database,
stale schema, wrong internal port, or an untracked seed. Production-like
deployment must be reproducible from tracked inputs.

### Implementation Steps

1. Inspect and preserve the existing development/staging PostgreSQL and
   secure-cookie guards in infrastructure/config/settings.py. Add an explicit
   production policy and secret validation without duplicating or weakening
   those existing staging rules; require PostgreSQL, secret-managed
   credentials, secure cookies, and explicit frontend origin where applicable.
2. Retain deprecated BMSTU_DATABASE_URL fallback only for a bounded local
   migration cycle, with warning and a removal task.
3. Make /health/ready compare current Alembic revision to the expected head
   and report database connectivity, migration compatibility, and safe
   dependency status.
4. Reconcile deploy/yc/compose.yaml port 8020 with
   frontend-next/src/lib/server-api.ts, telegram-bot configuration, and
   internal URL environment variables. Set an explicit
   ANDROMEDA_INTERNAL_API_URL=http://backend:8020 (or the documented
   equivalent) for server-side Next.js calls in compose/VM runtime
   configuration, while keeping the browser contract on same-origin /api.
   Include server-side routes such as frontend-next/src/app/og/chances/route.tsx
   in the port/env audit.
5. Remove data/tracer.db from the image build path or replace it with an
   intentional tracked demo seed that is never the staging/production
   default.
6. Keep migrations as an explicit deployment step and fail startup if
   migration status is unsafe; do not auto-run destructive or unknown DDL.
7. Define backup-before-migration, restore, forward-fix, and rollback
   compatibility checks.

### Required Interfaces and Contracts

- Readiness response distinguishes live process from schema-compatible
  service.
- A production environment cannot silently fall back to SQLite.
- Internal service URLs use one documented port contract.
- Browser requests use same-origin /api, while server-side frontend requests
  use the explicit internal backend URL and never the backend:8000 fallback in
  the production-like stack.
- Secrets are accepted through environment/secret manager only.

### Error Handling and Logging

- Startup/readiness logs show migration revision and dependency status, not
  passwords or full URLs.
- Wrong environment/database type fails closed with a safe configuration
  error.
- Rollback instructions identify image/schema compatibility boundary.

### Tests

- backend/tests/infrastructure/test_database_config.py
- new backend/tests/api/test_health.py
- backend/tests/infrastructure/test_alembic_migrations.py
- Add production-settings fail-closed, migration-behind, migration-ahead,
  wrong-port/internal URL, and tracked-image-input tests.
- Add deployment smoke scripts for deploy/yc/compose.yaml.
- Add a server-side OG/internal-fetch smoke that proves the configured
  frontend internal URL reaches backend:8020 in the production-like stack.

### Acceptance Criteria

- Clean checkout builds image without untracked database files.
- Production/staging cannot start on SQLite or a missing secret policy.
- /health/ready fails when schema is not at the expected supported head.
- Frontend, backend, Telegram, and Caddy use one internally consistent URL and
  port contract.
- Server-side Next.js OG/internal fetches pass with the explicit internal URL;
  browser/API checks remain same-origin and do not rely on localhost or
  backend:8000 fallbacks.
- Backup/restore and forward rollback procedure is executable and documented.

### Verification

- Build and start the YC compose shape with disposable PostgreSQL.
- Run Alembic from empty and current databases.
- Kill/restart backend around migration and ingestion boundaries.
- Check live and ready endpoints separately.
- Render the server-side OG route through the compose/runtime shape and record
  the resolved internal URL/port contract.

## Task MVP-043: Measure query behavior before adding performance fixes

### Intent

Address only evidence-backed persistence performance issues. Preserve
correctness and avoid premature indexes or caching.

### Implementation Steps

1. Capture query plans for catalog, program detail, curriculum/admission,
   decision suggestions, comparison, proftest catalog snapshot, and admin run
   list/detail.
2. Check the existing bulk reader/cache paths for fallback N+1 behavior.
3. Add indexes only for measured predicates and validate write/ingestion cost.
4. Bound result sizes and pagination at repository/API contracts.
5. Identify repeated full-catalog recommendation/adaptive calculations and
   decide whether a safe run/profile cache is warranted after measurement.
6. Record ingestion memory use for large PDF/body and raw snapshot batches.

### Required Interfaces and Contracts

- Pagination and limits are typed and stable.
- Cache invalidation is tied to completed ingestion run/source version.
- No cache may serve a partially projected or failed run.

### Error Handling and Logging

- Add timing fields at request/service/ingestion stage boundaries without
  logging query parameters that contain personal data.
- Slow-query diagnostics must be sampled/bounded and disabled or reduced
  outside diagnostics mode.

### Tests

- Existing repository/integration tests for catalog, decision, comparison,
  proftest, and ingestion.
- Add query-plan/limit regression tests on PostgreSQL.
- Add a performance smoke with a representative fixture, not arbitrary
  percentage targets.

### Acceptance Criteria

- Every performance change has a measured before/after reason.
- No N+1 or unbounded response remains on a critical flow without a
  documented reason.
- Ingestion memory and request timing are observable enough to diagnose.

### Verification

- Run EXPLAIN/EXPLAIN ANALYZE in disposable PostgreSQL only.
- Compare response correctness and canonical counts before and after indexes.
- Keep rollback as a forward migration or reversible code/config change.

## Phase Risks and Mitigations

- **Risk:** locks reduce ingestion availability. **Mitigation:** bounded lease,
  explicit conflict, and last-good read availability.
- **Risk:** stricter production settings break legacy local scripts.
  **Mitigation:** separate test/development compatibility from staging/
  production fail-closed configuration and track fallback removal.
- **Risk:** migration rollback corrupts university-scoped identities.
  **Mitigation:** backup, forward-compatible migration order, and restore
  drill before release.

## Phase Completion Checklist

1. Schema invariants, indexes, and migrations have a clear owner.
2. Concurrent ingestion/retry/crash behavior is tested on PostgreSQL.
3. Readiness verifies schema compatibility, not only a version-table row.
4. Clean deployment inputs and internal ports are consistent.
5. Performance work is evidence-based and does not change domain boundaries.
