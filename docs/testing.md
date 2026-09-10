[← Конфигурация](configuration.md) · [Back to README](../README.md)

# Тестирование

## Backend

```powershell
cd backend
python -m pytest -q
python -m mypy
```

Тесты покрывают module contracts, parser → canonical boundary, identity resolution, DB constraints, atomic repositories, API и полный backend vertical slice. Отдельные проверки гарантируют наличие всех 22 областей, покрытие текущих 101 уникальных BMSTU-дисциплин, сумму каждого вектора `1.0000`, сохранение area weights в SQLite и агрегацию содержания по часам/ЗЕТ.

Миграция `0003_discipline_taxonomy` создаёт справочник областей и таблицы весов дисциплин. Fixture smoke прогоняет цепочку ingestion → repository → comparison → API на чистой и повторно используемой SQLite-базе.

## Frontend

```powershell
cd frontend
npm run build
$env:OPENAPI_FILE="openapi.json"
npm run check-api-drift
npm run test:e2e
```

E2E-тест использует стабильные `data-testid`, выбирает scope семестра и проверяет видимую таблицу сравнения. Перед ним должен работать fixture demo:

```powershell
python backend/scripts/run_tracer_demo.py --mode fixture
```

## CI

GitHub Actions запускает backend tests/mypy, экспорт OpenAPI и drift gate, frontend build, fixture smoke и Chromium E2E. Poppler и браузер устанавливаются в CI job.

## See Also

- [API](api.md) — контракты, которые проверяются drift gate.
- [Быстрый старт](getting-started.md) — локальный fixture demo.
