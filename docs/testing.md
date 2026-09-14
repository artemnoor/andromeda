[← PostgreSQL](postgresql.md) · [Back to README](../README.md)

# Тестирование

## Backend

```powershell
cd backend
python -m pytest -q
python -m mypy
```

Тесты покрывают module contracts, parser → canonical boundary, identity resolution, DB constraints, atomic repositories, API и полный backend vertical slice. Отдельные проверки гарантируют наличие всех 22 областей, покрытие текущих 101 уникальных BMSTU-дисциплин, сумму каждого вектора `1.0000`, сохранение area weights в SQLite и агрегацию содержания по часам/ЗЕТ.

Миграция `0003_discipline_taxonomy` создаёт справочник областей и таблицы весов дисциплин. Fixture smoke прогоняет цепочку ingestion → repository → comparison → API на чистой и повторно используемой SQLite-базе. PostgreSQL integration tests используют Alembic, а не `Base.metadata.create_all()`, и проверяют migration chain, FK/unique/check constraints, idempotent rerun, projection update и rollback.

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

Admin/Ops data-quality slice проверяется отдельным bounded read-only набором:

```powershell
cd backend
python -m pytest -q tests/modules/admin_ops tests/api/test_admin_ops_contract.py tests/api/test_admin_ops_api.py tests/infrastructure/test_admin_ops_repository.py tests/integration/test_admin_ops_vertical_slice.py tests/vertical/test_admin_ops_vertical_contract.py tests/infrastructure/test_atomic_ingest.py
python -m pytest -q tests/architecture/test_module_boundaries.py
python -m mypy
```

Проверки покрывают lifecycle `running → completed|failed`, сохранение failed audit после rollback, deterministic list/detail, malformed audit data, explicit key guard, отсутствие raw source fields и OpenAPI operation IDs. Admin/Ops endpoint выключен без `ANDROMEDA_OPS_API_KEY`; ключ не попадает в логи или ответы.

Personal Route проверяется отдельными contract/API и vertical tests:

```powershell
cd backend
python -m pytest -q tests/modules/personal_route tests/api/test_personal_route_api.py tests/api/test_personal_route_contract.py tests/integration/test_personal_route_vertical_slice.py tests/vertical/test_personal_route_scope_guard.py
```

Набор проверяет deterministic plan ordering, current-profile isolation, recommendation-to-event filtering, canonical event/venue/point links, online events without a point, fixed-clock behavior for past events и отсутствие map/storage dependencies. PostgreSQL job повторяет fixture → repository → profile → personal plan flow.

## Frontend

```powershell
cd frontend
npm run build
$env:OPENAPI_FILE="openapi.json"
npm run check-api-drift
npm run test:unit
npm run test:e2e
```

E2E-тест использует стабильные `data-testid`, сохраняет existing comparison coverage и проходит профтест до explainable recommendation на desktop/mobile. Отдельный browser scenario завершает тест, очищает local draft и проверяет восстановление профиля и current recommendations по cookie/API. `personal-route.spec.ts` проверяет profile-required state, логические program/event steps, карточку известной точки, ссылку регистрации и отсутствие горизонтального overflow на mobile; карта и навигационные действия не тестируются, потому что не входят в slice. `admissions.spec.ts` открывает страницу реальной программы, проверяет offering, места, ЕГЭ, стоимость и переключение программы на desktop/mobile. `recommendations.spec.ts` отдельно проверяет Content Fit, блоки дисциплин, семестры, reasons/anti-reasons и отсутствие горизонтального overflow. `admission-fit.spec.ts` открывает тот же program flow, выбирает source-backed offering, вводит баллы, проверяет отдельный score/status/reasons и повторяет сценарий на viewport 390px без горизонтального overflow. Перед ним должен работать fixture demo:

```powershell
python backend/scripts/run_tracer_demo.py --mode fixture
```

Recommendation tests дополнительно проверяют strict contracts и module boundary, неизменность детерминированного ranking, tie-break по коду, монотонный anti-interest penalty, evidence-backed explanations, пять synthetic personas, empty catalog и DB → catalog adapter → service → API путь.

Persistence-проверки включают strict `ProfileScope`/`UserProfileSnapshot`, anonymous cookie isolation, revision conflict, migration `0005_user_profiles`, repository transaction, SQLite migration → BMSTU ingestion → `POST /proftest/results` → `GET /proftest/profile` → `GET /recommendations/current` и PostgreSQL smoke. Профиль не смешивается с Admission Fit и Content Fit ranking.

Для focused запуска:

```powershell
python -m pytest -q tests/api/test_proftest_profile_api.py tests/integration/test_user_profile_persistence.py tests/infrastructure/test_user_profile_repository.py
```

Frontend unit-тесты проверяют Admission Fit loading/empty/error/success states и структуру отправляемого payload. Browser E2E прогоняется на Chromium desktop и mobile project.

## CI

GitHub Actions запускает backend tests/mypy, recommendation и Admission Fit module/API integration gates, экспорт OpenAPI и drift gate, frontend build, fixture smoke и Chromium E2E. Отдельный `postgresql-integration` job поднимает disposable PostgreSQL 16 service, применяет Alembic к пустой базе, прогоняет BMSTU fixture → API → frontend и выполняет PostgreSQL-backed browser scenario. Poppler и браузер устанавливаются в CI jobs.

Для локального PostgreSQL запуска используйте [руководство PostgreSQL](postgresql.md). Без test DSN PostgreSQL-only tests явно помечаются skipped; CI обязан передавать `ANDROMEDA_POSTGRES_TEST_URL`.

## See Also

- [API](api.md) — контракты, которые проверяются drift gate.
- [Быстрый старт](getting-started.md) — локальный fixture demo.
- [PostgreSQL](postgresql.md) — storage integration commands.
