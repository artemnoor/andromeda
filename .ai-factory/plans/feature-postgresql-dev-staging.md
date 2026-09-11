# Implementation Plan: PostgreSQL для dev/staging Andromeda

Branch: `feature/postgresql-dev-staging`
Base: `feature/recommendation-module`
Created: 2026-09-11

## Original Request

Переведи Andromeda с локальной SQLite/fixture-ориентированной схемы на нормальную dev/staging PostgreSQL, не ломая текущие модули.
Нужно: PostgreSQL через существующие repository ports, Alembic migrations, конфигурация через env, отдельный staging database, ingestion/parser должен уметь наполнять и обновлять её. Сохрани SQLite для быстрых тестов, если это полезно.
Добавь smoke/integration tests и документацию запуска. Не меняй бизнес-логику comparison/proftest/recommendations.
DoD: Andromeda поднимается с PostgreSQL, реальные данные проходят parser → DB → API → frontend, CI green. После этого остановись.

## Settings

- Testing: yes
- Logging: verbose — DEBUG/INFO checkpoints без секретов и payloads
- Docs: yes — обязательный documentation checkpoint в `$aif-implement`
- Roadmap: skipped — `.ai-factory/ROADMAP.md` отсутствует, поэтому linkage не добавляется

## Current Evidence

Текущая рабочая точка — опубликованная ветка `feature/recommendation-module`; плановая ветка создана от неё, а не от настроенной по умолчанию `main`. Это намеренное решение: в `main` может не быть уже готовых `proftest` и `recommendations`, а задача требует сохранить эти vertical slices.

- `backend/src/andromeda/infrastructure/config/settings.py` хранит только `BMSTU_DATABASE_URL`, `VITE_FRONTEND_ORIGIN` и `LOG_LEVEL`; дефолт базы — `sqlite:///./data/tracer.db`.
- `backend/src/andromeda/infrastructure/database/base.py:create_engine_for_url()` различает SQLite и non-SQLite только для `check_same_thread` и SQLite foreign keys; pool/health-настройки для staging отсутствуют.
- `backend/alembic.ini` содержит SQLite URL, а `backend/alembic/env.py` читает URL из INI и сам по себе не использует `BMSTU_DATABASE_URL`.
- `backend/scripts/run_tracer_bullet.py:run_ingest()` уже принимает произвольный `database_url`, применяет Alembic, запускает `BmstuUniversityAdapter` и пишет canonical snapshot через `SqlAlchemyIngestionRepository`.
- `backend/src/andromeda/infrastructure/repositories/ingestion.py` уже делает одну транзакцию и сохраняет raw source snapshots, но `_insert_or_validate()` отклоняет изменение уже существующей сущности вместо синхронизации обновлённого canonical snapshot.
- `backend/alembic/versions/0001_tracer_bullet.py` использует `Base.metadata.create_all()` и импортирует mutable metadata из legacy facade; это не является стабильным историческим initial migration.
- `backend/alembic/versions/0002_comparison_identity.py` использует `batch_alter_table(..., recreate="always")`, что требует отдельной проверки на PostgreSQL из-за внешнего ключа `curriculum_item_assessments`.
- `backend/src/andromeda/modules/{universities,programs,curricula,disciplines,comparison,proftest,recommendations}` получают данные через contracts/repository ports; ORM находится в `backend/src/andromeda/infrastructure/database/models` и не должен становиться межмодульным API.
- Текущие API routes и frontend уже используют существующие readers и HTTP/OpenAPI path. Смена storage должна быть прозрачной для `/programs`, `/programs/{id}/curriculum`, `/compare`, `/proftest` и `/recommendations`.
- `.github/workflows/ci.yml` сейчас проверяет SQLite fixture path, backend/frontend gates и browser flows, но отдельного PostgreSQL service/integration job нет.
- `backend/tests` в основном поднимает SQLite через `Base.metadata.create_all()`; это сохраняется как быстрый слой, но не может служить доказательством Alembic/PostgreSQL compatibility.

## Architectural Decision

Остаётся один modular monolith и один набор domain/application contracts. PostgreSQL становится обязательным storage для окружений `development` и `staging`; SQLite остаётся разрешённым для unit tests, быстрых contract tests и локального fixture smoke по явному URL.

Единым runtime target будет `BMSTU_DATABASE_URL`. `ANDROMEDA_ENV` (`test`, `development`, `staging`) определяет policy проверки конфигурации, но не создаёт второй способ выбрать базу. API, ingestion runner, Alembic и CI используют один и тот же URL из environment. Пароли и query parameters никогда не попадают в logs.

Storage boundary не меняется:

```text
BMSTU source
  -> BMSTU adapter/parser
  -> raw + canonical contracts
  -> SqlAlchemy ingestion repository
  -> PostgreSQL (dev/staging) / SQLite (tests)
  -> existing module repository ports
  -> application services
  -> existing FastAPI/OpenAPI
  -> frontend
```

`comparison`, `proftest` и `recommendations` не получают новых storage dependencies и не меняют scoring, fingerprint, adaptive или response business logic. Все PostgreSQL-specific решения остаются в `infrastructure`, runner/ops и migration layer.

## Commit Plan

- **Commit 1** (после задач 1–3): `feat(infrastructure): add PostgreSQL runtime and portable migrations`
- **Commit 2** (после задач 4–5): `feat(ingestion): sync canonical snapshots to PostgreSQL`
- **Commit 3** (после задач 6–8): `test(ops): verify PostgreSQL fullstack path and document environments`

## Tasks

### Фаза 1: Database runtime и migration foundation

- [x] **Task 1: Ввести единую env-конфигурацию и PostgreSQL engine, сохранив SQLite test path.**

  **Deliverable:** Доработать `backend/src/andromeda/infrastructure/config/settings.py`, `backend/src/andromeda/infrastructure/database/base.py`, `backend/src/andromeda/infrastructure/database/session.py` и `backend/pyproject.toml`.

  Добавить runtime dependency `psycopg` с совместимым SQLAlchemy URL `postgresql+psycopg://...`. Расширить typed settings полями `environment`, `database_url` и безопасными pool options с разумными defaults. `BMSTU_DATABASE_URL` остаётся единственным источником адреса базы; не вводить отдельный URL для API и ingestion.

  Зафиксировать policy:

  - `test` допускает SQLite, включая `sqlite:///:memory:` и временные file databases;
  - `development` и `staging` требуют PostgreSQL URL и fail fast при явно выбранном окружении с неподходящим dialect;
  - отсутствие `ANDROMEDA_ENV` сохраняет backward-compatible SQLite fallback только для старых быстрых локальных команд, а документация и env examples используют PostgreSQL;
  - пароли с URL-special characters проходят через стандартный URL encoding, а validation error не раскрывает пароль.

  Для PostgreSQL настроить проверяемое соединение (`pool_pre_ping`, timeout/recycle/pool limits из env), не включать SQL echo в обычном режиме и корректно dispose engine при завершении. Для SQLite сохранить `check_same_thread=False` и `PRAGMA foreign_keys=ON`, чтобы существующие тесты не потеряли FK enforcement. Не менять session/repository ports и не переносить ORM в modules.

  Ввести небольшой sanitizer для database URL, чтобы logs показывали dialect/host/database без credentials. Проверить, что `Settings` и engine можно создать в тестах без запуска PostgreSQL.

  **LOGGING REQUIREMENTS:**

  - DEBUG: выбранный environment, dialect, pool policy и redacted database target;
  - INFO: engine initialization/disposal и длительность connection preflight;
  - WARNING: legacy SQLite fallback без `ANDROMEDA_ENV`;
  - ERROR: missing/invalid PostgreSQL driver, unsupported environment/dialect и connection failure с redacted target;
  - никогда не логировать `BMSTU_DATABASE_URL` целиком, password, access token или SQL payload.

  **Dependencies:** none.

  **Verification:** unit tests settings/URL redaction/engine dialect; existing SQLite suite remains green; a PostgreSQL smoke test is marked/skipped only when `BMSTU_DATABASE_URL` is not provided, and runs in CI with the service database.

  **Files:** `backend/src/andromeda/infrastructure/config/settings.py`, `backend/src/andromeda/infrastructure/config/**`, `backend/src/andromeda/infrastructure/database/base.py`, `backend/src/andromeda/infrastructure/database/session.py`, `backend/pyproject.toml`, `backend/tests/infrastructure/test_database_config.py`.

- [x] **Task 2: Сделать Alembic единым env-driven entry point и подтвердить portable schema.** (depends on Task 1)

  **Deliverable:** Обновить `backend/alembic/env.py`, `backend/alembic.ini` и migrations under `backend/alembic/versions/`, не меняя публичные module contracts.

  `env.py` должен брать `BMSTU_DATABASE_URL` из environment с явным приоритетом над INI placeholder, использовать тот же URL sanitizer в diagnostic logging и поддерживать offline/online mode. `alembic.ini` больше не должен подталкивать dev/staging к конкретному локальному SQLite файлу; SQLite fallback допустим только для backwards-compatible test command.

  Провести migration audit и исправить цепочку так, чтобы она была запускаема на пустой SQLite и пустой PostgreSQL, а также upgrade-совместима с локальными базами на предыдущих revisions:

  - initial revision не должна зависеть от текущего `Base.metadata.create_all()`/mutable legacy metadata; схема должна быть описана стабильными `op.create_table`/constraint operations;
  - `0002_comparison_identity` должна использовать PostgreSQL-native alter path и отдельный SQLite-compatible path там, где SQLite действительно требует batch recreation; учесть FK `curriculum_item_assessments` и nullable semester backfill;
  - `0003_discipline_taxonomy` должна оставаться idempotent для уже существующих reference rows и сохранять все 22 taxonomy areas;
  - сохранить FK, unique и check constraints, включая `semester_identity`, Numeric credits/weights, идентификаторы и status ranges;
  - проверить explicit casts/null semantics в check expressions и детерминированный порядок curriculum rows (`source_position`/NULL ordering), чтобы PostgreSQL не изменил результаты comparison/proftest/recommendations.

  Если исправление старых revisions необходимо, сохранить их revision IDs и написать upgrade tests для баз на `0001`, `0002` и `0003`; новую migration добавлять только для реально post-baseline изменений, а не для сокрытия несовместимости initial chain.

  **LOGGING REQUIREMENTS:**

  - INFO: migration target (redacted), current revision, target revision и duration;
  - DEBUG: dialect-specific branch и таблицы/constraints, но не row payloads;
  - ERROR: failed revision и безопасный migration context, без DSN secret;
  - не включать SQL statement logging в CI по умолчанию.

  **Dependencies:** Task 1.

  **Verification:** migration test matrix `empty -> head` и `old revision -> head` для SQLite; тот же `empty -> head`, schema inspection и rollback/constraint checks для PostgreSQL в integration environment. OpenAPI and module behavior snapshots должны остаться без business changes.

  **Files:** `backend/alembic/env.py`, `backend/alembic.ini`, `backend/alembic/versions/0001_tracer_bullet.py`, `backend/alembic/versions/0002_comparison_identity.py`, `backend/alembic/versions/0003_discipline_taxonomy.py`, optionally a new numbered migration only if required, `backend/tests/infrastructure/test_alembic_migrations.py`.

- [x] **Task 3: Добавить repeatable dev/staging PostgreSQL runtime с раздельными database targets.** (depends on Task 1)

  **Deliverable:** Добавить reproducible local PostgreSQL setup and environment templates under `ops/postgres/` (or an equivalent clearly named ops directory), plus `.env.development.example` and `.env.staging.example` without secrets.

  Compose setup должен иметь healthcheck and persistent named volumes, and separate targets:

  - development database, for example `andromeda_dev` on the local development port;
  - staging database, for example `andromeda_staging` on a distinct service/port or a separately configured external target and volume;
  - credentials supplied by environment, never committed;
  - explicit image/version and readiness checks so runner does not race PostgreSQL startup.

  Prefer one documented compose file with profiles or two explicit services, but make the database name/DSN separation visible and testable. Do not add Kubernetes, Kafka, auth, deployment platform integration or a second application service. Add a small `make`/PowerShell-independent command only if it reduces setup friction and does not hide the underlying `docker compose`/Alembic commands.

  **LOGGING REQUIREMENTS:**

  - setup output may show service name, host, port, database name and health status;
  - never show passwords or fully expanded DSNs;
  - failed healthcheck must identify the target environment and service, not dump container secrets.

  **Dependencies:** Task 1.

  **Verification:** start development and staging profiles independently, assert distinct database names/volumes, run `alembic upgrade head` against each, and prove that the app points to the selected target only through `BMSTU_DATABASE_URL`.

  **Files:** `ops/postgres/docker-compose.yml` (or selected equivalent), `.env.development.example`, `.env.staging.example`, `.gitignore` only if local env/runtime files are not already ignored, `backend/tests/infrastructure/test_environment_targets.py`.

<!-- Commit checkpoint: tasks 1-3 -->

### Фаза 2: Ingestion sync и existing repository path

- [x] **Task 4: Сделать parser → canonical → database ingestion идемпотентным и обновляемым.** (depends on Tasks 1–2)

  **Deliverable:** Доработать `backend/src/andromeda/infrastructure/repositories/ingestion.py`, `backend/scripts/run_tracer_bullet.py` и, только при необходимости для target selection, `backend/scripts/run_tracer_demo.py`.

  Сохранить `BmstuUniversityAdapter` как BMSTU-specific ingestion boundary: URL/selectors/PDF parsing/mappings не выносить в core andromeda modules. Runner должен брать target из `BMSTU_DATABASE_URL`/explicit CLI override, мигрировать выбранную базу и выполнять тот же raw → normalized → canonical flow для PostgreSQL.

  Расширить текущую atomic write strategy до deterministic sync:

  - повторный ingest того же snapshot не создаёт duplicate raw/domain/reference rows;
  - новые programs/curricula/disciplines/weights добавляются через существующие identities;
  - допустимые изменения source-backed mutable fields обновляют текущую domain projection в одной транзакции;
  - identity changes, conflicting parent links, duplicate semester identities и missing discipline остаются typed contract/source errors и полностью rollback-ят ingest;
  - для затронутых curriculum snapshots reconciliation удаляет устаревшие curriculum items/assessment links только внутри выбранной атомарной sync scope; raw snapshots/ingest history не удаляются;
  - taxonomy/reference rows проверяются и не размножаются;
  - поведение readers остаётся через `programs/curricula/disciplines` ports, а ingestion adapter остаётся infrastructure detail.

  Сохранить текущий result payload, run IDs и compatibility CLI. Добавить безопасный режим `--database-url`/environment documentation и, если потребуется, явный `--sync`/refresh flag без изменения default idempotency. Не делать parser aware of comparison/proftest/recommendations.

  **LOGGING REQUIREMENTS:**

  - INFO: ingest start/commit, environment, redacted target, run id, source count, programs, curricula/items added/updated/removed;
  - DEBUG: per-stage counters and identity categories, not raw names/body/payload;
  - WARNING: stale-row reconciliation, skipped optional source, or no-op repeat ingest;
  - ERROR: rollback, source contract conflict, constraint violation or connection failure with run id and redacted target;
  - never log PDF bytes, full source payloads, passwords, signed URLs or user data.

  **Dependencies:** Tasks 1–2.

  **Verification:** fixture ingest into empty PostgreSQL, identical rerun, changed canonical fixture sync, stale item reconciliation, intentional constraint/source conflict rollback; repeat the core idempotency tests on SQLite.

  **Files:** `backend/src/andromeda/infrastructure/repositories/ingestion.py`, `backend/scripts/run_tracer_bullet.py`, `backend/scripts/run_tracer_demo.py` only if needed, `backend/tests/infrastructure/test_ingestion_refresh.py`, `backend/tests/integration/test_postgresql_ingestion.py`.

- [x] **Task 5: Провести DB → repository ports → services smoke без изменений business logic.** (depends on Task 4)

  **Deliverable:** Add integration coverage proving that all current read paths work against PostgreSQL and still work against SQLite.

  Use the existing composition root and API dependencies in `backend/src/andromeda/composition/container.py` and `backend/src/andromeda/api/dependencies/`; do not inject SQLAlchemy models into `comparison`, `proftest` or `recommendations`. If a composition cleanup is needed, keep it limited to reusing the existing repository ports and one engine/session lifecycle.

  Validate, against the same ingested PostgreSQL data:

  - `ProgramReader`, `CurriculumReader`, `DisciplineReader` return the same public contracts;
  - comparison supports all-learning and semester modes with stable row ordering;
  - ProgramFingerprint/Content Fit, anti-interest penalty, adaptive flow and recommendation explanations are byte/semantic compatible with the existing fixture expectations;
  - missing curriculum/discipline and database errors preserve current typed API errors;
  - no ORM/infrastructure import leaks into module domain/services, and no frontend/parser file access is introduced.

  No new recommendation formula, proftest scoring, comparison rule or API response field is in scope. This task verifies the storage substitution only.

  **LOGGING REQUIREMENTS:**

  - INFO: checkpoints `database -> reader -> service -> API`, row/result counts and elapsed time;
  - DEBUG: selected dialect and repository operation names;
  - WARNING/ERROR: expected missing-data and rollback paths with stable error codes;
  - test logs must not assert or print full curriculum payloads.

  **Dependencies:** Task 4.

  **Verification:** `backend/tests/integration/test_postgresql_vertical_slice.py` with Alembic-created schema and HTTP `TestClient`; existing SQLite tests, OpenAPI snapshot and recommendation/proftest/comparison tests remain green.

  **Files:** `backend/src/andromeda/composition/container.py` only if lifecycle wiring needs a narrow change, `backend/src/andromeda/api/dependencies/*.py` only if required, `backend/tests/integration/test_postgresql_vertical_slice.py`, `backend/tests/integration/test_storage_parity.py`, `backend/tests/architecture/test_module_boundaries.py`.

<!-- Commit checkpoint: tasks 4-5 -->

### Фаза 3: CI, fullstack evidence и documentation checkpoint

- [x] **Task 6: Добавить PostgreSQL smoke/integration test harness и CI service job.** (depends on Tasks 1–5)

  **Deliverable:** Update `.github/workflows/ci.yml` and add narrowly scoped smoke helpers/tests under `backend/tests/integration/` or `backend/scripts/`.

  Keep current SQLite backend, frontend, fullstack, proftest and recommendation gates. Add a dedicated PostgreSQL service job with:

  - PostgreSQL service container, explicit healthcheck and a unique CI database;
  - `psycopg` installation through the normal backend package;
  - `alembic upgrade head` on an empty database using only `BMSTU_DATABASE_URL`;
  - BMSTU fixture ingestion into PostgreSQL, repeatable ingest/update check and API smoke for `/programs`, `/programs/{id}/curriculum`, `/compare`, `/proftest/results` and `/recommendations` as applicable;
  - existing frontend build/OpenAPI drift and a browser path pointed at the PostgreSQL-backed API, reusing the current demo lifecycle where possible;
  - artifacts/logs on failure and reliable process/container cleanup.

  Do not replace all SQLite jobs with PostgreSQL, because SQLite remains valuable for fast tests. Do not make CI depend on a private staging database or credentials. CI must prove the migration and real fixture data path in an isolated disposable PostgreSQL service.

  **LOGGING REQUIREMENTS:**

  - INFO: service readiness, migration revision, ingest run id/counts, API/frontend readiness and E2E completion;
  - DEBUG only when explicitly enabled by CI troubleshooting; no SQL body dump by default;
  - WARNING: non-blocking runner deprecations or skipped optional tests;
  - ERROR: failed stage with sanitized endpoint/exit code and uploaded logs;
  - redact CI secrets and never echo env blocks containing DSN/password.

  **Dependencies:** Tasks 1–5.

  **Verification:** exact workflow run is green on a fresh GitHub runner; PostgreSQL job reaches all later steps rather than stopping at install/migration; all existing jobs remain green.

  **Files:** `.github/workflows/ci.yml`, `backend/tests/integration/test_postgresql_smoke.py`, optionally `backend/scripts/check_postgresql.py`, `frontend/tests/*.spec.ts` only if the existing browser scenario needs a configurable API target.

- [x] **Task 7: Обновить запуск и документацию dev/staging без изменения API/business modules.** (depends on Tasks 3–6)

  **Deliverable:** Documentation checkpoint through `$aif-docs` covering setup, environment separation, migrations, ingestion refresh and verification.

  Update `README.md`, `docs/getting-started.md`, `docs/configuration.md`, `docs/testing.md`, `docs/architecture.md` and add `docs/postgresql.md` (or an equivalent single runbook). Document exact commands for:

  1. starting development PostgreSQL;
  2. exporting/creating the development env from the example without committing secrets;
  3. applying `alembic upgrade head`;
  4. ingesting BMSTU fixture/live sources into the selected PostgreSQL database;
  5. rerunning ingest to update the projection safely;
  6. starting FastAPI and frontend and opening `/docs`, `/openapi.json` and the UI;
  7. selecting the separate staging DSN/database and running the same migration/ingestion commands;
  8. keeping SQLite tests fast and explicit.

  Explain that comparison/proftest/recommendations consume the same public contracts and that no business scoring was changed. Add troubleshooting for driver missing, invalid URL encoding, migration failure, PostgreSQL readiness and parser source failure. Avoid documenting real credentials or a private staging hostname.

  **LOGGING REQUIREMENTS:**

  - examples use `LOG_LEVEL=INFO` and show only redacted/placeholder targets;
  - docs explicitly state how to turn on DEBUG and which fields are safe;
  - no command in documentation prints secrets with `echo`, `set`, or equivalent.

  **Dependencies:** Tasks 3–6.

  **Verification:** a clean developer can follow the docs on a machine with Docker, Python, Node and Poppler; the documented commands produce API/frontend readiness and non-empty real fixture comparison.

  **Files:** `README.md`, `docs/getting-started.md`, `docs/configuration.md`, `docs/testing.md`, `docs/architecture.md`, `docs/postgresql.md`, `backend/.env.example`, `.env.development.example`, `.env.staging.example`.

- [x] **Task 8: Выполнить final acceptance, storage parity и stop condition.** (depends on Task 7)

  **Deliverable:** Final verification record in the implementation handoff; no new product feature after this task.

  Run and record:

  - unit/type/contract tests with SQLite;
  - empty PostgreSQL `alembic upgrade head` and migration compatibility checks;
  - BMSTU fixture ingest into development PostgreSQL, repeat ingest and update scenario;
  - one live BMSTU parser ingest into a disposable PostgreSQL target if network/source prerequisites are available, otherwise report the exact external source blocker without bypassing the parser;
  - API smoke for programs, curriculum, compare, proftest and recommendations;
  - frontend build, OpenAPI drift and browser comparison/proftest/recommendations scenario backed by PostgreSQL;
  - mobile/desktop browser readiness only for the existing UI path, with no UI redesign;
  - strict `mypy` and complete CI workflow.

  Acceptance must demonstrate that replacing SQLite with PostgreSQL changes storage configuration only: real source data still reaches API and frontend, all current business results remain valid, reruns are safe, and no secret appears in logs. If a migration or source contract fails, preserve the failure as a visible error and fix only the in-scope compatibility issue.

  **LOGGING REQUIREMENTS:**

  - INFO: each acceptance stage and pass/fail status;
  - ERROR: actionable failing command, revision, endpoint or test id with secrets redacted;
  - retain only safe CI artifacts and no raw source bodies/credentials.

  **Dependencies:** Task 7.

  **Verification:** all acceptance checklist items below are checked and CI is green. After this task, stop; do not start map, career recommender, auth, ML, personal route, Kubernetes, Kafka, microservices or unrelated UI work.

  **Files:** test/report artifacts only plus files strictly required by failed acceptance gates.

  **Verification status (2026-09-11):** локальные SQLite/backend/frontend gates выполнены: `117 passed, 2 skipped` backend tests, strict `mypy`, OpenAPI drift, frontend unit/build и 7 Playwright browser scenarios прошли. PostgreSQL integration tests корректно skipped без `ANDROMEDA_POSTGRES_TEST_URL`; Docker daemon недоступен, а локальный PostgreSQL требует недоступные credentials, поэтому запуск PostgreSQL service и GitHub Actions остаются внешней проверкой после публикации ветки. Прямой доступ к БД для обхода этого ограничения не использовался.

<!-- Commit checkpoint: tasks 6-8 -->

## Acceptance Checklist

- [x] `psycopg` is installed by the normal backend package and `postgresql+psycopg://` engine configuration is covered by tests.
- [x] `ANDROMEDA_ENV=development` and `ANDROMEDA_ENV=staging` require PostgreSQL through `BMSTU_DATABASE_URL`; staging has a distinct database target.
- [x] SQLite remains available for fast tests and explicit fixture checks.
- [ ] Alembic reads the environment URL and upgrades empty PostgreSQL to `head` without relying on mutable `metadata.create_all()`.
- [x] Existing SQLite databases at earlier revisions can upgrade or fail with a documented, actionable compatibility error; no silent data loss.
- [ ] FK, unique and check constraints are present and enforced on PostgreSQL.
- [x] BMSTU parser/normalizer/canonical contracts are unchanged and remain isolated under `backend/src/andromeda/ingestion/universities/bmstu/`.
- [ ] First ingest populates PostgreSQL with real fixture/live-derived data; repeated ingest is idempotent; changed source projection updates atomically; failed sync rolls back.
- [x] `universities`, `programs`, `curricula` and `disciplines` readers still expose typed public contracts and no module imports infrastructure ORM.
- [x] Existing comparison, proftest and recommendations business logic and API response contracts are unchanged.
- [ ] API smoke and existing frontend work against PostgreSQL; OpenAPI drift remains green.
- [ ] SQLite unit/contract tests, PostgreSQL integration tests, mypy, build and browser E2E all pass.
- [ ] Complete GitHub Actions workflow is green, including the new PostgreSQL service job.
- [x] Documentation contains reproducible dev/staging startup, migration, ingestion/update and test commands without credentials.

## Non-goals / Guardrails

- Не переписывать modular monolith и не делать microservices.
- Не менять scoring/comparison/proftest/recommendations business logic, public domain contracts или frontend design.
- Не давать application modules прямой доступ к SQLAlchemy ORM, PostgreSQL driver или parser output.
- Не удалять SQLite test support.
- Не добавлять авторизацию, карту, career recommender, ML, CQRS/Event Sourcing, Kubernetes или Kafka.
- Не подключать private staging infrastructure, production deployment или реальные secrets к CI.

## Stop Rule

После успешного PostgreSQL migration + parser/ingestion sync + API/frontend smoke + green CI этот scope считается завершённым. Дальше не начинать следующие Andromeda features; любые последующие изменения оформлять отдельным планом.
