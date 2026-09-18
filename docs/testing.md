[← PostgreSQL](postgresql.md) · [Back to README](../README.md)

# Тестирование

## Backend

Multi-university HSE gate:

```powershell
python -m pytest -q tests/ingestion/test_hse_parser.py tests/integration/test_hse_full_ingestion.py
```

Проверяются official fixture metadata, HSE parser → canonical → persistence, admissions/curricula, repeat ingestion и coexistence с BMSTU при одинаковом direction code.

```powershell
cd backend
python -m pytest -q
python -m mypy
```

Тесты покрывают module contracts, parser → canonical boundary, dynamic BMSTU catalog identity, DB constraints, atomic repositories, API и полный backend vertical slice. Отдельные проверки гарантируют наличие всех 22 областей, положительные deterministic vectors BMSTU taxonomy, сумму каждого вектора `1.0000`, сохранение area weights в SQLite и агрегацию содержания по часам/ЗЕТ. Последний полный live audit дал 2 582 уникальные дисциплины: у всех есть valid `area_weights`, `fallback_unclassified = 0`, используются 21 из 22 областей (отсутствующая область зафиксирована как отсутствие источника).

Миграция `0003_discipline_taxonomy` создаёт справочник областей и таблицы весов дисциплин. Fixture smoke прогоняет цепочку ingestion → repository → comparison → API на чистой и повторно используемой SQLite-базе. PostgreSQL integration tests используют Alembic, а не `Base.metadata.create_all()`, и проверяют migration chain, FK/unique/check constraints, idempotent rerun, projection update и rollback. Для full BMSTU ingestion повторный live run должен сохранить canonical counts без дублей и допускает только обновление provenance/curriculum metadata.

Admission Fit покрывается отдельным набором:

```powershell
cd backend
python -m pytest -q tests/modules/admission_fit tests/api/test_admission_fit_api.py tests/api/test_admission_fit_contract.py tests/integration/test_admission_fit_vertical_slice.py
```

Набор проверяет strict contracts, нормализацию и неоднозначность предметов, четыре статуса, minimum/passing/completeness breakdown, provenance-backed reasons, отсутствие влияния на recommendation ranking и synthetic personas. `test_admission_fit_vertical_slice.py` прогоняет BMSTU fixture parser → canonical admissions → SQLite repository → FastAPI endpoint. PostgreSQL smoke добавляется командой:

```powershell
$env:ANDROMEDA_POSTGRES_TEST_URL = "postgresql+psycopg://..."
python -m pytest -q tests/integration/test_postgresql_smoke.py tests/integration/test_storage_parity.py
```

Без PostgreSQL DSN smoke-тест явно `skipped`; CI передаёт disposable PostgreSQL URL.

Decision/Shortlist и отсутствие линейной зависимости проверяются отдельно:

```powershell
cd backend
python -m pytest -q tests/modules/decision tests/api/test_decision_routes.py tests/infrastructure/test_decision_analytics.py tests/integration/test_no_linear_flow.py
```

Набор проверяет owner-bound `DecisionContext`, optimistic revision, explicit
add/remove/restore/role transitions, отсутствие silent prune после изменения
ограничений, derived suggestions и batch Admission Fit. `test_no_linear_flow.py`
подтверждает, что свежий anonymous scope может открыть context, catalog,
comparison, admissions и Admission Fit без `UserProfile`, proftest или
Personal Route.

Для order-derived minima используйте focused набор:

```powershell
cd backend
python -m pytest -q tests/ingestion/test_bmstu_source_capture.py tests/ingestion/test_bmstu_orders_metadata.py tests/ingestion/test_bmstu_admission_orders_parser.py tests/ingestion/test_bmstu_admissions_normalizer.py tests/ingestion/test_bmstu_admissions_parser.py
python -m pytest -q tests/infrastructure/test_admissions_repository.py tests/infrastructure/test_alembic_migrations.py tests/api/test_andromeda_api.py
```

Проверяется migration `0010_admission_passing_route`, backfill старых numeric rows, route/BVI round-trip, deterministic minimum/provenance, API JSON и отсутствие `null балла` в UI. OpenAPI обновляется перед drift gate:

```powershell
python backend/scripts/export_openapi.py --out frontend-next/openapi.json
cd frontend-next
$env:OPENAPI_FILE = "openapi.json"
npm run generate-api
npm run check-api-drift
npm run test:unit
npm run build
```

Повторяемый SQLite smoke полного runner:

```powershell
python backend/scripts/run_andromeda_ingestion.py --university all --mode fixture --database-url sqlite:///backend/data/andromeda-admission-ci.db --log-level INFO
python backend/scripts/run_andromeda_ingestion.py --university all --mode fixture --database-url sqlite:///backend/data/andromeda-admission-ci.db --log-level INFO
```

На live smoke runner динамически читает только официальный [orders manifest](https://priem.bmstu.ru/lists/orders.json) и сохраняет source gaps вместо нулевых или выдуманных баллов. В CI live сеть не требуется: используются sanitized source excerpts и injected fetchers.

Admin/Ops data-quality slice проверяется отдельным bounded read-only набором:

```powershell
cd backend
python -m pytest -q tests/modules/admin_ops tests/api/test_admin_ops_contract.py tests/api/test_admin_ops_api.py tests/infrastructure/test_admin_ops_repository.py tests/integration/test_admin_ops_vertical_slice.py tests/vertical/test_admin_ops_vertical_contract.py tests/infrastructure/test_atomic_ingest.py
python -m pytest -q tests/architecture/test_module_boundaries.py
python -m mypy
```

Проверки покрывают lifecycle `running → completed|failed`, сохранение failed audit после rollback, deterministic list/detail, bounded fixture retry, running conflict, staging-only live boundary, malformed audit data, explicit key guard, отсутствие raw source fields и OpenAPI operation IDs. Admin/Ops endpoint выключен без `ANDROMEDA_OPS_API_KEY`; ключ не попадает в логи или ответы. Browser check открывает только `/#ops`, проверяет safe detail, unavailable conflict notice, confirmation перед retry и wrong-key error state.

Personal Route проверяется отдельными contract/API и vertical tests как
совместимый optional support layer:

```powershell
cd backend
python -m pytest -q tests/modules/personal_route tests/api/test_personal_route_api.py tests/api/test_personal_route_contract.py tests/integration/test_personal_route_vertical_slice.py tests/vertical/test_personal_route_scope_guard.py
```

Набор проверяет deterministic plan ordering, current-profile isolation, recommendation-to-event filtering, canonical event/venue/point links, online events without a point, fixed-clock behavior for past events и отсутствие map/storage dependencies. Отдельно проверяется, что DecisionService не вызывает этот модуль и что отсутствие profile не закрывает каталог/сравнение/поступление. PostgreSQL job повторяет fixture → repository → profile → optional support read flow.

## Canonical Next frontend

```powershell
cd frontend-next
npm run build
$env:OPENAPI_FILE="openapi.json"
npm run check-api-drift
npm run test:unit
npm run test:e2e
```

E2E-тест использует стабильные `data-testid`, сохраняет existing comparison coverage и проходит профтест до explainable recommendation на desktop/mobile. Отдельный browser scenario завершает тест, очищает local draft и проверяет восстановление профиля и current recommendations по cookie/API. `legacy-flow-compat.spec.ts` проверяет, что старый `flow` URL открывает нейтральный DecisionContext без mandatory funnel. `events-support-layer.spec.ts` проверяет optional personal route, source-backed event-to-program links и видимый source gap для события без связи; просмотр не меняет shortlist. `admissions.spec.ts` открывает страницу реальной программы, проверяет offering, места, ЕГЭ, стоимость и переключение программы на desktop/mobile. `recommendations.spec.ts` отдельно проверяет Content Fit, блоки дисциплин, семестры, reasons/anti-reasons и отсутствие горизонтального overflow. `admission-fit.spec.ts` открывает тот же program flow, выбирает source-backed offering, вводит баллы, проверяет отдельный score/status/reasons и повторяет сценарий на viewport 390px без горизонтального overflow. Перед ним должен работать fixture demo:

```powershell
python backend/scripts/run_andromeda_demo.py --mode fixture
```

Recommendation tests дополнительно проверяют strict contracts и module boundary, неизменность детерминированного ranking, tie-break по коду, монотонный anti-interest penalty, evidence-backed explanations, пять synthetic personas, empty catalog и DB → catalog adapter → service → API путь.

Persistence-проверки включают strict `ProfileScope`/`UserProfileSnapshot`, anonymous cookie isolation, revision conflict, migration `0005_user_profiles`, repository transaction, SQLite migration → BMSTU ingestion → `POST /proftest/results` → `GET /proftest/profile` → `GET /recommendations/current` и PostgreSQL smoke. Auth-проверки дополнительно покрывают Argon2 hash, opaque/revocable sessions, cookie flags, trusted Origin, anonymous → account transfer, account-profile-wins conflict и cross-account isolation. Профиль не смешивается с Admission Fit и Content Fit ranking.

Session-driven adaptive proftest имеет focused backend gate:

```powershell
python -m pytest -q tests/api/test_proftest_sessions_api.py tests/modules/proftest
python -m mypy src/andromeda/modules/proftest src/andromeda/api
```

Он покрывает version-pinned вопросы v3/v2, ровно пять core submissions,
preliminary topics, 7/8/9-step adaptive personas и cap 4,
five-plus component mechanics,
uncertain/skipped answers, deterministic adaptive selection и stop reasons,
stale revision conflicts, early-answer invalidation, guest ownership,
completed session resume, atomic profile persistence, analytics replay,
bounded payload validation и expiry. Полный browser gate запускается через
fixture demo на отдельном порту, если стандартный локальный frontend занят:

```powershell
$env:PLAYWRIGHT_BASE_URL = "http://127.0.0.1:3001"
python backend/scripts/run_andromeda_demo.py --mode fixture --api-port 8010 --frontend-port 3001
cd frontend-next
npx playwright test --workers=1
```

Browser scenarios проверяют desktop/mobile completion, reload resume,
completed-result recovery, auth/guest menu, independent entry points и
существующие catalog/comparison/admissions/events/recommendations/support
contracts. В
двухпрограммном fixture adaptive selector может завершиться с
`insufficient_candidate_spread`; это явный source-backed gap, а не
синтетический adaptive вопрос.

Локальный gate canonical Next включает backend pytest/mypy, Next unit, lint,
build, OpenAPI drift и Playwright на desktop/mobile проектах. Browser suite
запускает одинаковые сценарии на desktop и mobile; число сценариев определяется
файлами в `frontend-next/tests`, а не фиксированным списком. Шесть
backend PostgreSQL cases без `ANDROMEDA_POSTGRES_TEST_URL` явно skipped
локально, а CI job `postgresql-integration` поднимает PostgreSQL 16 и
выполняет их с миграциями.

Для focused запуска:

```powershell
python -m pytest -q tests/api/test_auth_api.py tests/api/test_proftest_profile_api.py tests/integration/test_user_profile_persistence.py tests/infrastructure/test_user_profile_repository.py
```

Next unit-тесты проверяют API mapping/error/timeout contracts, а browser E2E
прогоняется на Chromium desktop и mobile projects.

## CI

GitHub Actions запускает backend tests/mypy, canonical Next contract/unit/lint/build gates, fixture smoke и Chromium E2E. Отдельный `postgresql-integration` job поднимает disposable PostgreSQL 16 service, применяет Alembic к пустой базе, прогоняет BMSTU fixture → API → `frontend-next` и выполняет PostgreSQL-backed browser scenario. Poppler и браузер устанавливаются в CI jobs.

Перед отправкой изменений полный локальный gate повторяет существенные CI
границы:

```powershell
git diff --check
cd backend
python -m pytest -q
python -m mypy
cd ..\frontend-next
npm run check-api-drift
npm run test:unit
npm run lint
npm run build
npm run test:e2e
```

Для migration parity применяйте `alembic upgrade head`, downgrade до revision
перед DecisionContext, повторный `upgrade head` на SQLite и PostgreSQL; `python
-m alembic heads` должен вернуть одну голову `0014_decision_analytics`.

Analytics tests проверяют allowlist, bounded canonical IDs, отсутствие raw
profile/score/cookie/source body, owner isolation, idempotency и то, что отказ
telemetry не блокирует shortlist mutation. Browser events допускают только
safe view/interaction payload; authoritative shortlist size before/after
создаётся сервером.

Для локального PostgreSQL запуска используйте [руководство PostgreSQL](postgresql.md). Без test DSN PostgreSQL-only tests явно помечаются skipped; CI обязан передавать `ANDROMEDA_POSTGRES_TEST_URL`.

## See Also

- [API](api.md) — контракты, которые проверяются drift gate.
- [Быстрый старт](getting-started.md) — локальный fixture demo.
- [PostgreSQL](postgresql.md) — storage integration commands.
