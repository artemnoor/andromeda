# Implementation Plan: Contract-First BMSTU Tracer Bullet

Branch: none (Git-aware workflow unavailable; current `.git` directory is not recognized as a Git worktree)
Created: 2026-09-10

## Original Request

Перепроектируй текущий spike как один contract-first Tracer Bullet:

источник → parser → domain → database → API → frontend

Цель — не просто провести данные end-to-end, а сделать строгие и явно проверяемые контракты между всеми слоями.

Требования:

1. DOMAIN CONTRACTS

Для каждой доменной сущности должен существовать явный контракт.

Например:

- University
- Faculty
- Department
- Direction
- EducationalProgram
- Curriculum
- Discipline

Для каждого поля определить:

- имя;
- тип;
- обязательность;
- nullable / non-nullable;
- допустимые значения;
- enum, где это возможно;
- ограничения длины;
- числовые ограничения;
- формат;
- идентификаторы и связи;
- уникальность;
- semantic constraints.

Контракты должны быть централизованы и не дублироваться независимо в parser/API/frontend.

2. RUNTIME VALIDATION

Недостаточно только статической типизации.

Все данные на границах системы должны проходить runtime validation:

source/parser
→ normalized domain data

API request
→ service

service
→ API response

Если данные не соответствуют контракту, система должна возвращать понятную структурированную ошибку.

Нельзя silently исправлять или пропускать некорректные данные.

3. PARSER CONTRACT

Parser не должен напрямую создавать произвольные словари/JSON.

После получения данных из источника:

raw data
→ parser
→ DTO/schema validation
→ normalized domain entity

Отдельно сохранить различие между:

- raw source data;
- normalized data;
- domain entity.

4. DATABASE CONTRACT

Схема БД должна поддерживать ограничения доменной модели:

- NOT NULL;
- FOREIGN KEY;
- UNIQUE;
- CHECK;
- enum/reference tables;
- корректные типы данных.

Не полагаться только на application-level validation.

5. API CONTRACT

Каждый публичный endpoint должен иметь формальный контракт.

Для первого Tracer Bullet достаточно небольшого API, например:

GET /programs/{id}

GET /programs/{id}/curriculum

GET /compare?programIds=id1,id2

Для каждого endpoint определить:

- request schema;
- path/query params;
- response schema;
- error schema;
- HTTP status codes.

6. OPENAPI

OpenAPI specification является обязательной частью проекта.

Должен автоматически подниматься Swagger UI или аналогичный интерфейс, где можно:

- увидеть все endpoints;
- посмотреть request/response schemas;
- увидеть domain DTO;
- посмотреть enums;
- выполнить запрос;
- увидеть validation errors.

Например:

/docs
/openapi.json

OpenAPI должен генерироваться из тех же контрактов, которые реально используются приложением, либо автоматически проверяться на соответствие им.

Нельзя поддерживать документацию вручную отдельно от кода.

7. STRICT TYPING

Включить максимально строгую типизацию в используемом стеке.

Не использовать:

- any;
- Dict[str, Any];
- untyped JSON objects;
- magic strings для enum;
- необъявленные nullable значения

без объективной необходимости.

8. FRONTEND CONTRACT

Frontend не должен вручную предполагать структуру API.

Typed API client должен генерироваться или выводиться из OpenAPI/schema.

Желаемый поток:

domain/backend schemas
→ OpenAPI
→ generated frontend types/client
→ frontend

Если API-контракт изменяется, frontend должен получать type/build error, а не runtime-баг.

9. CONTRACT TESTS

Добавить проверки контрактов.

Минимально:

parser output соответствует domain schema;

domain model соответствует DB constraints;

API responses соответствуют OpenAPI schema;

frontend client соответствует актуальной OpenAPI specification.

Добавить тест, который прогоняет реальный минимальный объект через:

parser
→ validation
→ DB
→ API
→ frontend-compatible DTO.

10. ERROR CONTRACT

Создать единый формат ошибок API.

Например:

{
"code": "VALIDATION\_ERROR",
"message": "...",
"details": [...]
}

Ошибки также должны быть описаны в OpenAPI.

11. TRACER BULLET SCOPE

Не пытайся сразу реализовать все сущности Andromeda.

Для первого Tracer Bullet возьми:

University
Direction
EducationalProgram
Discipline

и минимальные поля, необходимые для сценария:

реальный источник
→ две программы
→ их дисциплины
→ часы/семестры
→ БД
→ API compare
→ экран сравнения.

При этом архитектура контрактов должна позволять потом добавлять остальные доменные сущности без переписывания существующего pipeline.

12. DELIVERABLE

В конце должно быть возможно:

1. открыть Swagger UI;
2. посмотреть контракты сущностей;
3. выполнить API-запрос;
4. увидеть строго типизированный ответ;
5. открыть frontend;
6. увидеть те же реальные данные;
7. изменить контракт сущности и получить ошибку validation/typecheck/test там, где система перестала ему соответствовать.

Перестрой текущий план вокруг этого вертикального сценария.

Не создавай отдельные большие этапы:
"сначала вся БД",
"потом весь API",
"потом весь frontend".

Каждая задача должна двигать один end-to-end Tracer Bullet.

## Settings

- Testing: yes
- Logging: standard
- Docs: yes
- Artifact language: English (default; `Original Request` is preserved verbatim)

## Current Evidence and Scope Boundary

The repository currently implements `HTTP/Playwright -> Python CLI -> JSON/JSONL files -> inline HTML`, not a contract-first application:

- `backend/src/bmstu_parser/models.py` uses dataclasses and broad `dict[str, Any]` records.
- `backend/src/bmstu_parser/pipeline.py` writes `records.jsonl`, `profile.json`, `hierarchy.json`, and browser assets but has no database or service boundary.
- `backend/src/bmstu_parser/adapters/bmstu.py` contains useful S06 and PDF parsing logic, but its public extraction surface is untyped dictionaries.
- `backend/src/bmstu_parser/profile.py` turns heterogeneous records into a large unvalidated profile.
- `bmstu-dashboard.html` embeds `BMSTU_PROFILE` and compares `study_plans` locally; it has no API client or build/typecheck step.
- `backend/pyproject.toml` has no FastAPI, Pydantic, SQLAlchemy, Alembic, or frontend tooling. `.github/workflows` is empty.

The current output provides a realistic baseline: `output/bmstu-priority-2026-09-08-v9-reference-parser/profile.json` contains 136 programs and 6,998 study-plan rows, but the selected output is a rebuild artifact with missing run-side JSONL files and cannot be treated as a database contract.

The tracer uses two programs that are present with curriculum rows in that baseline and are expected to be rediscovered from the official source at ingest time:

- `program:09.03.01-02` / source code `09.03.01-02` — "Интеллектуальные системы обработки информации и управления";
- `program:09.03.01-12` / source code `09.03.01-12` — "Искусственный интеллект в системах обработки информации и управления";
- both belong to direction `09.03.01` — "Информатика и вычислительная техника";
- the current baseline has 213 and 123 curriculum rows respectively.

The new tracer path is isolated under `contracts/`, `tracer/`, `db/`, `api/`, and `frontend/`. The legacy broad-record pipeline remains available for out-of-scope Andromeda blocks, but no new tracer/API code may import its untyped `parse_source`, `build_profile`, or browser-asset output as a contract. Existing `Any` usages outside the tracer boundary are a documented compatibility surface; the strict type gate applies to all new tracer, API, DB repository, and frontend code.

## Target Architecture and Data Flow

```text
official BMSTU S01 + S06 catalog/API + linked curriculum PDFs
        |
        v
RawSourceSnapshot + typed Raw* DTOs (immutable bytes, URL, hash, provenance)
        |
        v
typed parser -> explicit normalization -> University/Direction/
EducationalProgram/Discipline/Curriculum domain entities
        |
        v
one transaction: source_snapshots/raw_source_records + domain tables
        |
        v
typed repositories -> service -> runtime-validated API response models
        |
        v
FastAPI /openapi.json -> generated TypeScript types/client -> frontend compare screen
```

The source adapter must use the existing official source facts, not the committed `profile.json` as a source of truth:

- university facts: `https://bmstu.ru/sveden/common/` (source-map `S01`);
- direction/program catalog: `https://bmstu.ru/bachelor/majors` and the existing BMSTU API URL in `pipeline.py` (`S06`);
- curriculum documents: the study-plan URLs returned by the official S06 detail data, including the current baseline URLs for the two target programs.

The allowlist for follow-up URLs is restricted to the official BMSTU hosts and the document hosts already used by S06 (`disk.yandex.ru` and its documented download endpoints). A changed/missing/ambiguous target program or malformed selected document is a contract failure, not an empty result.

## Central Contract Design

### Shared primitives and enums

All constraints below are declared once in `backend/src/bmstu_parser/contracts/constraints.py` and consumed by Pydantic models, parser normalization, DB metadata/migration assertions, and OpenAPI-generated frontend types.

| Contract | Type and constraints |
|---|---|
| `NonEmptyText` | strict `str`; trim outer whitespace, then length 1..512; blank values are invalid |
| `ShortText` | strict `str`; length 1..128 |
| `UniversityId` | strict `str`; pattern `^university:[a-z0-9][a-z0-9-]{0,62}$` |
| `DirectionId` | strict `str`; pattern `^direction:[0-9]{2}\.[0-9]{2}\.[0-9]{2}$` |
| `ProgramId` | strict `str`; pattern `^program:[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}$` |
| `CurriculumId` | strict `str`; stable value `curriculum:{program-code}-{education-year}` |
| `DisciplineId` | strict `str`; pattern `^discipline:[a-f0-9]{16}$`; derived from the first 16 hexadecimal characters of SHA-256 of `normalized_name` |
| `DirectionCode` | strict `str`; pattern `^[0-9]{2}\.[0-9]{2}\.[0-9]{2}$` |
| `ProgramCode` | strict `str`; pattern `^[0-9]{2}\.[0-9]{2}\.[0-9]{2}-[0-9]{2,3}$`; ASCII `-` only after explicit normalization |
| `EducationLevel` | enum: `bachelor`, `specialist`, `master`, `postgraduate` |
| `AssessmentType` | enum: `exam`, `credit`, `graded_credit`, `coursework`, `course_project`, `state_exam` |
| `SourceKind` | enum: `bmstu_common`, `bmstu_major_catalog`, `bmstu_curriculum_document` |
| `CompareStatus` | enum: `both`, `only_a`, `only_b`, `different` |
| `ErrorCode` | enum: `VALIDATION_ERROR`, `NOT_FOUND`, `SOURCE_CONTRACT_ERROR`, `CONTRACT_ERROR`, `INTERNAL_ERROR` |
| `education_year` | strict integer, inclusive range 2000..2100 |
| `semester` | strict integer, inclusive range 1..12 |
| `hours` | strict integer, inclusive range 0..2,000 per curriculum item |
| `credits` | strict `Decimal` or explicitly nullable; range 0..60, at most 2 fractional digits |
| `HttpUrl` | absolute `https://` URL; source-specific host allowlist applies to follow-ups |
| `Sha256` | strict lowercase hexadecimal string of exactly 64 characters |

Public JSON uses camelCase aliases (`universityId`, `studyPlanUrl`, `programIds`), while Python and SQL identifiers remain snake_case. Aliases are defined on the same Pydantic models that generate OpenAPI; the frontend never re-declares them.

### Domain entities

Every field is required unless explicitly marked nullable below. All models use Pydantic v2 `ConfigDict(strict=True, extra="forbid")`; arbitrary extra keys, implicit coercion, and undeclared nulls are rejected.

| Entity | Fields and rules |
|---|---|
| `University` | `id: UniversityId` required/non-null; `name: NonEmptyText` required/non-null, max 512; `city: ShortText` required/non-null, max 128; `official_site: HttpUrl` required/non-null; `address: NonEmptyText` required/non-null, max 512. `id` is stable for the source institution; `official_site` must be `https://bmstu.ru/` for this slice. |
| `Direction` | `id: DirectionId`; `university_id: UniversityId`; `code: DirectionCode`; `name: NonEmptyText`; `education_level: EducationLevel`. All required/non-null. Unique `(university_id, code)`; `id` must equal `direction:{code}`; direction code in `id` and `code` must agree; `university_id` must resolve to `University`. |
| `EducationalProgram` | `id: ProgramId`; `direction_id: DirectionId`; `code: ProgramCode`; `name: NonEmptyText`; `education_year: int` 2000..2100; `study_plan_url: HttpUrl`; `source_url: HttpUrl`. All required/non-null. Unique `(direction_id, code)`; code prefix must equal parent `Direction.code`; `id` must equal `program:{code}`; curriculum source URL must be the URL discovered for this exact program. |
| `Discipline` | `id: DisciplineId`; `name: NonEmptyText` max 256; `normalized_name: ShortText` max 256. All required/non-null. `normalized_name` is deterministic Unicode NFKC/casefold/whitespace normalization and is not a replacement for the raw display name; unique within the database. `id` must be derived from `normalized_name`, so equivalent source spellings cannot create duplicate disciplines. |
| `Curriculum` | `id: CurriculumId`; `program_id: ProgramId`; `education_year: int`; `source_url: HttpUrl`; `captured_at: datetime` timezone-aware; `items: non-empty tuple[CurriculumItem, ...]`. All required/non-null. Unique `(program_id, education_year)`; `id` must match program/year; every item belongs to the same curriculum and the program must exist. |
| `CurriculumItem` | `id: strict str` stable per curriculum/discipline/semester assignment; `discipline_id: DisciplineId`; `semester: int | None` 1..12 when the source assigns a semester, otherwise explicitly null; `hours: int` 0..2,000; `credits: Decimal | None`; `assessment_types: tuple[AssessmentType, ...] | None`; `subject_group: ShortText | None`; `source_position: int | None` 1..10,000. `id`, discipline, and hours are required/non-null; semester is nullable only for source rows whose workload is not assigned to a semester; only credits, assessment types, subject group, source position, and semester may be null. Unique `(curriculum_id, discipline_id, semester)`; source position is ordering/provenance and is not globally unique because the same discipline row legitimately spans multiple semesters. `credits` cannot be negative; assessment types are nullable only when the source cell is genuinely empty. |
| `SourceAttribution` | `kind: SourceKind`; `url: HttpUrl`; `captured_at: datetime`; `content_sha256: Sha256`; all required/non-null. It is the domain provenance boundary and never contains raw arbitrary payload. |

Semantic normalization is deliberately narrow: Unicode/whitespace normalization and the source's documented en-dash/em-dash/slash-to-ASCII-hyphen code notation are allowed only while retaining the original raw value and recording the transformation. The raw assessment mapping is explicit: `Экз`/`РЭкз` -> `exam`, `Зчт` -> `credit`, `ДЗчт` -> `graded_credit`, `КуР` -> `coursework`, `КуП` -> `course_project`, `ГЭК` -> `state_exam`, and `Экз КуР` -> `(exam, coursework)`. Any other non-empty assessment mark is a contract failure. Missing fields, unknown enums, invalid codes, duplicate identity, and malformed numeric cells raise `SOURCE_CONTRACT_ERROR` with field/path details; they are not skipped or silently repaired. Exact duplicate PDF rows may be collapsed only when the source locator and all normalized values match; the collapse is recorded in provenance and logged as a parser event.

### Raw and normalized DTOs

`backend/src/bmstu_parser/contracts/raw.py` defines a recursive `JsonValue`/`JsonObject` type for the objectively dynamic raw payload boundary only. `RawSourceSnapshot` stores the exact response bytes, requested/final URL, status, content type, capture time, SHA-256, and immutable file path. `RawUniversityRecord`, `RawDirectionRecord`, `RawProgramRecord`, and `RawCurriculumRow` are Pydantic DTOs with source-shaped scalar fields and a `SourceLocator` (page/table/row when available).

`backend/src/bmstu_parser/contracts/normalized.py` defines typed normalized records with no `JsonValue`, raw HTML, source-specific aliases, or free-form dictionaries. The parser returns `NormalizedTracerSnapshot`, which contains typed normalized entities and the `SourceAttribution`; the ingest service constructs domain aggregates from it. This gives the code and tests three visibly distinct types:

`RawSourceSnapshot / Raw* DTO -> Normalized* -> domain entity`.

### Unified API error

`ErrorResponse` is the only public error shape:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [
    {"path": "programIds", "message": "Exactly two distinct program ids are required", "type": "value_error"}
  ]
}
```

`details` is always a list (possibly empty) of typed `ErrorDetail` objects. The API adapter converts FastAPI/Pydantic errors, `NotFound`, parser contract failures, and response-validation failures into this shape. Values are sanitized strings; raw HTML, source bodies, credentials, and stack traces never enter the response.

## API and OpenAPI Contract

| Endpoint | Request contract | Success | Errors/statuses |
|---|---|---|---|
| `GET /programs/{id}` | path `id: ProgramId`; no body | `200 ProgramResponse` | `404 NOT_FOUND`, `422 VALIDATION_ERROR`, `500 CONTRACT_ERROR` |
| `GET /programs/{id}/curriculum` | path `id: ProgramId`; no body | `200 CurriculumResponse` | `404 NOT_FOUND`, `422 VALIDATION_ERROR`, `500 CONTRACT_ERROR` |
| `GET /compare?programIds=id1,id2` | required CSV query parameter `programIds`; exactly two distinct `ProgramId` values after schema validation | `200 CompareResponse` | `404 NOT_FOUND` if either program/curriculum is absent, `422 VALIDATION_ERROR` for malformed/duplicate/count errors, `500 CONTRACT_ERROR` |

The field-level API schemas are part of the central registry in `backend/src/bmstu_parser/contracts/api.py` and use the same Pydantic models that generate OpenAPI:

| Schema | Required public fields and semantics |
|---|---|
| `UniversityResponse` | `id`, `name`, `city`, `officialSite`, `address` |
| `DirectionResponse` | `id`, `universityId`, `code`, `name`, `educationLevel` |
| `ProgramSummaryResponse` | `id`, `directionId`, `code`, `name`, `educationYear`, `studyPlanUrl`, `sourceUrl` |
| `ProgramResponse` | `university: UniversityResponse`, `direction: DirectionResponse`, `program: ProgramSummaryResponse`, `source: SourceAttributionResponse` |
| `DisciplineResponse` | `id`, `name`, `normalizedName` |
| `CurriculumItemResponse` | `id`, `discipline: DisciplineResponse`, nullable `semester`, `hours`, nullable `credits`, nullable `assessmentTypes`, nullable `subjectGroup`, nullable `sourcePosition` |
| `CurriculumResponse` | `program: ProgramSummaryResponse`, `curriculum: CurriculumMetadataResponse`, `items: CurriculumItemResponse[]`, `source: SourceAttributionResponse` |
| `WorkloadResponse` | nullable `semester`, `hours`, nullable `credits`, nullable `assessmentTypes`, nullable `subjectGroup` |
| `CompareRowResponse` | `discipline: DisciplineResponse`, `semester`, nullable `a: WorkloadResponse`, nullable `b: WorkloadResponse`, `status: CompareStatus` |
| `CompareResponse` | `programA: ProgramSummaryResponse`, `programB: ProgramSummaryResponse`, `rows: CompareRowResponse[]`, `sources: SourceAttributionResponse[]` |

`programIds` is represented as a CSV string on the wire and as a validated fixed-size tuple in the service. Compare rows align by `discipline.normalizedName` plus nullable semester; a null semester is a real unassigned-source value, not a fabricated number. `both` means both sides exist and all declared workload fields match; `only_a`/`only_b` means presence on one side only; `different` means both exist but at least one declared workload field differs. Rows are sorted by normalized discipline name, then numbered semester with null semesters last. `assessmentTypes` is a sorted enum array so composite source marks remain lossless.

`ErrorResponse` is the only public error shape for `422`, `404`, and `500` responses. FastAPI sets every model as `response_model`; the service validates its own return value before handing it to FastAPI. A response that cannot be validated is handled through `ResponseValidationError` as a structured `500 CONTRACT_ERROR`, never a partially serialized object.

OpenAPI is generated by the FastAPI application at `/openapi.json`; Swagger UI is available at `/docs`. A deterministic export command writes the same generated document for frontend generation and contract tests. No hand-maintained endpoint/schema documentation is allowed. Local frontend access is made executable through either exact-origin CORS (`VITE_FRONTEND_ORIGIN`) or a tested Vite proxy; the chosen mechanism is part of the first vertical slice and is covered by an integration check.

## Database Contract

Use SQLAlchemy 2 typed `Mapped[...]` models plus Alembic, with SQLite as the local/integration database and a PostgreSQL-compatible schema target. The migration must create:

- `ingest_runs` and `source_snapshots` for run/provenance metadata;
- `raw_source_records` with typed metadata, SHA-256, and a JSON column validated as `JsonObject` before storage; it is never read as a domain object;
- `universities`, `directions`, `educational_programs`, `disciplines`, `curricula`, and `curriculum_items` for normalized domain data;
- reference tables `education_levels` and `assessment_types` seeded with the declared enum values.

Required DB constraints:

- `NOT NULL` on every non-nullable domain field;
- `FOREIGN KEY` links university -> direction -> program -> curriculum -> item and item -> discipline;
- `UNIQUE` on university identity, `(university_id, direction.code)`, `(direction_id, program.code)`, `discipline.normalized_name`, `(program_id, education_year)`, and `(curriculum_id, discipline_id, semester)`; source position is explicitly not unique;
- `CHECK` constraints for non-empty text, canonical code shape/prefix, education year, nullable semester, hours, credits, and non-negative source positions. SQLite-compatible `length`/`GLOB` checks or registered deterministic functions are used instead of assuming a native SQLite regex operator; PostgreSQL migrations use equivalent checks;
- foreign keys to enum/reference tables rather than unchecked magic strings;
- decimal/numeric storage for credits and integer storage for hours/semester/year;
- indexes on program code and curriculum item lookup by curriculum/semester.

The aggregate invariant `Curriculum.items` must be non-empty cannot be expressed portably as a row-level `CHECK`; the ingest transaction explicitly verifies at least one child item before commit, and the integration test proves an empty curriculum is rolled back and never becomes visible. Semester-less workload rows are retained with explicit `semester: null`; the compare contract sorts them after numbered semesters and never invents a semester.

The migration is an independent enforcement layer, not a substitute for runtime validation. `contracts/constraints.py` supplies the limits used to build/check both layers, and `tests/contracts/test_db_constraints.py` directly attempts invalid inserts to prove SQLite rejects them. Ingest uses one transaction: any invalid selected raw DTO, normalization error, identity conflict, foreign-key failure, or DB constraint failure rolls back the entire tracer snapshot; no partial two-program dataset is exposed.

## Tasks

The plan is intentionally organized as five vertical increments. There is no separate “all backend”, “all database”, “all API”, or “all frontend” phase. Every increment extends the same executable path from source to a user-visible result.

- [x] **Task 1: Vertical Increment A — one real BMSTU program from source to the first frontend result** (files: `backend/src/bmstu_parser/contracts/{__init__.py,constraints.py,primitives.py,enums.py,raw.py,normalized.py,domain.py,api.py,errors.py}`, `backend/src/bmstu_parser/tracer/{__init__.py,source.py,parser.py,normalizer.py,ingest.py}`, `backend/src/bmstu_parser/db/{base.py,session.py,models.py,repositories.py}`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_tracer_bullet.py`, `backend/src/bmstu_parser/api/{main.py,dependencies.py,error_handlers.py}`, `backend/src/bmstu_parser/api/routes/programs.py`, `backend/src/bmstu_parser/api/services/program_service.py`, `frontend/{package.json,package-lock.json,tsconfig.json,vite.config.ts,index.html}`, `frontend/src/{api/generated.ts,api/client.ts,api/errors.ts,features/program/ProgramScreen.ts,main.ts}`, `backend/tests/vertical/test_increment_1.py`, `backend/tests/fixtures/tracer/raw/09.03.01-02/`, `backend/scripts/run_tracer_bullet.py`; dependency: none)

  Deliverable: build the smallest useful contract registry for `University`, `Direction`, `EducationalProgram`, `Discipline`, `Curriculum`, `CurriculumItem`, `SourceAttribution`, the API DTOs, and `ErrorResponse`. Use strict Pydantic v2 models, explicit nullability, public aliases, enums, and semantic validators. Capture the official S01 university page, the official S06 catalog/detail data, and the linked study-plan document for `09.03.01-02`; store exact raw bytes and `source_manifest.json` with public URL, final URL, status, capture time, SHA-256, and target code. Reuse existing BMSTU PDF extraction only behind typed adapters; do not call legacy generic `parse_source` or read `profile.json` as input. Run `Raw* DTO -> normalized snapshot -> domain aggregate -> one SQLite/Alembic transaction`, including at least one real curriculum item. Expose `GET /programs/{id}`, `/docs`, and `/openapi.json`, and generate the first TypeScript client from that live OpenAPI document. Create a minimal frontend screen that calls the endpoint and renders the real program name, direction, education year, and source link from the API. Add exact-origin CORS or a tested Vite proxy so the browser request succeeds.

  First demonstration: after this task, the documented `tracer-bullet demo --program-id program:09.03.01-02` preparation command plus the API/frontend start commands show a real program card in the browser, with the data proven to have come from the database rather than inline `BMSTU_PROFILE`.

  Verification: the vertical test runs the captured official source through raw DTO validation, normalization, domain validation, migration, ingest, `TestClient`, OpenAPI response validation, and generated-client compilation. It also proves that a missing target plan or malformed selected field stops ingestion with a structured contract error and non-zero exit status.

  Logging requirements: use `contracts.validation` DEBUG/WARN events for boundary and rejected-path metadata; use `tracer.source.fetch` INFO for source kind, URL host/path, status, byte count, hash, and duration; use `tracer.ingest` INFO for run id, transaction start/commit, item counts, and hashes; use `api.request` DEBUG for route template and correlation id; use the frontend logger DEBUG/WARN for request lifecycle and sanitized API errors. Never log raw bodies, signed URLs, response payloads, or personal data. Honor `LOG_LEVEL`.

- [x] **Task 2: Vertical Increment B — add the second real program and curriculum data through the same path** (files: `backend/src/bmstu_parser/tracer/{source.py,parser.py,normalizer.py}`, `backend/src/bmstu_parser/contracts/{raw.py,normalized.py,domain.py,api.py}`, `backend/src/bmstu_parser/api/routes/programs.py`, `backend/src/bmstu_parser/api/services/program_service.py`, `backend/src/bmstu_parser/db/repositories.py`, `frontend/src/{api/generated.ts,api/client.ts,features/curriculum/CurriculumScreen.ts,main.ts}`, `backend/tests/vertical/test_increment_2.py`, `backend/tests/fixtures/tracer/raw/09.03.01-12/`, `frontend/scripts/generate-api.mjs`; dependency: Task 1)

  Deliverable: extend the existing contracts and adapter, without creating a second schema family, to rediscover exactly `09.03.01-12` from the live S06 catalog/detail chain and its linked official study-plan document. Preserve the raw en-dash code and normalize it to ASCII hyphen only in the normalized/domain layer. Normalize the observed assessment marks with the declared mapping, including composite `Экз КуР`, and fail on any unknown non-empty mark. Preserve legitimate source rows without an assigned semester as explicit `semester: null`; never invent or silently discard a semester. Ingest both programs and their non-empty curricula atomically, expose `GET /programs/{id}/curriculum`, and regenerate the client from the running backend OpenAPI. Extend the frontend to load both program curriculum responses and render the actual discipline, nullable semester, hours, credits, and assessment values returned by the API. Keep the first screen working while adding this second route.

  Demonstration: the browser shows curriculum rows for both real target programs; the API response contains only rows persisted by the new database path, and the source manifest links each curriculum to its public official document URL and content hash.

  Verification: test the exact target-selection chain, raw/normalized distinction, composite assessment mapping, non-empty curriculum invariant, idempotent replay, and a negative case where one selected document is absent or ambiguous. Assert at least one known discipline/semester/hour sample from each captured document while avoiding live-network-dependent row-count assumptions.

  Logging requirements: retain the Task 1 boundary loggers; add `tracer.source.select` DEBUG for candidate counts and selected source locators, ERROR for missing/ambiguous targets, and `api.curriculum` INFO for program id and item count. Log normalization transformations as field names and source locators only, never raw values or signed download URLs.

- [x] **Task 3: Vertical Increment C — compare API and side-by-side comparison screen** (files: `backend/src/bmstu_parser/contracts/{api.py,enums.py,errors.py}`, `backend/src/bmstu_parser/api/{error_handlers.py}`, `backend/src/bmstu_parser/api/routes/compare.py`, `backend/src/bmstu_parser/api/services/compare_service.py`, `backend/tests/vertical/test_increment_3.py`, `backend/tests/api/test_compare_contract.py`, `frontend/src/{api/generated.ts,api/client.ts,api/errors.ts,features/compare/CompareScreen.ts,main.ts}`, `frontend/scripts/generate-api.mjs`; dependency: Task 2)

  Deliverable: implement `GET /compare?programIds=id1,id2` over the persisted curriculum rows. Validate the CSV query as exactly two distinct `ProgramId` values, load both sides through typed repositories, align by `normalizedName + semester`, preserve nullable workload values and composite assessment types, compute only the declared `CompareStatus` values, and sort deterministically. Validate `CompareResponse` before serialization. Regenerate the TypeScript client from the changed OpenAPI document and replace the temporary curriculum view with a comparison screen that renders `programA`, `programB`, and every typed comparison row. Add explicit loading, empty, not-found, and structured validation-error states. Do not make the legacy dashboard a dependency or a second contract.

  Demonstration: selecting the two configured target ids opens a side-by-side table in the browser whose program names, disciplines, semesters, hours, credits, and assessments exactly match `GET /compare` and the database-backed curriculum responses.

  Verification: test a valid comparison, one-sided discipline, differing workload, matching workload, malformed ids, duplicate ids, wrong cardinality, and missing program/curriculum. Assert deterministic JSON ordering and exact OpenAPI `$ref`/required/enum definitions for the compare response.

  Logging requirements: use `api.compare` INFO for validated ids, row counts, and status counts; WARN for malformed query paths only; ERROR for alignment or response-contract failures with correlation id and sanitized counts. The frontend logs route/lifecycle at DEBUG and API code/status at WARN without payloads.

- [x] **Task 4: Vertical Increment D — harden the working bullet at every contract boundary** (files: `backend/tests/contracts/{test_domain_contracts.py,test_error_contract.py,test_db_constraints.py,test_parser_domain_db.py,test_openapi_jsonschema.py}`, `backend/tests/integration/test_tracer_bullet.py`, `backend/src/bmstu_parser/api/error_handlers.py`, `backend/src/bmstu_parser/tracer/ingest.py`, `backend/pyproject.toml`, `frontend/{tsconfig.json,package.json}`, `frontend/scripts/{generate-api.mjs,check-api-drift.mjs}`; dependency: Task 3)

  Deliverable: finish the single `ErrorResponse` implementation for FastAPI request validation, not-found errors, source/domain failures that reach the API, DB errors, and `ResponseValidationError`; document all of them in the generated OpenAPI. Prove DB `NOT NULL`, FK, UNIQUE, CHECK, reference-table, and numeric constraints with direct invalid writes; prove that an empty curriculum, invalid selected record, duplicate identity, and changed source conflict roll back the entire two-program ingest. Validate API payloads against the generated OpenAPI JSON Schema. Add the complete captured-fixture test `raw source -> parser -> raw DTO -> normalized -> domain -> SQLite/Alembic -> API -> frontend-compatible DTO`, plus a frontend generation/drift check. Configure strict Python typing (`mypy --strict` for new tracer/contracts/db/api code), strict TypeScript options, and mutation tests showing a changed required field, enum, range, or response property fails at the first affected boundary.

  Verification: no new tracer/API/DB code uses `Any`, untyped dictionaries, magic enum strings, or undeclared nulls; contract tests run without network; a separate live-source smoke command proves the fixture refresh path against the official BMSTU URLs.

  Logging requirements: contract tests capture structured logs and assert stable error code/path pairs; CI logs stage names, schema hash, migration revision, and test counts at INFO; rejected fields and rollback reasons are WARN/ERROR with sanitized paths; raw documents and response bodies remain suppressed.

- [x] **Task 5: Vertical Increment E — package the same end-to-end scenario for repeatable demonstration and CI** (files: `backend/README.md`, `frontend/README.md`, `.github/workflows/ci.yml`, `backend/scripts/{export_openapi.py,run_tracer_bullet.py}`, `backend/.env.example`, `frontend/.env.example`; dependency: Task 4)

  Deliverable: document and automate one reproducible flow: install dependencies, apply Alembic, replay the official captured fixture or explicitly refresh it from the live source, ingest both target programs, start FastAPI, use Swagger at `/docs`, execute all three endpoints, export `/openapi.json`, generate/check the frontend client, start the frontend, and open the comparison screen. Make `run_tracer_bullet.py` print the run id, database path, source hashes, API URLs, and frontend URL so the demonstration is verifiable. Add CI for strict Python tests/typecheck, migration/constraint checks, deterministic OpenAPI export and client drift, and frontend typecheck/build. Document that `profile.json` and the inline dashboard are legacy artifacts, how raw snapshots and provenance are retained, how source-contract failures stop ingestion, and how a future Faculty/Department contract extends the registry without rewriting this path.

  Verification: a fresh checkout can reproduce the same user-visible comparison from the captured official-source fixture without network access; the optional live refresh produces a new manifest/hash and fails closed if the selected source no longer satisfies the contract.

  Logging requirements: document `LOG_LEVEL`, stage names, correlation/run ids, redaction rules, and expected INFO/WARN/ERROR events; CI publishes concise sanitized summaries only and never uploads raw source bodies, signed URLs, or API payloads.

## Acceptance Criteria

The plan is complete only when the following milestones are demonstrated in order against the same captured/ingested official-source dataset:

1. After Task 1, the first vertical slice displays one real `09.03.01-02` program card in the frontend; its API response is generated from OpenAPI and its data is read from SQLite after parser/normalization/ingest.
2. After Task 2, both real target programs and their non-empty curriculum rows are available through the API and visible in the frontend; no data comes from `profile.json` or inline `BMSTU_PROFILE`.
3. After Task 3, Swagger executes all three endpoints and the frontend comparison screen displays the same typed disciplines, semesters, hours, credits, assessments, and compare statuses as the API.
4. After Task 4, malformed requests, missing data, source failures, response mismatches, direct DB violations, and partial-ingest failures produce deterministic structured errors or rollbacks; the complete chain and OpenAPI JSON Schema are tested.
5. After Task 5, a fresh checkout can reproduce the same two-program comparison from the captured official-source fixture, while a live refresh is provenance-hashed and fails closed on contract drift.
6. A deliberate contract change (required field, enum, range, or response property) produces a deterministic parser validation failure, DB/test failure, API/OpenAPI mismatch, or frontend type/build error at the first broken boundary.

## Non-goals and Follow-up Extension Point

This slice does not implement Faculty, Department, admission, tuition, rankings, all 177 Andromeda fields, or a generic arbitrary-record API. Their future contracts can add models and relation tables under the same central contract registry and source/provenance interfaces. The current task must not broaden into a full profile migration or keep `profile.json` alive as a second API schema.

## Commit Plan

- **Commit 1** (after Task 1): `feat: add first end-to-end bmstu tracer slice`
- **Commit 2** (after Task 2): `feat: ingest second program and expose curriculum`
- **Commit 3** (after Task 3): `feat: add generated compare screen`
- **Commit 4** (after Task 4): `test: enforce tracer contracts and schema drift`
- **Commit 5** (after Task 5): `docs: package the bmstu tracer bullet workflow`
