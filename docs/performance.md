# Performance evidence

MVP performance work is evidence-driven. The repository keeps bounded limits
in public contracts and does not introduce a cache or a latency target without
a representative PostgreSQL measurement.

## PostgreSQL read profile

Against a disposable PostgreSQL database at the current Alembic head:

```powershell
$env:ANDROMEDA_POSTGRES_TEST_URL = "postgresql+psycopg://..."
python backend/scripts/profile_queries.py --out $env:TEMP/andromeda-query-profile.json
```

The diagnostic runs fixed, read-only `SELECT` statements for catalog,
curriculum, admissions, comparison, proftest catalog, events, campus and
admin runs. It records `EXPLAIN (FORMAT JSON)` and one bounded timing sample;
the database target is redacted. It does not run `ANALYZE`, mutate data, or
emit query parameters.

## Ingestion memory profile

The fixture parser profile records source bytes, canonical row counts and
`tracemalloc` peak for BMSTU or HSE without writing to the database:

```powershell
python backend/scripts/profile_ingestion_memory.py --university bmstu
python backend/scripts/profile_ingestion_memory.py --university hse
```

Runtime ingestion logs the same safe source-byte/count metrics together with
projection duration and run ID. Raw bodies, credentials and payload contents
are never logged.

## Current measured finding

`SqlAlchemyCurriculumRepository.get_for_program` previously selected
assessment rows once per curriculum item. The reader now loads all assessment
rows for the selected curriculum in one bounded query; the regression is
covered by `backend/tests/infrastructure/test_query_behavior.py`.

Future index or cache changes must attach a before/after profile artifact and
preserve completed-run/source-version invalidation semantics.
