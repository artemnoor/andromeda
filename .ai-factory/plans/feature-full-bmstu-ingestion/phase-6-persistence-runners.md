# Phase 6: repository and runners

## Goal

Project the full canonical graph atomically and make command/retry paths dynamic, idempotent and auditable.

## Files and symbols

- `backend/src/andromeda/infrastructure/repositories/ingestion.py`: raw record insertion, all-direction upsert and current-graph reconciliation.
- `backend/src/andromeda/infrastructure/repositories/bmstu_ingestion_retry.py`: selected profile removal/dynamic parse.
- `backend/scripts/run_tracer_bullet.py`: dynamic defaults, counts and non-fixed API example.
- `backend/src/andromeda/infrastructure/database/models/*`, `backend/alembic/versions/*`: schema only if contract fields need persistence; keep migrations linear.

## Ordered edits

1. Insert every canonical direction before programs and retain raw source-gap records in the same transaction.
2. Reconcile stale curriculum items/programs only for the BMSTU graph represented by the current snapshot; never delete unrelated university data.
3. Make retries call live discovery without target-code constants and preserve failure audit status/error code.
4. Keep existing ID/check constraints valid; add migration tests if source-gap quality storage needs a schema field.
5. Update runner payload to report discovered directions/programs/plans/gaps and use a generated pair only for optional fixture demo verification.

## Tests and acceptance

- SQLite fresh migration, one ingest, repeat ingest and changed snapshot reconciliation have no duplicate IDs.
- PostgreSQL smoke/integration tests use the same canonical payload and FK ordering.
- Commands: `python -m pytest backend/tests/infrastructure backend/tests/integration/test_postgresql_ingestion.py -q` and the repository's configured PostgreSQL command when `DATABASE_URL` is available.
