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

## Frontend

```powershell
cd frontend
npm run build
$env:OPENAPI_FILE="openapi.json"
npm run check-api-drift
npm run test:unit
npm run test:e2e
```

E2E-тест использует стабильные `data-testid`, сохраняет existing comparison coverage и проходит профтест до explainable recommendation на desktop/mobile. `admissions.spec.ts` открывает страницу реальной программы, проверяет offering, места, ЕГЭ, стоимость и переключение программы на desktop/mobile. `recommendations.spec.ts` отдельно проверяет Content Fit, блоки дисциплин, семестры, reasons/anti-reasons и отсутствие горизонтального overflow. Перед ним должен работать fixture demo:

```powershell
python backend/scripts/run_tracer_demo.py --mode fixture
```

Recommendation tests дополнительно проверяют strict contracts и module boundary, неизменность детерминированного ranking, tie-break по коду, монотонный anti-interest penalty, evidence-backed explanations, пять synthetic personas, empty catalog и DB → catalog adapter → service → API путь.

## CI

GitHub Actions запускает backend tests/mypy, recommendation module/API integration gate, экспорт OpenAPI и drift gate, frontend build, fixture smoke и Chromium E2E. Отдельный `postgresql-integration` job поднимает disposable PostgreSQL 16 service, применяет Alembic к пустой базе, прогоняет BMSTU fixture → API → frontend и выполняет PostgreSQL-backed browser scenario. Poppler и браузер устанавливаются в CI jobs.

Для локального PostgreSQL запуска используйте [руководство PostgreSQL](postgresql.md). Без test DSN PostgreSQL-only tests явно помечаются skipped; CI обязан передавать `ANDROMEDA_POSTGRES_TEST_URL`.

## See Also

- [API](api.md) — контракты, которые проверяются drift gate.
- [Быстрый старт](getting-started.md) — локальный fixture demo.
- [PostgreSQL](postgresql.md) — storage integration commands.
