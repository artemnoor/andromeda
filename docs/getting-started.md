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

Команда прогоняет captured BMSTU sources через ingestion, Alembic, SQLite, FastAPI и Vite, затем проверяет compare и admissions endpoints. Для ручного просмотра используйте ту же команду без `--check`.

## Проверка результата

- UI: `http://127.0.0.1:5173/`;
- Swagger: `http://127.0.0.1:8000/docs`;
- OpenAPI: `http://127.0.0.1:8000/openapi.json`.

В UI откройте раздел «Программа», выберите одну из программ и дождитесь блока «Поступление». В нём отображаются текущие места и минимумы, исторические проходные баллы, а для платного набора — стоимость, если эти поля есть в captured BMSTU source. Ссылка «Источник» ведёт на официальный detail page.

Для live-источников:

```powershell
python backend/scripts/run_tracer_demo.py --mode live
```

## PostgreSQL dev

Для обычного запуска поднимите отдельный development target:

```powershell
Copy-Item .env.development.example .env.development
docker compose --env-file .env.development -f ops/postgres/docker-compose.yml --profile development up -d postgres-dev
$env:ANDROMEDA_ENV = "development"
$env:BMSTU_DATABASE_URL = "postgresql+psycopg://andromeda:change-me@127.0.0.1:5432/andromeda_dev"
python -m alembic upgrade head
python backend/scripts/run_tracer_bullet.py --mode fixture --database-url $env:BMSTU_DATABASE_URL
```

После ingestion запустите API и frontend отдельными процессами либо через demo runner с тем же `--database-url`. Для staging используйте `.env.staging.example`, профиль `staging`, порт `5433` и базу `andromeda_staging`. Подробности, refresh и troubleshooting — в [руководстве PostgreSQL](postgresql.md).

## See Also

- [Архитектура](architecture.md) — границы модулей и ingestion.
- [Тестирование](testing.md) — полный набор локальных проверок.
