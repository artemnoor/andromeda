# Read-contract для Proftest Spike

Этот документ фиксирует boundary между отдельным Spike и текущим Andromeda
backend. В текущем scope Spike не открывает SQLite/PostgreSQL, не импортирует
ORM и не читает parser output.

## Используется сейчас

Spike вызывает текущий API по HTTP через свой `AndromedaApiClient`:

| Endpoint | Нужные поля |
| --- | --- |
| `GET /programs` | `id`, `directionId`, `code`, `name`, `educationYear`, `studyPlanUrl`, `sourceUrl` |
| `GET /programs/{id}/curriculum` | `program`, `curriculumId`, `educationYear`, `sourceUrl`, `capturedAt`, `items` |
| `GET /discipline-areas` | `code`, `name`, `description`, `position` |

Для каждой позиции curriculum используются:

- `discipline.id`, `name`, `normalizedName`, `primaryArea`;
- `discipline.areaWeights[]` — `code`, `name`, `description`, `weight`;
- `sourceName`, `semester`, `hours`, `credits`;
- `assessmentTypes`, `subjectGroup`, `sourcePosition`.

Входной `code` weighted area vector нормализуется на Spike boundary в поле
canonical DTO `area`. Исходное `sourceName` не заменяется нормализованным
названием и попадает в fingerprint evidence/distinctive subjects.

## Что уже достаточно для Spike

Текущий read path позволяет построить fingerprint из фактической нагрузки:

- hours используются как основная workload basis, credits — fallback;
- area shares, activity signals, subject groups и semester distribution считаются
  локально детерминированно;
- API не обязан заранее строить fingerprint и не становится coupled с Spike
  domain-моделями;
- admission/career/workload readiness данных нет, поэтому эти метрики в Spike
  имеют typed `status=not_available` и не влияют на Content Fit.

Fixture-каталог, использованный при проверке, содержит 2 программы, 89 и 123
curriculum positions, всего 212 позиций. Это рабочая проверка цепочки, но не
полный каталог МГТУ. По этой причине adaptive selector на реальном fixture
возвращает `skipped`, когда разброс кандидатов недостаточен.

## Минимальный контракт для следующего scope

После Spike можно добавить versioned read-only fingerprint endpoint:

```text
GET /program-fingerprints?programIds=...
GET /programs/{id}/fingerprint
```

Предпочтительно поддержать bulk-вариант с pagination/filtering. Ответ должен
быть отдельным публичным DTO, а не ORM-моделью:

```json
{
  "programId": "program:...",
  "programCode": "...",
  "programName": "...",
  "basis": "hours",
  "totalHours": 0,
  "totalCredits": "0.0000",
  "totalWorkload": "0.0000",
  "areaShare": {},
  "subjectGroupShare": {},
  "semesterDistribution": {},
  "activitySignals": {},
  "distinctiveSubjects": [],
  "sourceCoverage": {
    "curriculumItems": 0,
    "capturedAt": "2026-01-01T00:00:00Z"
  },
  "calculatedAt": "2026-01-01T00:00:00Z"
}
```

Обязательны schema version, strict field policy, `sourceCoverage` и
`calculatedAt`. Это устранит N+1 запросов при полном каталоге, но endpoint не
реализуется в основном Andromeda в рамках текущего Spike.
