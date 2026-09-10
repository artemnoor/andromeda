[← API](api.md) · [Back to README](../README.md) · [Тестирование →](testing.md)

# Конфигурация

Настройки читаются через `andromeda.infrastructure.config.Settings`. Примеры переменных находятся в `backend/.env.example` и `frontend/.env.example`.

| Переменная | Компонент | По умолчанию | Назначение |
|---|---|---|---|
| `BMSTU_DATABASE_URL` | backend | `sqlite:///./data/tracer.db` | SQLAlchemy storage |
| `VITE_FRONTEND_ORIGIN` | backend | `http://localhost:5173` | CORS origin |
| `LOG_LEVEL` | backend | `INFO` | logging level |
| `VITE_API_BASE_URL` | frontend | empty | API base URL; empty uses Vite proxy |
| `VITE_LOG_LEVEL` | frontend | `WARN` | client diagnostics |

Для повторяемого fixture-запуска database URL можно передать явно:

```powershell
python backend/scripts/run_tracer_bullet.py --mode fixture --database-url sqlite:///./data/tracer.db
```

`LOG_LEVEL=DEBUG` включает технические stage-сообщения, но raw response body, PDF text и signed query strings в логах не выводятся.

## See Also

- [Быстрый старт](getting-started.md) — установка и запуск.
- [Архитектура](architecture.md) — infrastructure boundary.
- [Тестирование](testing.md) — CI variables and commands.
