[Back to README](../README.md) · [Архитектура →](architecture.md)

# Быстрый старт

## Требования

- Python 3.11+;
- Node.js 22+ и npm;
- Poppler `pdftotext` для PDF учебных планов;
- Chromium для browser E2E-проверки.

## Установка

```powershell
python -m pip install -e "backend[dev]"
cd frontend
npm ci
npx playwright install chromium
cd ..
```

## Fixture-запуск

Из корня репозитория:

```powershell
python backend/scripts/run_tracer_demo.py --mode fixture --check
```

Команда прогоняет captured BMSTU sources через ingestion, Alembic, SQLite, FastAPI и Vite, затем проверяет compare endpoint. Для ручного просмотра используйте ту же команду без `--check`.

## Проверка результата

- UI: `http://127.0.0.1:5173/`;
- Swagger: `http://127.0.0.1:8000/docs`;
- OpenAPI: `http://127.0.0.1:8000/openapi.json`.

Для live-источников:

```powershell
python backend/scripts/run_tracer_demo.py --mode live
```

## See Also

- [Архитектура](architecture.md) — границы модулей и ingestion.
- [Тестирование](testing.md) — полный набор локальных проверок.
