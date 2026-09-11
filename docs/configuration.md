[← Admission Fit](admission-fit.md) · [Back to README](../README.md) · [PostgreSQL →](postgresql.md)

# Конфигурация

Настройки читаются через `andromeda.infrastructure.config.Settings`. Примеры переменных находятся в `backend/.env.example`, `.env.development.example`, `.env.staging.example` и `frontend/.env.example`.

| Переменная | Компонент | По умолчанию | Назначение |
|---|---|---|---|
| `ANDROMEDA_ENV` | backend | `test` | Окружение: `test`, `development` или `staging`; non-test требует PostgreSQL |
| `BMSTU_DATABASE_URL` | backend | SQLite fallback | Единый SQLAlchemy storage target для API, Alembic и ingestion |
| `BMSTU_DB_POOL_SIZE` | backend | `5` | PostgreSQL connection pool size |
| `BMSTU_DB_MAX_OVERFLOW` | backend | `10` | Дополнительные PostgreSQL connections |
| `BMSTU_DB_POOL_TIMEOUT` | backend | `30` | Ожидание connection из pool, seconds |
| `BMSTU_DB_POOL_RECYCLE` | backend | `1800` | Connection recycle interval, seconds |
| `VITE_FRONTEND_ORIGIN` | backend | `http://localhost:5173` | CORS origin |
| `LOG_LEVEL` | backend | `INFO` | logging level |
| `VITE_API_BASE_URL` | frontend | empty | API base URL; empty uses Vite proxy |
| `VITE_LOG_LEVEL` | frontend | `WARN` | client diagnostics |

Для повторяемого fixture-запуска database URL можно передать явно:

```powershell
python backend/scripts/run_tracer_bullet.py --mode fixture --database-url sqlite:///./data/tracer.db
```

`LOG_LEVEL=DEBUG` включает технические stage-сообщения, но raw response body, PDF text и signed query strings в логах не выводятся.

В development/staging credentials передаются только через environment. Database URL в логах редактируется до `dialect://host:port/database`; password и query parameters не выводятся. SQLite fallback предназначен для быстрых тестов и старых локальных команд, не для staging.

## See Also

- [Быстрый старт](getting-started.md) — установка и запуск.
- [Архитектура](architecture.md) — infrastructure boundary.
- [PostgreSQL](postgresql.md) — dev/staging database runbook.
- [Тестирование](testing.md) — CI variables and commands.
