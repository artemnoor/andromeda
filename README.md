# Andromeda BMSTU

> Сравнение реальных образовательных программ МГТУ через один строгий контракт.

Andromeda — modular monolith для source-backed данных учебных планов. Первый полноценный vertical slice позволяет выбрать две программы, сравнить их целиком или по семестру и увидеть дисциплины, блоки, часы, ЗЕТ, формы контроля и разницы.

## Быстрый старт

```powershell
python -m pip install -e "backend[dev]"
python backend/scripts/run_tracer_demo.py --mode fixture --check
```

После запуска API доступен на `http://127.0.0.1:8000/docs`, UI — на `http://127.0.0.1:3000/`. Для ручной работы уберите `--check`.

Для обычной dev-работы используйте PostgreSQL: инструкции находятся в [руководстве PostgreSQL](docs/postgresql.md). SQLite остаётся быстрым test fallback.

## Что уже работает

- BMSTU fixture/live ingestion с provenance и fail-closed source selection.
- Изолированные модули universities, programs, curricula, disciplines, comparison, proftest, recommendations, admissions и admission_fit.
- SQLAlchemy/Alembic с FK, unique/check constraints и Decimal без float-конверсии.
- FastAPI/OpenAPI и сгенерированные TypeScript-типы.
- Выбор программ A/B, scope «всё обучение / семестр», блоки и состояния loading/empty/error.
- Профиль содержания: короткое ядро из пяти вопросов, preliminary topic chips, bounded adaptive refinement и TOP реальных программ с объяснениями по учебному плану. Новая session-сессия использует `proftest-v3`; старые pinned `proftest-v2` продолжают читаться.
- Persistence профиля: completed `UserProfile` хранится по anonymous HttpOnly session cookie и восстанавливается после перезагрузки UI.
- Recommendation vertical slice: готовый `UserProfile` → детерминированный Content Fit → reasons/anti-reasons по реальному fingerprint.
- Admissions vertical slice: реальные BMSTU данные поступления по canonical `program_id` — места, ЕГЭ и минимумы, квоты, проходные баллы, стоимость и форма обучения.

### Профиль содержания

В UI выберите «Профиль содержания». Flow получает вопросы и результаты только через API: `GET /proftest/questions`, `POST /proftest/preview` и `POST /proftest/results`. Финальный результат сохраняется в Andromeda по anonymous HttpOnly cookie; после reload UI использует `GET /proftest/profile` и `GET /recommendations/current`. Готовый профиль также можно передать в `POST /recommendations`. После изменения API обновите frontend-контракт:

```powershell
python backend/scripts/export_openapi.py --out frontend-next/openapi.json
cd frontend-next
npm run generate-api
npm run check-api-drift
```

`Content Fit` рассчитывается детерминированно по реальным часам/ЗЕТ и долям предметных областей. В recommendation response `Workload readiness` и `Career Fit` пока имеют статус `not_available`; отдельный `Admission Fit` запускается на странице программы и не влияет на Content Fit или ranking рекомендаций.

### Данные поступления

В UI выберите «Программа». Страница получает карточку и `GET /programs/{id}/admissions` через generated OpenAPI client. Данные поступления проходят тот же BMSTU parser → canonical contracts → PostgreSQL/SQLite repository → FastAPI flow; отсутствующие официальные значения не заменяются нулями.

## Пример

```text
GET /compare?programIds=<program-id-a>,<program-id-b>&scope=semester&semester=1
```

Ответ содержит rows со статусами `both`, `different`, `only_a`, `only_b`, а также totals и blocks.

## Документация

| Гид | Содержание |
|---|---|
| [Быстрый старт](docs/getting-started.md) | Установка и первый запуск |
| [Архитектура](docs/architecture.md) | Модули и поток данных |
| [API](docs/api.md) | OpenAPI endpoints и контракты |
| [Admissions](docs/admissions.md) | Данные поступления и source gaps |
| [Admission Fit](docs/admission-fit.md) | Отдельная оценка реалистичности поступления |
| [Конфигурация](docs/configuration.md) | Переменные окружения |
| [PostgreSQL](docs/postgresql.md) | Dev/staging, migrations и ingestion |
| [Тестирование](docs/testing.md) | Локальные и CI-проверки |

## Лицензия

Лицензия проекта не задана в текущем репозитории.
