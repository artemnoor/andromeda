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
| `VITE_FRONTEND_ORIGIN` | backend | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated trusted CORS/CSRF origins |
| `LOG_LEVEL` | backend | `INFO` | logging level |
| `ANDROMEDA_PROFILE_COOKIE_NAME` | backend | `andromeda_profile_session` | Anonymous profile cookie name |
| `ANDROMEDA_PROFILE_COOKIE_MAX_AGE` | backend | `2592000` | Browser cookie lifetime, seconds |
| `ANDROMEDA_PROFILE_TTL_SECONDS` | backend | `2592000` | Persisted profile retention, seconds |
| `ANDROMEDA_PROFILE_COOKIE_SECURE` | backend | `false` in test/dev, `true` in staging | Require HTTPS for the profile cookie |
| `ANDROMEDA_PROFILE_COOKIE_SAMESITE` | backend | `lax` | Cookie SameSite policy (`lax`, `strict`, `none`; `none` requires Secure) |
| `ANDROMEDA_AUTH_COOKIE_NAME` | backend | `andromeda_auth_session` | Auth session cookie name |
| `ANDROMEDA_AUTH_COOKIE_MAX_AGE` | backend | `2592000` | Auth cookie lifetime, seconds |
| `ANDROMEDA_AUTH_SESSION_TTL_SECONDS` | backend | `2592000` | Server-side session expiry, seconds |
| `ANDROMEDA_AUTH_COOKIE_SECURE` | backend | `false` in test/dev, `true` in staging | Require HTTPS for auth cookie |
| `ANDROMEDA_AUTH_COOKIE_SAMESITE` | backend | `lax` | Auth cookie SameSite policy; `none` requires Secure |
| `ANDROMEDA_AUTH_PASSWORD_MIN_LENGTH` | backend | `12` | Registration password minimum |
| `VITE_API_BASE_URL` | frontend | empty | API base URL; empty uses Vite proxy |
| `VITE_LOG_LEVEL` | frontend | `WARN` | client diagnostics |

Для повторяемого fixture-запуска database URL можно передать явно:

```powershell
python backend/scripts/run_tracer_bullet.py --mode fixture --database-url sqlite:///./data/tracer.db
```

`LOG_LEVEL=DEBUG` включает технические stage-сообщения, но raw response body, PDF text и signed query strings в логах не выводятся.

В development/staging credentials передаются только через environment. Database URL в логах редактируется до `dialect://host:port/database`; password и query parameters не выводятся. SQLite fallback предназначен для быстрых тестов и старых локальных команд, не для staging.

Profile persistence is anonymous by default: the server creates an opaque HttpOnly cookie, stores only its SHA-256 hash, and expires the profile after `ANDROMEDA_PROFILE_TTL_SECONDS`. The browser must not copy this cookie into LocalStorage or JavaScript state. Use `Secure=true` with HTTPS in staging; local HTTP development keeps it `false`.

Account sessions are persistent server-side rows with revocation and expiry. Profile binding is deterministic: anonymous-only transfers, account profile wins on conflict, and no field-level merge occurs. State-changing auth calls with an `Origin` header require a configured `VITE_FRONTEND_ORIGIN` value.

## See Also

- [Быстрый старт](getting-started.md) — установка и запуск.
- [Архитектура](architecture.md) — infrastructure boundary.
- [PostgreSQL](postgresql.md) — dev/staging database runbook.
- [Тестирование](testing.md) — CI variables and commands.
