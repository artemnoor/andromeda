# Phase 7: tests and documentation

## Goal

Turn the new behavior into runnable evidence and explain live versus fixture operation.

## Files and symbols

- `backend/tests/ingestion/`: source, parser, identity, taxonomy and full adapter tests.
- `backend/tests/infrastructure/` and `backend/tests/integration/`: storage/idempotence/SQLite/PostgreSQL coverage.
- `backend/tests/scripts/`: runner payload/default tests.
- `docs/architecture.md`, `docs/postgresql.md`, `docs/testing.md`, `README.md`: current commands, source gaps and observed full-catalog semantics.

## Ordered edits

1. Add deterministic synthetic source fixtures/tests without using them as production live truth.
2. Add full adapter contract assertions for counts/IDs/gaps/area vectors.
3. Run focused tests after each implementation phase, then full backend pytest and mypy.
4. Document official source URLs, pagination, Yandex resolver behavior, gap reporting, live event/campus limitation and repeat ingestion.

## Acceptance

No existing API/recommendation/comparison/proftest fixture test regresses; docs contain no claim that fixture events/campus are live BMSTU truth.
