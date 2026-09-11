[← Быстрый старт](getting-started.md) · [Back to README](../README.md) · [API →](api.md)

# Архитектура

Проект остаётся modular monolith: один backend, одна инфраструктура и явные границы предметных модулей. Микросервисы, Kafka, CQRS и отдельный deployment-модуль в текущий scope не входят.

## Поток данных

```text
BMSTU source
  → ingestion/universities/bmstu
  → raw DTO → normalization → canonical contracts
  → universities / programs / curricula / disciplines
  → infrastructure repositories → PostgreSQL (development/staging) or SQLite (tests)
  → FastAPI/OpenAPI → TypeScript frontend
```

Для профиля содержания application flow продолжается так:

```text
programs / curricula / disciplines public readers
  → proftest catalog adapter
  → ProgramFingerprint
  → UserProfile
  → recommendations scoring/ranking/explanations
  → /proftest/preview|results или /recommendations
  → generated frontend types
```

## Границы

```text
backend/src/andromeda/
├── modules/{universities,programs,curricula,disciplines,comparison}/
├── modules/proftest/{domain,contracts,services,repository}/
├── modules/recommendations/{domain,contracts,services,repository}/
├── modules/admissions/{domain,contracts,services,repository}/
├── ingestion/universities/bmstu/
├── infrastructure/{database,repositories,config,logging}/
├── api/{routes,schemas,dependencies}/
└── composition/
```

Предметные модули публикуют `contracts.public` и Protocol-порты. `comparison` получает программы, curricula и disciplines через reader-контракты. SQLAlchemy-модели и `Session` остаются внутри infrastructure.

`proftest` использует те же публичные reader-контракты через собственный typed catalog port; его domain/services не знают об ORM, HTTP schemas или BMSTU parser. `ProgramFingerprint` и `UserProfile` остаются application contracts, а API routes только связывают их с HTTP.

`recommendations` получает только публичные `UserProfile` и `ProgramFingerprint`, а для каталога использует `RecommendationCatalogReader`. Его scoring policy фиксирует Content Fit как сумму subject, activity и distinctive fit с отдельным anti-interest penalty. `Career Fit`, `Admission Fit` и `Workload readiness` typed как `not_available` и не меняют score. Старые proftest matching/ranking/explanation paths остаются compatibility facades.

`admissions` публикует `ProgramAdmissions`, offering и child contracts через `AdmissionReader`. Его service получает программу через `ProgramReader`, а не через ORM. Admission Fit в этот модуль не входит: slice только показывает source-backed факты поступления и сохраняет их provenance. Новые университеты подключают собственный ingestion adapter, не меняя этот application path.

BMSTU URL, selectors, PDF parser, mappings и browser fallback находятся в BMSTU adapter. Добавление нового вуза должно создавать новый adapter без зависимости comparison от структуры сайта.

## Storage boundary

`BMSTU_DATABASE_URL` — единый target для FastAPI, Alembic и ingestion runner. `SqlAlchemy*Repository` и `SqlAlchemyIngestionRepository` — infrastructure adapters; модули видят только public contracts и repository ports. Поэтому PostgreSQL не меняет comparison/proftest/recommendations и не требует переписывать их scoring или fingerprint logic.

`ANDROMEDA_ENV=development` и `ANDROMEDA_ENV=staging` fail fast с non-PostgreSQL URL. `ANDROMEDA_ENV=test` сохраняет SQLite для быстрых тестов. Raw source snapshots остаются immutable provenance, а canonical domain projection обновляется атомарной ingestion sync-транзакцией.

## Identity дисциплин

Исходное `source_name` сохраняется на каждой позиции. Canonical normalization ограничивается Unicode, casefold и пробелами. Fuzzy-сопоставление и автоматическое объединение неоднозначных названий не используются.

## Таксономия дисциплин Andromeda

Каждая дисциплина получает не единственный ярлык, а нормализованный вектор `area_weights`: веса по 22 верхнеуровневым областям Andromeda. Веса строго положительны, не дублируют область и в сумме дают `1.0000`. Поэтому междисциплинарные предметы не теряют вторичную область: например, машинное обучение хранится как компьютерные науки + математика.

Для BMSTU явные сопоставления находятся в `ingestion/universities/bmstu/mappings/discipline_areas.py`. Это часть university-specific ingestion adapter, а не core comparison. На входе сохраняется исходное название, затем adapter применяет точное сопоставление по нормализованному имени; прозрачные keyword rules и универсальная область являются только fallback для новых или неизвестных предметов.

Распределение содержания программы считается в `comparison` по часам позиций учебного плана (при отсутствии часов используется ЗЕТ). Вектор предмета умножается на долю его нагрузки, после чего веса агрегируются по программе и выбранному семестру. Один предмет может влиять на несколько профилей, но исходная дисциплина и её workload остаются отдельной строкой сравнения.

## See Also

- [API](api.md) — HTTP-контракты для frontend.
- [Конфигурация](configuration.md) — database и logging settings.
- [PostgreSQL](postgresql.md) — запуск storage targets и migrations.
- [Тестирование](testing.md) — архитектурные и интеграционные gates.
