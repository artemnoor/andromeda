# Andromeda BMSTU

> Сравнение реальных образовательных программ МГТУ через один строгий контракт.

Andromeda — modular monolith для source-backed данных учебных планов. Первый полноценный vertical slice позволяет выбрать две программы, сравнить их целиком или по семестру и увидеть дисциплины, блоки, часы, ЗЕТ, формы контроля и разницы.

## Быстрый старт

```powershell
python -m pip install -e "backend[dev]"
python backend/scripts/run_tracer_demo.py --mode fixture --check
```

После запуска API доступен на `http://127.0.0.1:8000/docs`, UI — на `http://127.0.0.1:5173/`. Для ручной работы уберите `--check`.

## Что уже работает

- BMSTU fixture/live ingestion с provenance и fail-closed source selection.
- Изолированные модули universities, programs, curricula, disciplines, comparison, proftest и recommendations.
- SQLAlchemy/Alembic с FK, unique/check constraints и Decimal без float-конверсии.
- FastAPI/OpenAPI и сгенерированные TypeScript-типы.
- Выбор программ A/B, scope «всё обучение / семестр», блоки и состояния loading/empty/error.
- Профиль содержания: сценарные вопросы, anti-interest, adaptive refinement и TOP реальных программ с объяснениями по учебному плану.
- Recommendation vertical slice: готовый `UserProfile` → детерминированный Content Fit → reasons/anti-reasons по реальному fingerprint.

### Профиль содержания

В UI выберите «Профиль содержания». Flow получает вопросы и результаты только через `GET /proftest/questions`, `POST /proftest/preview` и `POST /proftest/results`. Готовый профиль также можно передать в `POST /recommendations`. После изменения API обновите frontend-контракт:

```powershell
python backend/scripts/export_openapi.py --out frontend/openapi.json
cd frontend
npm run generate-api
```

`Content Fit` рассчитывается детерминированно по реальным часам/ЗЕТ и долям предметных областей. `Workload readiness`, `Career Fit` и `Admission Fit` пока имеют статус `not_available` и не влияют на результат.

## Пример

```text
GET /compare?programIds=program:09.03.01-02,program:09.03.01-12&scope=semester&semester=1
```

Ответ содержит rows со статусами `both`, `different`, `only_a`, `only_b`, а также totals и blocks.

## Документация

| Гид | Содержание |
|---|---|
| [Быстрый старт](docs/getting-started.md) | Установка и первый запуск |
| [Архитектура](docs/architecture.md) | Модули и поток данных |
| [API](docs/api.md) | OpenAPI endpoints и контракты |
| [Конфигурация](docs/configuration.md) | Переменные окружения |
| [Тестирование](docs/testing.md) | Локальные и CI-проверки |

## Лицензия

Лицензия проекта не задана в текущем репозитории.
