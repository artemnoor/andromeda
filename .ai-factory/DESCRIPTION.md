# Andromeda: описание проекта

## Идентичность и цель

Andromeda — source-backed modular monolith для работы с образовательными программами и университетскими данными. Текущий основной контекст — BMSTU: canonical university/program/discipline data проходит через ingestion и доступен через typed application contracts, FastAPI/OpenAPI и frontend.

Проект помогает пользователю сравнивать реальные учебные планы, проходить профтест, получать объяснимые рекомендации и просматривать факты поступления. Университетские события и campus spatial data предоставляются как данные для UI и будущих внешних клиентов; сама карта и маршрутизация не входят в текущую систему.

## Текущий BMSTU scope

- BMSTU fixture/live ingestion с dynamic catalog discovery, provenance, нормализацией и canonical IDs; live source gaps сохраняются явно.
- Учебные планы, программы, curricula и дисциплины с workload, семестрами, формами контроля и taxonomy areas.
- Профиль содержания пользователя (`UserProfile`), Content Fit и рекомендации по реальным fingerprints.
- Source-backed admissions facts и отдельный Admission Fit для явно выбранной программы.
- Университетские events с venue/address/optional coordinates, временем, ссылкой регистрации и canonical links.
- Campus points (корпуса, зоны, места событий, входы и другие физические точки) с карточкой точки и связанными events.

## Functional modules

Каждый subject module организован вокруг `domain`, `contracts`, `services` и `repository`; внешние зависимости входят через public contracts/typed ports.

- `universities` — canonical universities, departments/directions и university readers.
- `programs` — canonical educational programs.
- `curricula` — учебные планы и curriculum items.
- `disciplines` — дисциплины, identity resolution и areas taxonomy.
- `comparison` — сравнение программ целиком или по семестру.
- `proftest` — questionnaire, UserProfile, fingerprint и profile persistence contracts.
- `recommendations` — Content Fit scoring, ranking и evidence-backed explanations.
- `admissions` — опубликованные admission offerings, exams, quotas, passing scores, tuition и provenance.
- `admission_fit` — независимая оценка реалистичности поступления по admissions facts.
- `events` — typed university event data, filtering и registration metadata.
- `campus` — typed physical points и map-agnostic point/event read contracts.

## Основные product flows

```text
BMSTU source
  → ingestion/universities/bmstu
  → raw DTO → normalization → canonical contracts
  → university/program/curriculum/discipline repositories
  → FastAPI/OpenAPI → TypeScript frontend
```

```text
questionnaire → UserProfile → ProgramFingerprint
  → recommendations Content Fit → reasons/ranking → profile/recommendations API
```

```text
admissions facts → Admission Fit request for one program
  → independent score/status/reasons/data gaps
```

```text
events + campus points → API contracts
  → event list/cards, filters, point details and future external map module
```

`Content Fit`, `Admission Fit`, `Career Fit` и `Workload Readiness` — разные dimensions. `Admission Fit` не меняет Content Fit или ranking recommendations.

## Техническая форма

Backend: Python 3.11+, FastAPI, Pydantic, SQLAlchemy и Alembic. PostgreSQL — development/staging target; SQLite остаётся test fallback. SQLAlchemy models/session и concrete repository adapters находятся в `andromeda.infrastructure`. API routes связывают transport schemas с application services; business logic остаётся в subject modules.

Новые университеты подключаются отдельным adapter в `ingestion/universities/<university>` и не требуют копирования BMSTU parser в core modules. Public contracts используют canonical typed IDs из `andromeda.shared.contracts.ids`; `UserProfile` является typed contract и не содержит storage metadata.

## Направление multi-university

BMSTU — первый adapter и fixture. Следующий университет должен получить свой source parser/mappings/normalizers в собственном `ingestion/universities/<university>` namespace, сохраняя общие canonical contracts и application flows. Университетская специфика не должна просачиваться в comparison, recommendations, admissions или API.

## Out of scope

Не являются частью текущего Andromeda scope: Personal Route, microservices, Kafka, CQRS, отдельный deployment для модулей, интерактивная 2D/3D-карта, визуальное размещение объектов и маршрутизация/route optimizer.
