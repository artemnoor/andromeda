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

После завершения профтеста application flow сохраняет финальный профиль через отдельный persistence port:

```text
POST /proftest/results
  → UserProfilePersistenceService
  → UserProfileRepository
  → user_profiles (session hash + JSON snapshot + revision/TTL)
  → GET /proftest/profile | GET /recommendations/current
```

Anonymous identity — это случайный HttpOnly cookie, а в domain/infrastructure boundary передаётся только typed `ProfileScope` с SHA-256 hash. `UserProfile` не содержит storage metadata; revision и timestamps находятся в `UserProfileSnapshot`. Admission Fit остаётся отдельным score и не влияет на Content Fit.

Auth identity follows the same boundary: `modules/auth` publishes typed `Account` and application ports; infrastructure stores Argon2 password hashes and opaque session-token hashes in `accounts`/`auth_sessions`. The API alone reads the raw HttpOnly cookie. `ProfileScope` may carry a canonical `AccountId` in addition to the anonymous session hash, so the existing proftest/recommendations/personal-route flows restore account-owned profiles without adding `account_id` to `UserProfile`. Binding is explicit and non-merging: account profile wins when both owners have a profile, while the anonymous row remains isolated.

Университетские события и campus points используют общий canonical venue boundary:

```text
events ingestion / campus ingestion
  → Event + Venue + CampusPoint canonical contracts
  → infrastructure repositories
  → /events и /campus/* FastAPI contracts
  → список/карточка события или физической точки
```

`campus` отдаёт map-agnostic spatial data: название и canonical ID точки, тип (корпус, зона, место события, вход или другая категория), адрес, известные координаты, university/department/program links, events в точке, время событий и поля карточки. Эти данные предназначены для UI и будущего внешнего map-модуля. Внутри Andromeda не задаются визуальная раскладка объектов, 2D/3D-визуализация, связи, маршруты, route optimizer или библиотека карт.

Ingestion quality для operator-инструментов использует существующий `ingest_runs` и отдельный read-only `admin_ops` module:

```text
ingestion lifecycle
  → ingest_runs (running → completed|failed + bounded counters)
  → admin_ops reader/service + typed retry executor port
  → protected GET /ops/ingestion/runs[/{id}] and POST /ops/ingestion/runs/retry
```

Run создаётся до capture и атомарной projection transaction, а failure обновляет только безопасный audit status и generic error message после rollback. `admin_ops` не читает raw snapshot bodies или `RawSourceRecord.payload_json`, не знает ORM/parser и получает retry через typed executor port. Infrastructure связывает этот port с существующим BMSTU adapter/repository; retry ограничен фиксированными профилями и не принимает URL/команды. `#ops` UI не является обычной навигацией и не реализует correction, CMS, Auth/RBAC, карту или пользовательское scoring.

## Границы

```text
backend/src/andromeda/
├── modules/{universities,programs,curricula,disciplines,comparison}/
├── modules/proftest/{domain,contracts,services,repository}/
├── modules/recommendations/{domain,contracts,services,repository}/
├── modules/admissions/{domain,contracts,services,repository}/
├── modules/admission_fit/{domain,contracts,services,repository}/
├── modules/events/{domain,contracts,services,repository}/
├── modules/campus/{domain,contracts,services,repository}/
├── modules/personal_route/{domain,contracts,services,repository}/
├── modules/admin_ops/{domain,contracts,services,repository}/
├── ingestion/universities/bmstu/
├── infrastructure/{database,repositories,config,logging}/
├── api/{routes,schemas,dependencies}/
└── composition/
```

Предметные модули публикуют `contracts.public` и Protocol-порты. Cross-module imports разрешены только через `modules/<module>/contracts/public.py` и typed `modules/<module>/repository/ports.py`; concrete domain/services/repository internals остаются закрытыми. `comparison` получает программы, curricula и disciplines через reader-контракты. SQLAlchemy-модели и `Session` остаются внутри infrastructure.

`proftest` использует те же публичные reader-контракты через собственный typed catalog port; его domain/services не знают об ORM, HTTP schemas или BMSTU parser. `ProgramFingerprint` и `UserProfile` остаются application contracts, а API routes только связывают их с HTTP.

`recommendations` получает только публичные `UserProfile` и `ProgramFingerprint`, а для каталога использует `RecommendationCatalogReader`. Его scoring policy фиксирует Content Fit как сумму subject, activity и distinctive fit с отдельным anti-interest penalty. `Career Fit`, `Admission Fit` и `Workload readiness` typed как `not_available` и не меняют score. Старые proftest matching/ranking/explanation paths остаются compatibility facades.

`admission_fit` — отдельный application/domain-модуль для оценки одного явно выбранного admission offering. Он публикует `ApplicantAdmissionProfile`, `AdmissionFitRequest` и `AdmissionFitResult`, а свой `AdmissionFitDataReader` получает snapshot через публичные `ProgramReader` и `AdmissionReader`. Внутри модуля нет SQLAlchemy, FastAPI, parser или recommendation imports:

```text
ProgramReader + AdmissionReader public contracts
  → AdmissionFitDataReader infrastructure adapter
  → AdmissionFitService
  → deterministic AdmissionFitScoringService
  → reasons / antiReasons / dataGaps + score/status
  → POST /programs/{id}/admission-fit
```

`Admission Fit` оценивает только реалистичность поступления по опубликованным admissions facts. Он не принимает `UserProfile`, `ProgramFingerprint` или Content Fit score и не вызывается из `RecommendationService`; поэтому его результат не меняет ranking рекомендаций.

`admissions` публикует `ProgramAdmissions`, offering и child contracts через `AdmissionReader`. Его service получает программу через `ProgramReader`, а не через ORM. Admission Fit в этот модуль не входит: slice только показывает source-backed факты поступления и сохраняет их provenance. Новые университеты подключают собственный ingestion adapter, не меняя этот application path.

`events` публикует event/venue contracts и фильтры для списков, карточек и recommendation-aware reads. `campus` публикует point contracts, point details, events-at-point и recommendation results; он не владеет картой и не вычисляет маршруты. Оба модуля используют canonical `UniversityId`, `DepartmentId`, `ProgramId` и `VenueId`, поэтому карта может запрашивать данные без дублирования university/program сущностей.

`personal_route` — тонкий application slice для текущего пользователя. Его public contracts описывают explainable logical steps, а Protocol-порты читают существующие recommendation/event/campus contracts. Composition wiring собирает `PersonalRouteService`; модуль не имеет ORM, миграций, ingestion, HTTP или map dependency. Он не хранит собственную сущность маршрута: каждый read заново строит plan из current profile, source-backed recommendations, будущих событий и связанных campus point details. `attend_event` может быть online и тогда не содержит venue/point; физическая близость, граф связей, directions и оптимизация маршрута намеренно остаются за будущим независимым map-модулем.

Старые пути `proftest.services.ranking`, `proftest.services.matching` и `proftest.services.explanations` сохранены как точечные compatibility facades. Они не являются разрешением импортировать recommendation internals в новый runtime-код и перечислены в architecture test как единственные переходные aliases.

BMSTU URL, catalog pagination, detail/API shape, public study-plan resolver, PDF parser, mappings и browser fallback находятся в BMSTU adapter. Live ingestion начинает с официального catalog API, обнаруживает все detail slugs/profiles и связывает curriculum/admissions по сохранённому source code и study-plan URL; ручной список программ не является production input. Добавление нового вуза должно создавать новый adapter без зависимости comparison от структуры сайта.

## Storage boundary

`BMSTU_DATABASE_URL` — единый target для FastAPI, Alembic и ingestion runner. `SqlAlchemy*Repository` и `SqlAlchemyIngestionRepository` — infrastructure adapters; модули видят только public contracts и repository ports. Поэтому PostgreSQL не меняет comparison/proftest/recommendations и не требует переписывать их scoring или fingerprint logic.

`user_profiles` хранит только сериализованный public `UserProfile` и nullable future `account_id`; raw session token, answers и ORM objects не являются публичными контрактами. LocalStorage во frontend используется только для незавершённого draft. Completed profile восстанавливается через API и cookie.

`ANDROMEDA_ENV=development` и `ANDROMEDA_ENV=staging` fail fast с non-PostgreSQL URL. `ANDROMEDA_ENV=test` сохраняет SQLite для быстрых тестов. Raw source snapshots остаются immutable provenance, а canonical domain projection обновляется атомарной ingestion sync-транзакцией.

## Identity дисциплин

Исходное `source_name` сохраняется на каждой позиции. Canonical normalization ограничивается Unicode, casefold и пробелами. Fuzzy-сопоставление и автоматическое объединение неоднозначных названий не используются.

## Таксономия дисциплин Andromeda

Каждая дисциплина получает не единственный ярлык, а нормализованный вектор `area_weights`: веса по 22 верхнеуровневым областям Andromeda. Веса строго положительны, не дублируют область и в сумме дают `1.0000`. Поэтому междисциплинарные предметы не теряют вторичную область: например, машинное обучение хранится как компьютерные науки + математика.

Для BMSTU явные сопоставления находятся в `ingestion/universities/bmstu/mappings/discipline_areas.py`. Это часть university-specific ingestion adapter, а не core comparison. На входе сохраняется исходное название, затем adapter применяет точное сопоставление по нормализованному имени; прозрачные keyword rules и универсальная область являются fallback только для новых или неизвестных предметов. В полном live audit все 2 582 обнаруженные дисциплины получили vector без `fallback_unclassified`; отсутствующая в каталоге 22-я область не подменяется искусственными предметами.

Распределение содержания программы считается в `comparison` по часам позиций учебного плана (при отсутствии часов используется ЗЕТ). Вектор предмета умножается на долю его нагрузки, после чего веса агрегируются по программе и выбранному семестру. Один предмет может влиять на несколько профилей, но исходная дисциплина и её workload остаются отдельной строкой сравнения.

## See Also

- [API](api.md) — HTTP-контракты для frontend.
- [Конфигурация](configuration.md) — database и logging settings.
- [PostgreSQL](postgresql.md) — запуск storage targets и migrations.
- [Тестирование](testing.md) — архитектурные и интеграционные gates.
