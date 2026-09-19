<!-- aif:plan-mode:ultra -->

# Andromeda: Tracer Bullet / Private Alpha → MVP Production Level

## Plan Metadata

| Field | Value |
| --- | --- |
| Plan identifier | feature-andromeda-mvp-production-level |
| Mode | ultra |
| Language | Русский; technical names remain in repository form |
| Scope | Repository audit plus incremental implementation of all planned MVP Production Level phases |
| Baseline commit | 4088116 merge: graduate Andromeda to MVP private alpha |
| Creation date | 2026-09-18 |
| Working branch | feature/andromeda-mvp-production-level |
| Base branch | main |
| Testing | Required; baseline and focused checks were executed read-only |
| Logging | Verbose; every implementation task has logging/redaction requirements |
| Documentation | Required; current docs, operations runbooks, archive, and AI workflow are in scope |
| Roadmap linkage | none |
| Handoff | none |

## Original Request

Нужно провести глубокий аудит текущего состояния репозитория Andromeda и составить конкретный технический план перехода проекта из стадии Tracer Bullet / Private Alpha foundation в полноценную стадию MVP Production Level.

ВАЖНО: на этом этапе НЕ вносить изменения в код. Сначала исследовать реальный репозиторий, проверить каждый тезис ниже по исходникам, тестам, документации, конфигурации и текущим runtime flows, а затем составить grounded implementation plan.

Ключевое архитектурное ограничение

НЕ УПРОЩАТЬ существующую архитектуру ради MVP.

Существующая сложность архитектуры является сознательным решением проекта.

Не предлагать:

* превращать modular monolith в простой монолит;
* объединять bounded contexts только потому, что сейчас проект небольшой;
* удалять domain/contracts/services/repository layering как «избыточный»;
* убирать архитектурные boundary tests;
* отказываться от contract-first подхода;
* убирать typed contracts;
* ослаблять strict typing;
* сокращать архитектурные abstractions исключительно ради уменьшения количества файлов;
* превращать проект в prototype-style код;
* ломать existing separation между ingestion, domain, recommendation, decision, admissions и другими contexts.

Допускаются локальные улучшения API, contracts, dependency direction, naming и ответственности модулей, если это делает архитектуру более корректной.

Но высокая модульность и production-oriented структура должны остаться.

Цель — не сделать Andromeda проще.

Цель — сделать существующую серьёзную архитектуру оправданной реальным качеством продукта, данных, тестирования и эксплуатации.

⸻

Исходная проблема

Сейчас репозиторий выглядит архитектурно сильнее, чем фактически зрел продукт.

Нужно убрать этот разрыв.

Проект должен перестать быть хорошо оформленным tracer bullet и стать реально работающим MVP, который можно:

* запустить;
* наполнить актуальными данными;
* использовать реальными пользователями;
* поддерживать;
* развивать;
* диагностировать;
* безопасно изменять.

⸻

1. Сначала проверь критику, а не принимай её на веру

Для каждого приведённого ниже замечания установи один из статусов:

* CONFIRMED — проблема реально присутствует сейчас;
* PARTIALLY CONFIRMED;
* OUTDATED — уже исправлено;
* INTENTIONAL — сознательное архитектурное или продуктовое решение;
* FALSE POSITIVE;
* FUTURE RISK — сейчас не проблема, но станет проблемой при масштабировании.

Каждый вывод должен иметь evidence из текущего repository state:

* paths;
* modules;
* symbols;
* tests;
* configuration;
* docs;
* runtime/data flows.

Никаких выводов исключительно на основании текста этого задания.

Repository is the source of truth.

⸻

2. Архитектура

Проверить реальное состояние всех bounded contexts и архитектурных границ.

В частности:

* decision;
* proftest;
* recommendations;
* admission_fit;
* admissions;
* comparison;
* campus;
* events;
* personal_route;
* admin_ops;
* auth;
* ingestion;
* остальные существующие contexts.

Определить:

* есть ли реальные нарушения dependency direction;
* есть ли циклические зависимости;
* дублируется ли domain logic;
* действительно ли contracts являются public boundary;
* нет ли прямых импортов implementation details;
* есть ли dead abstractions;
* есть ли adapters/interfaces без реальных consumers;
* есть ли legacy compatibility layers, которые уже можно безопасно удалить;
* остались ли tracer-bullet shortcuts;
* остались ли temporary abstractions;
* остались ли TODO/FIXME/temporary fallbacks;
* насколько architecture tests соответствуют фактической архитектуре.

ВАЖНО:

НЕ рассматривать само количество модулей или bounded contexts как дефект.

Исправлять нужно нарушения архитектуры, а не архитектурную сложность как таковую.

⸻

3. Tracer Bullet leftovers

Найти всё, что осталось от исследовательской / tracer-bullet стадии:

* spike code;
* archived implementations;
* compatibility shims;
* deprecated endpoints;
* deprecated schemas;
* legacy tests;
* temporary feature flags;
* placeholder services;
* fake implementations;
* mock-only production paths;
* unreachable code;
* abandoned migrations;
* stale fixtures;
* obsolete docs;
* duplicated v1/v2/v3 logic;
* comments, которые больше не соответствуют действительности.

Для каждого элемента определить:

1. оставить;
2. мигрировать;
3. заменить;
4. удалить после доказательства эквивалентности.

Не удалять старую реализацию до того, как:

* новый path покрыт regression/integration tests;
* доказана функциональная эквивалентность либо намеренное изменение поведения.

⸻

4. Product readiness

Проверить, насколько backend capabilities реально соответствуют пользовательским сценариям Andromeda.

Основные сценарии:

1. Куда я могу поступить?
2. Что выбрать в конкретном вузе?
3. Какие программы мне подходят?
4. Чем отличаются мои варианты?
5. Я не знаю, что выбрать — профориентационный старт.

Проследить каждый сценарий end-to-end:

frontend
→ API
→ contracts
→ application/domain
→ repository
→ database/data
→ response
→ frontend rendering.

Для каждого определить:

* полноценен ли flow;
* где используются placeholders;
* где возвращается not_available;
* где UI обещает больше, чем backend способен посчитать;
* какие данные отсутствуют;
* какие states обрабатываются плохо;
* какие ошибки видит пользователь.

Особенно проверить recommendation pipeline.

Проверить состояние:

* Content Fit;
* Admission Fit;
* Career Fit;
* Workload Readiness;
* explanation layer;
* confidence;
* provenance.

Если какой-либо компонент публично заявлен, но фактически не реализован:

* либо реализовать минимально жизнеспособную production-safe версию;
* либо исключить его из публичного продукта до реализации.

Не оставлять misleading placeholders.

⸻

5. Recommendation system

Провести отдельный аудит recommendation architecture.

Проверить:

* ranking;
* filtering;
* weighting;
* normalization;
* confidence;
* missing data;
* explanation;
* provenance;
* admission eligibility;
* profile scope;
* decision context;
* deterministic behaviour.

Проверить, не получается ли ситуация, где сложный recommendation contract фактически строится на слишком малом количестве реальных сигналов.

Каждая recommendation должна быть объяснима.

Пользователь должен иметь возможность понять:

* почему программа рекомендована;
* какие данные использованы;
* каких данных не хватало;
* насколько результат надёжен.

⸻

6. Proftest

Отдельно проверить текущий adaptive proftest.

Не делать новый тест с нуля без необходимости.

Проверить:

* session model;
* adaptive selection;
* stopping criteria;
* question usefulness;
* stale_question_ids;
* dimensions/components;
* scoring;
* recommendation mapping;
* restart/resume;
* incomplete session handling;
* persistence;
* frontend UX;
* API contracts.

Цель MVP:

короткий адаптивный тест, который собирает достаточно сигнала для первичного recommendation, а не длинный психологический опрос.

Убрать complexity, которая не улучшает качество результата, но сохранить корректную архитектурную модель.

⸻

7. Ingestion — критический блок

Это один из наиболее важных блоков плана.

Проверить BMSTU и HSE ingestion end-to-end.

Исследовать:

* discovery;
* download/fetch;
* HTML parsing;
* PDF parsing;
* normalization;
* validation;
* canonicalization;
* database projection;
* provenance;
* atomic updates;
* source gaps;
* retries;
* idempotency;
* failure recovery.

Проверить зависимости от:

* PyMuPDF;
* pdfplumber;
* pypdf;
* BeautifulSoup;
* Poppler;
* других parser dependencies.

Найти university-specific assumptions, скрытые под generic abstractions.

Для каждого assumption определить:

* нормально ли это как adapter-specific logic;
* просочилось ли оно в core;
* помешает ли добавлению третьего университета.

Core должен оставаться university-independent там, где это действительно domain-generic.

Но не создавать generic abstractions заранее без реальной необходимости.

⸻

8. Data quality

Проверить taxonomy и discipline classification.

В частности:

* 22-area classification;
* area_weights;
* fallback_unclassified;
* coverage;
* unknown disciplines;
* manually classified values;
* duplicate mappings;
* normalization;
* historical aliases;
* audit process.

Нужно определить механизм, при котором добавление нового университета не потребует бесконтрольной ручной классификации тысяч новых строк.

Продумать:

* deterministic classification;
* auditable overrides;
* unknown queue;
* coverage metrics;
* regression dataset;
* manual correction workflow.

Fail-closed сохранить там, где отсутствие данных может привести к ложному выводу.

Но absence of data не должна автоматически превращать пользовательский продукт в бесполезный набор source gap.

Разделить:

* truly blocking missing data;
* degradable missing data;
* informational missing data.

⸻

9. Database и migrations

Проверить production readiness persistence layer.

Проверить:

* PostgreSQL schema;
* migrations;
* constraints;
* indexes;
* transaction boundaries;
* uniqueness;
* idempotent ingestion;
* concurrency;
* atomic projection;
* rollback;
* test database setup;
* production bootstrap.

Найти места, где корректность поддерживается application code, хотя должна поддерживаться database constraint.

⸻

10. Tests

Не сокращать тестирование только потому, что тестов много.

Задача — сделать тестовую систему полезнее и понятнее.

Проверить:

* unit;
* domain;
* contract;
* architecture;
* integration;
* database;
* ingestion;
* E2E;
* frontend;
* Telegram bot;
* regression tests.

Найти:

* duplicated tests;
* brittle fixture snapshots;
* tests implementation details;
* flaky tests;
* excessive mocks;
* tests, которые ничего существенного не проверяют;
* gaps в critical business logic.

Добавить измеримый coverage reporting.

Но не использовать coverage percentage как единственный quality metric.

Выделить critical business logic и убедиться, что она покрыта содержательными тестами.

⸻

11. Test execution

Сейчас большое количество отдельных команд тестирования не должно требовать знания внутренней структуры проекта.

Нужно прийти к понятным entrypoints вроде:

* fast checks;
* backend tests;
* frontend tests;
* integration tests;
* ingestion tests;
* full CI;
* production smoke.

Точные команды определить по существующему toolchain.

Не обязательно использовать Makefile, если repository уже имеет более подходящий механизм.

Цель — один очевидный путь проверки проекта.

⸻

12. CI

Проверить весь CI pipeline.

Определить:

* какие checks обязательны;
* какие redundant;
* какие flaky;
* где кеширование отсутствует;
* какие dependencies unnecessarily reinstall;
* где можно безопасно распараллелить jobs;
* есть ли migration check;
* schema/OpenAPI drift check;
* architecture check;
* frontend build;
* backend test;
* integration;
* ingestion fixture smoke;
* Playwright;
* production smoke.

CI должен быть строгим, но понятным.

Не скрывать failing checks удалением проверки или ослаблением assertions.

⸻

13. Frontend

Проверить frontend-next не только как API consumer, а как пользовательский продукт.

Исследовать:

* route structure;
* data fetching;
* generated OpenAPI client;
* loading;
* errors;
* empty states;
* stale data;
* mobile;
* accessibility;
* responsiveness;
* DecisionContext representation;
* shortlist;
* comparison;
* recommendation;
* proftest.

Найти места, где backend domain model протекает напрямую в UX.

UI не должен заставлять абитуриента понимать внутреннюю архитектуру Andromeda.

⸻

14. Product coherence

Проверить соответствие пяти основных пользовательских flows текущему интерфейсу.

У пользователя не должно быть ощущения набора отдельных backend features.

Нужна связная воронка:

интерес / исходные данные
→ первоначальный набор программ
→ shortlist
→ comparison
→ detailed explanation
→ admission reality
→ решение.

Не создавать новые bounded contexts только ради UI flow, если существующие позволяют это реализовать.

⸻

15. Auth

Проверить:

* Argon2;
* opaque sessions;
* anonymous HttpOnly cookie;
* anonymous → account transfer;
* isolation rules;
* account precedence;
* session lifecycle;
* CSRF;
* logout;
* expiration;
* concurrent sessions;
* privilege boundaries.

Не упрощать auth только потому, что проект MVP.

Исправить только реальные security/usability issues.

⸻

16. Admin/Ops

Проверить admin_ops:

* API key;
* ingest trigger;
* retries;
* ingest_runs;
* state machine;
* failure state;
* observability;
* audit trail.

Сохранить production-oriented operations architecture.

Но убрать ceremony, которое не даёт реальной эксплуатационной ценности.

Любой ingestion run должен быть диагностируем.

⸻

17. Observability

Проверить наличие:

* structured logging;
* request correlation;
* ingestion run IDs;
* exception reporting;
* timing;
* health endpoints;
* readiness;
* database connectivity;
* migration status;
* external source failures.

Составить минимальный observability baseline для MVP Production Level.

Не строить enterprise observability platform.

⸻

18. Local developer experience

Сложная архитектура допустима.

Сложный запуск — нет.

Новый разработчик или AI agent должен иметь возможность получить работающую систему через минимальное количество хорошо документированных команд.

Проверить:

* environment setup;
* PostgreSQL;
* Poppler;
* frontend;
* backend;
* migrations;
* fixture ingestion;
* Playwright;
* Telegram bot;
* env variables.

Предложить canonical bootstrap path.

⸻

19. Documentation

Не сокращать документацию просто потому, что её много.

Проверить её на:

* актуальность;
* duplication;
* contradictions;
* aspirational claims;
* stale commands;
* obsolete architecture;
* historical material, смешанный с current documentation.

Разделить:

* current documentation;
* ADR/history/archive;
* operational runbooks.

README должен описывать реальное текущее состояние продукта.

Не называть capability production-ready, если она фактически experimental/private-alpha.

⸻

20. AGENTS.md / AI workflow

Проверить, что инструкции агентам:

* соответствуют реальной структуре repository;
* не дублируют друг друга;
* не содержат obsolete paths;
* не требуют ritual действий без engineering value.

Сохранить важные guardrails:

* evidence;
* regression tests;
* architecture boundaries;
* validation;
* no hiding failures.

⸻

21. Dependencies

Провести dependency audit.

Определить:

* unused dependencies;
* duplicate functionality;
* optional runtime dependencies;
* system packages;
* version pinning;
* security problems;
* unnecessary heavyweight tooling.

Не удалять зависимость только потому, что она большая.

Удалять только то, что реально лишнее или заменено.

⸻

22. Security

Проверить MVP security baseline:

* secrets;
* cookies;
* auth;
* admin endpoints;
* API keys;
* CORS;
* CSRF where applicable;
* input validation;
* SQL;
* SSRF possibilities in ingestion;
* file/PDF handling;
* rate limits для чувствительных endpoints;
* dependency vulnerabilities;
* sensitive logging.

Не заниматься compliance theatre.

Только реальные угрозы для данного продукта.

⸻

23. Performance

Не делать premature optimization.

Но проверить очевидные проблемы:

* N+1;
* repeated heavy calculations;
* repeated parsing;
* missing indexes;
* unnecessarily large responses;
* expensive recommendation recomputation;
* blocking operations;
* pagination;
* ingestion memory usage.

Исправления включать в план только при наличии evidence.

⸻

24. Scope и product claims

Проверить README, MVP docs и product wording.

Нужно чётко зафиксировать состояние проекта после работ:

Andromeda MVP Production Level.

Не enterprise platform.

Не prototype.

Это production-capable MVP с ограниченным университетским coverage.

Явно разделить:

* что поддерживается;
* какие университеты поддерживаются;
* какие данные поддерживаются;
* какие возможности experimental;
* какие ограничения известны.

⸻

25. Переход Tracer Bullet → MVP

Нужно явно определить exit criteria.

Проект можно считать вышедшим из Tracer Bullet только если:

1. Основные пользовательские flows работают end-to-end.
2. Нет product-visible placeholders, выдаваемых за реализованные capabilities.
3. Ingestion BMSTU/HSE воспроизводим.
4. Ошибки ingestion диагностируются.
5. Database schema и migrations стабильны.
6. Critical business rules покрыты тестами.
7. Full CI проходит из clean checkout.
8. Production-like deployment можно поднять по документированной процедуре.
9. Frontend обрабатывает loading/error/empty/partial-data states.
10. Recommendation объясним.
11. Missing data корректно отражается.
12. Security baseline выполнен.
13. Documentation соответствует коду.
14. Не осталось tracer-bullet shortcuts в critical paths.
15. Есть smoke-test production flow.
16. Добавление следующего университета не требует изменения generic domain core без реальной domain-причины.

⸻

26. План должен быть конкретным

Не писать рекомендации вида:

«улучшить тестирование»;
«улучшить архитектуру»;
«почистить документацию».

Для каждой задачи указать:

* проблема;
* evidence;
* affected paths;
* affected symbols/modules;
* desired state;
* конкретные изменения;
* dependencies;
* migration strategy;
* tests;
* acceptance criteria;
* риски;
* rollback/fallback при необходимости.

⸻

27. Приоритеты

Разделить работу минимум на:

P0 — блокирует переход в MVP Production Level.

P1 — необходимо для качественного MVP.

P2 — желательно сделать до публичного beta.

P3 — будущая масштабируемость / post-MVP.

Не смешивать долгосрочные улучшения с blocker-задачами.

⸻

28. Порядок реализации

Составить dependency-aware implementation sequence.

Предпочтительно вертикальными рабочими slices, а не огромным horizontal refactor.

Сначала фундаментальные blockers.

После каждого значимого этапа система должна оставаться runnable.

Не делать giant-bang rewrite.

⸻

29. Сохранение baseline

Перед рискованными изменениями:

* зафиксировать текущий behaviour;
* добавить regression evidence;
* не удалять старый implementation path до доказательства нового;
* migrations делать обратимыми там, где это разумно;
* сохранить working checkpoints.

⸻

30. Финальный артефакт

Создай полноценный AI Factory implementation plan.

В начале дай:

1. Current repository state.
2. Что из критики подтвердилось.
3. Что оказалось неверным или устаревшим.
4. Какие решения являются намеренными и не должны меняться.
5. Главные blockers выхода из Tracer Bullet.

Затем сформируй dependency-aware phased plan.

Для каждой фазы:

* goal;
* exact tasks;
* paths/modules;
* tests;
* acceptance criteria;
* definition of done.

В конце дай:

MVP Production Level Exit Checklist

и

Deferred Post-MVP Work

После выполнения плана должно быть возможно обоснованно изменить статус проекта с:

Tracer Bullet / Private Alpha foundation

на:

MVP Production Level.

Не вноси изменения в код в рамках этой команды.

Только исследование repository + grounded implementation plan.

## Settings

| Setting | Value |
| --- | --- |
| Testing | yes; baseline, focused suites, and release gates are required |
| Logging | verbose; each task specifies structured fields, redaction, and failure handling |
| Docs | yes; current docs, operations runbooks, archive, and AI workflow are in scope |

## Scope Guardrails

This plan preserves the existing modular monolith, bounded contexts, domain /
contracts / services / repository layering, typed public contracts, strict
typing, architecture tests, contract-first API, and university-independent
core boundaries. It does not propose microservices, Kafka, CQRS, flattening
contexts, removal of repository ports, or prototype-style shortcuts.

The plan is based on source, tests, configuration, documentation, Graphify
reports, and read-only command results. Pre-existing dirty/untracked files were
not overwritten or removed. The only workspace changes for this request are
the plan bundle itself; the feature branch was created because the configured
AI Factory workflow requires a plan branch.

## Current Repository State

Andromeda is a substantial source-backed modular monolith, not an empty
prototype. The canonical runtime is backend/src/andromeda with FastAPI,
PostgreSQL for development/staging, SQLite for tests, frontend-next as the
canonical web consumer, and telegram-bot as an additional consumer. The
subject-module set contains admin_ops, admission_fit, admissions, auth,
campus, comparison, curricula, decision, disciplines, events, personal_route,
proftest, programs, recommendations, and universities. Each subject module
has the intended domain/contracts/services/repository shape.

The strongest confirmed baseline is:

- 13 architecture tests pass and the source-only import graph has no detected
  cycles or forbidden subject-module imports.
- The focused ingestion, taxonomy, recommendation, proftest, and architecture
  slice passed 90 tests.
- Frontend unit tests passed 13 tests in four files.
- BMSTU/HSE fixture adapters, canonical projection, PostgreSQL CI, OpenAPI
  generation, anonymous/account profile scope, optimistic decision revision,
  and v3 adaptive proftest are real implementations.
- The repository has deployment documentation and YC compose files, but
  production-like clean-checkout reproducibility has not been proven.

The important negative baseline is:

- The active API wiring and backend/scripts still coexist with an unused
  composition/container.py graph.
- run_andromeda_demo.py delegates to run_tracer_demo.py, which delegates to
  run_tracer_bullet.py; backend README, tests, Dockerfile, and entrypoint still
  contain tracer naming and an untracked tracer.db seed/fallback.
- deploy/yc/compose.yaml uses backend port 8020 while
  frontend-next/src/lib/server-api.ts and telegram-bot configuration default
  to backend:8000, and no single internal URL contract is enforced.
- infrastructure/config/settings.py has test/development/staging policy but
  no explicit fail-closed production environment; deployment safety therefore
  depends on staging conventions rather than a production profile.
- Recommendation and decision contracts are more mature than their evidence
  propagation: Content Fit is deterministic, while confidence, source hashes,
  inferred activity signals, and missing-data semantics are not consistently
  carried through to UI.
- Admission Fit is separate in backend policy but the program UI calls it a
  chance calculator and submits hardcoded 85/82/88 scores.
- HSE/BMSTU fixture ingestion is covered; live repeatability, parser resource
  limits, retries for all failure classes, optional-gap persistence, quality
  quarantine, and concurrent run recovery are not proven.
- Taxonomy has 22 areas and deterministic overrides, but fallback-to-Universal
  does not produce an explicit unknown/review outcome. The documented live
  audit metric is not executable in the current code.
- Database schema and migrations are strong, but readiness does not compare
  against the expected Alembic head, and ingestion lifecycle/locks are split
  across transactions without a concurrency protocol.
- CI is broad but lacks explicit coverage/critical-rule reporting, dependency
  scanning, a named architecture/dead-surface gate, and a single canonical
  developer command.

### Baseline commands and results

| Command | Result | Interpretation |
| --- | --- | --- |
| cd backend; python -m pytest -q tests/architecture | 13 passed | Current module/runtime boundary baseline is green |
| cd backend; focused architecture/ingestion/taxonomy/recommendation/proftest pytest slice | 90 passed, 6 warnings | Core fixture/domain slice is runnable; warnings need toolchain disposition |
| cd frontend-next; npm run test:unit -- --run | 4 files / 13 tests passed | Frontend unit baseline is green |
| cd frontend-next; npm run check-api-drift without a running API | failed with HTTP 404 | Command assumes a live endpoint unless OPENAPI_FILE is supplied |
| cd frontend-next; OPENAPI_FILE=openapi.json npm run check-api-drift | passed according to focused frontend audit | Tracked generated contract is usable; command prerequisites must be canonical |
| python backend/scripts/export_openapi.py --check | CLI rejected --check | Export script requires --out; command documentation must be normalized |
| git diff --check | passed in the read-only audit | Existing dirty state had no whitespace error in tracked diff |
| Graphify backend/frontend reports | backend 2,189 nodes / 6,057 edges / no import cycles; frontend 410 nodes / 1,187 edges / no import cycles | Architecture investigation evidence, not a replacement for tests |

The frontend drift command was intentionally not made to pass by starting a
background server or changing files during this audit. Live source ingestion,
production database, deployment, backup/restore, concurrency, and external
security scans remain release evidence items rather than assumed facts.

## Executive Audit Conclusions

### What is confirmed

1. The runtime still contains tracer-bullet compatibility ownership:
   wrappers, old CLI names, tracer database seed references, old test imports,
   and stale documentation.
2. There are two composition concepts, and composition/container.py has no
   active source consumer. This is an architectural ownership defect, not a
   reason to remove modularity.
3. Recommendation evidence is incomplete: the scoring algorithm is real and
   deterministic, but confidence/reliability, provenance/source hashes, and
   inferred-vs-direct signals are not consistently public.
4. The UI exposes an admission “chance” calculator with invented default
   scores; this is a product-visible misleading placeholder.
5. Program detail is coupled to curriculum and admissions through Promise.all,
   so optional/partial data can hide valid program facts.
6. Ingestion retry, source-gap persistence, SSRF/final redirect policy,
   parser limits, quality gates, concurrent run locking, and crash recovery
   are incomplete.
7. Taxonomy fallback is not auditable enough to support the documented live
   coverage claim or scalable third-university onboarding.
8. Readiness, production configuration, deployment port/env contracts,
   coverage reporting, dependency scanning, and canonical verification
   commands are incomplete.
9. Auth has a strong Argon2/opaque-session/isolation foundation, but rate
   limits, abuse controls, full CSRF review, cleanup, and privilege/lifecycle
   evidence need completion before public exposure.
10. Source health currently runs mutating live ingestion from a scheduled
    workflow, without the required read-only/alertable operational separation.

### What is false, outdated, or not a defect

- “The architecture is too complex for an MVP” is a FALSE POSITIVE. The
  repository rules, module-boundary tests, public contracts, and Graphify
  import scan support the intentional modular monolith. Complexity is not a
  blocker; unowned runtime wiring is.
- “There are cross-context dependency cycles/direct implementation imports” is
  a FALSE POSITIVE for the current subject modules. Existing architecture
  tests and AST/Graphify evidence show no forbidden imports or cycles.
- “proftest-spike is an active second runtime” is OUTDATED. Its executable
  manifests/source are absent from the runtime surface and the archive note
  says it is retired. The untracked workspace directory is still a hygiene
  decision and must not be deleted in this plan.
- “No production-oriented auth architecture exists” is OUTDATED/FALSE
  POSITIVE. Argon2id, opaque cookies, hashes, scope isolation, account
  precedence, transfer semantics, and trusted-origin checks exist. The
  remaining abuse/CSRF/lifecycle gaps are real, narrower issues.
- “A TODO/FIXME backlog is the main problem” is a FALSE POSITIVE. Source-only
  runtime search found no material TODO/FIXME/XXX/HACK backlog. Existing
  fallbacks are behavior that needs typed observability, not a comment cleanup.
- “All dependencies should be removed or simplified” is a FALSE POSITIVE.
  PyMuPDF, pypdf, pdfplumber, BeautifulSoup, Poppler, and browser fallback
  have concrete parser uses; the issue is reproducibility/resource policy.
- A blanket CORS defect is a FALSE POSITIVE: explicit origins and credential
  policy exist. Production origin validation and state-changing request
  protection still require tests.
- The 2,582-discipline fallback_unclassified = 0 statement is OUTDATED/
  UNVERIFIED, not current evidence. It must not remain as a production claim
  until an executable audit produces it.
- Documentation referring to Alembic 0014 while current head is 0016 is
  OUTDATED. It is a documentation drift issue, not evidence that the migration
  chain itself is invalid.

### Intentional decisions to preserve

- Modular monolith and all current bounded contexts.
- Domain/contracts/services/repository layering and typed Protocol ports.
- Public contract-first API and generated frontend types.
- Separate Content Fit, Admission Fit, Career Fit, and Workload Readiness.
- Admission Fit must not alter Content Fit ranking.
- DecisionContext owns explicit shortlist/final choice; recommendations are
  derived suggestions and never silently prune choice.
- Anonymous opaque HttpOnly profile/auth cookies, account precedence, and
  explicit guest-to-account transfer.
- Fail-closed behavior where missing data could cause a false admission or
  ranking conclusion, with degradable/informational states where safe.
- University-specific parsing/mapping under ingestion adapters.
- Map-agnostic events/campus and read-only personal route.
- Telegram in-memory callback state as an explicit single-replica P3
  limitation until scale requirements justify shared storage.

## Main Promotion Blockers

> Historical-baseline note: this section, the status table below, and the
> end-to-end flow audit record the findings captured when the plan was created
> from baseline commit `4088116`. They are retained for traceability and are
> not a present-tense release decision after the implementation phases ran.
> For current status, use the phase implementation notes and the release
> evidence ledger in [`docs/release/mvp-production-level-gate.md`](../../../docs/release/mvp-production-level-gate.md).

These are blockers for changing the status claim, not a statement that the
current repository is unusable:

1. One canonical active composition/runtime graph and canonical non-tracer
   runner are not established.
2. Consumer-less Protocol definitions around comparison, curricula, programs,
   disciplines, and identity resolution have no explicit keep/use/deprecate
   decision.
3. Clean-checkout deployment is not reproducible because the image references
   untracked tracer.db and internal ports/env names disagree.
4. BMSTU/HSE ingestion lacks a complete production safety envelope:
   structured optional gaps, retries, SSRF/resource limits, quality gate,
   last-good protection, per-university concurrency, and recovery.
5. Recommendation and admission contracts/UI do not yet expose complete
   evidence, confidence, provenance, and honest unknown semantics.
6. The five user flows are not all partial-data/error-safe end to end;
   program detail and recommendation fallback can mask failures.
7. Taxonomy coverage/unknown handling and third-university regression process
   are not executable/auditable.
8. Security/operations baseline lacks abuse limits, full browser mutation
   protection review, external-source safety, migration-head readiness, and
   durable source/run observability.
9. Full clean-checkout CI, coverage/critical-rule reporting, canonical
   bootstrap, production smoke, and documentation truth are not yet proven.

## Status Audit of the Requested Critique

The status below is the repository assessment captured at plan creation.
“PARTIALLY
CONFIRMED” means an important slice is real but the product/operational
claim is incomplete. Evidence paths are source-controlled unless explicitly
marked as a runtime unknown. Subsequent implementation phases may have
changed these findings; reconcile them with the release evidence ledger before
making a promotion decision.

| # | Topic | Status | Evidence and precise interpretation |
| --- | --- | --- | --- |
| 2 | Architecture and bounded contexts | INTENTIONAL | 15 subject modules, public contracts, repository ports, no forbidden cycles/imports; duplicate composition root and missing same-layer/dead-surface gates are local risks, not a reason to simplify |
| 3 | Tracer-bullet leftovers | CONFIRMED | run_andromeda_demo → run_tracer_demo → run_tracer_bullet; legacy tests/docs; backend Dockerfile/entrypoint tracer.db; compatibility facades are intentional one-cycle paths |
| 4 | Product readiness / five flows | PARTIALLY CONFIRMED | backend vertical slices and frontend routes exist; program detail partial data, admission wording/defaults, recommendation fallback, source/provenance gaps, and live/deployment evidence are incomplete |
| 5 | Recommendation system | PARTIALLY CONFIRMED | scoring/ranking/explanations are deterministic; confidence/reliability/provenance/inferred signals/missing candidates are not complete |
| 6 | Adaptive proftest | PARTIALLY CONFIRMED | v3 session/adaptive/stale/revision/persistence backend is real; legacy v1/v2 paths coexist and frontend negative-state coverage is missing |
| 7 | BMSTU/HSE ingestion | PARTIALLY CONFIRMED | registry, adapters, parser, normalization, fixture tests, raw snapshots, atomic projection exist; live repeatability, quality publication, retry/gap/SSRF/resource/concurrency controls are incomplete |
| 8 | Taxonomy/data quality | CONFIRMED | 22 areas and BMSTU overrides exist; fallback-to-Universal lacks explicit unknown queue/coverage metrics; docs claim is unverified |
| 9 | Database/migrations | PARTIALLY CONFIRMED | constraints, indexes, 0016 linear chain, PostgreSQL CI, atomic projection exist; lifecycle transactions, locks, stale recovery, readiness head, clean seed remain |
| 10 | Tests | PARTIALLY CONFIRMED | broad layered suites are real and should be retained; critical negative/provenance/concurrency/UI gaps and coverage reporting remain |
| 11 | Test execution | CONFIRMED | commands are scattered across README/docs/CI/backend/frontend; OpenAPI drift needs server/artifact prerequisite normalization |
| 12 | CI | PARTIALLY CONFIRMED | broad backend/frontend/PostgreSQL/fullstack/proftest/Telegram workflow exists; repeated setup, missing coverage/dependency/explicit architecture/schema gates remain |
| 13 | Frontend | PARTIALLY CONFIRMED | typed generated client and shared states exist; manual any mappers, dropped fields, partial data coupling, misleading copy, and negative-state gaps remain |
| 14 | Product coherence | PARTIALLY CONFIRMED | unified route and DecisionContext exist; summary/detail comparison mismatch and failure-to-profile fallback break a fully coherent funnel |
| 15 | Auth | PARTIALLY CONFIRMED | Argon2/opaque sessions/isolation/transfer/trusted origin are real; rate limiting, lockout, cleanup, concurrent lifecycle and full CSRF review remain |
| 16 | Admin/Ops | PARTIALLY CONFIRMED | API key, run state/detail, safe errors, and BMSTU retry exist; HSE parity, concurrency/recovery, confirmation/UI drift, and complete audit trail remain |
| 17 | Observability | PARTIALLY CONFIRMED | structured-ish logs, correlation, run IDs, stage logs, health endpoints exist; timing, exception reporting, migration readiness, durable source alerts/gaps remain |
| 18 | Local developer experience | PARTIALLY CONFIRMED | docs, Docker/PostgreSQL/Poppler/Playwright/Telegram instructions exist; no single canonical path and env/port/tracer command drift remain |
| 19 | Documentation | PARTIALLY CONFIRMED | architecture/current docs are substantial; Private Alpha wording, unsupported taxonomy/live claims, stale head, filenames/commands/envs need reconciliation |
| 20 | AGENTS / AI workflow | FALSE POSITIVE | root AGENTS.md and .ai-factory/RULES.md match the modular architecture and require evidence/regression; add path/command validation, do not remove guardrails |
| 21 | Dependencies | PARTIALLY CONFIRMED | parser dependencies are used; lower-bound Python dependencies lack lock/reproducibility and CI vulnerability scan |
| 22 | Security | PARTIALLY CONFIRMED | secrets/cookies/Argon2/admin compare_digest/input schemas/CORS baseline exist; rate/CSRF/SSRF/PDF/resource/dependency/sensitive-log verification incomplete |
| 23 | Performance | FUTURE RISK | bulk catalog/cache paths exist; repeated adaptive/catalog calculations, parser blocking, fallback N+1, indexes/response limits need measurement before optimization |
| 24 | Scope/product claims | PARTIALLY CONFIRMED | docs explicitly limit Career Fit/ML/mass coverage and call Private Alpha; source/deployment/live confidence and UI chance wording overclaim portions |
| 25 | Tracer → MVP exit | CONFIRMED | exit criteria are not all evidenced: live/production-like reproducibility, clean CI/deployment, security, provenance, partial UI, no critical tracer shortcuts |
| 26 | Plan specificity | NOT A REPOSITORY DEFECT; addressed here | This bundle names problems, paths/symbols, contracts, dependencies, migrations, tests, acceptance, logging, risks, and rollback |
| 27 | Priority separation | NOT A REPOSITORY DEFECT; addressed here | P0–P3 labels and promotion blockers are explicit below |
| 28 | Dependency-aware sequence | NOT A REPOSITORY DEFECT; addressed here | Phases are ordered by baseline → runtime/ingestion/data/persistence → product → security/CI/release |
| 29 | Baseline preservation | PARTIALLY PRESENT; must be formalized | Current tests/atomic rollback/compatibility evidence exist; parity snapshots, concurrency failure evidence, and release checkpoints are planned |
| 30 | Final status artifact | PLAN OUTPUT | This bundle is the grounded implementation plan; it does not promote the product status now |

## End-to-End Flow Audit

The following flow descriptions are the baseline audit captured before the
implementation phases. Retain them as rationale for the work items, but use
current executable evidence and the release ledger for present-tense status.

### Flow A: “Куда я могу поступить?”

Current route: AdmissionPage and program detail → decision constraints/
suggestions and admissions/admission-fit endpoints → admissions and
admission_fit services/repositories → admission_offerings and source-backed
facts → AdmissionOutcomes/program UI.

Real behavior: Admission Fit returns readiness/risk/status and source gaps,
not a probability. The UI currently labels a chance calculator, seeds scores,
and uses a Promise.all program-detail load that can hide valid data when
curriculum or admissions are absent. Tuition and location constraints are
collected but explicitly reported as not applied when comparable source facts
are absent. Status: PARTIALLY CONFIRMED, promotion blocker until semantics and
partial states are fixed.

### Flow B: “Что выбрать в конкретном вузе?”

Current route: catalog/program → programs, curriculum, admissions, comparison
and decision routes → programs/curricula/admissions/comparison/decision
services → university-scoped canonical rows.

Real behavior: BMSTU/HSE identity and fixture data exist; comparison summary
and detail have different cardinality (summary supports 2–3, detail A/B);
program detail copy assumes BMSTU; curriculum/admission empty/source states
are under-explained. Status: PARTIALLY CONFIRMED.

### Flow C: “Какие программы мне подходят?”

Current route: proftest or current profile → recommendations or decision
suggestions → profile builder, RecommendationScoringService,
DecisionCandidatePipeline → fingerprint/catalog repositories → recommendation
cards.

Real behavior: Content Fit uses deterministic subject/activity/distinctive and
anti-interest policy; explanation exists. Confidence/provenance/inferred
activity/missing data are not consistently carried to response/UI. A decision
service failure can fall through to legacy/profile-required UI. Status:
PARTIALLY CONFIRMED, P0 product trust issue.

### Flow D: “Чем отличаются мои варианты?”

Current route: shortlist/compare → compare summary/detail API → comparison
service/repositories → curricula/disciplines → summary/evidence UI.

Real behavior: raw evidence and area breakdown are real; shortlist persistence
is covered; compare C only participates in summary, detail error lacks retry,
and stale data/state handling needs explicit states. Status: PARTIALLY
CONFIRMED.

### Flow E: “Я не знаю, что выбрать — профориентационный старт”

Current route: ProftestPage → /proftest/sessions → session service/adaptive
selector/profile builder → proftest session/profile repositories → profile
revision and recommendations/decision handoff.

Real behavior: v3 is compact, adaptive, deterministic, resumable, stale-aware,
and persisted in backend. The frontend happy path works, but restore/start/
complete/revision/expiry/local-storage negative states and the legacy path split
need completion. Status: PARTIALLY CONFIRMED.

## Dependency-Aware Implementation Sequence

The implementation is intentionally vertical and keeps the system runnable
after every phase:

1. **Phase 1** freezes behavior and defines the evidence/exit gate.
2. **Phase 2** makes runtime ownership and tracer compatibility explicit.
3. **Phase 3** hardens capture/parse/validate/projection and run control.
4. **Phase 4** makes taxonomy and provenance auditable.
5. **Phase 5** makes PostgreSQL/migrations/concurrency/deployment bootstrap
   safe.
6. **Phase 6** fixes recommendation/admission/decision evidence and claims.
7. **Phase 7** completes the adaptive proftest production slice.
8. **Phase 8** connects the user funnel and all frontend states.
9. **Phase 9** completes public security, ops, health, and observability.
10. **Phase 10** makes tests/CI/DX/docs/deployment/release evidence
    reproducible and runs the final gate.

No phase authorizes a giant-bang rewrite. A phase may add a typed contract,
compatibility adapter, migration, or test, but the old behavior remains until
equivalence or intentional change is proven.

## Priority Model

### P0 — blocks MVP Production Level

- MVP-001–004: evidence baseline and release gate.
- MVP-010 and MVP-012: canonical composition/runtime and tracer-path
  migration.
- MVP-020–023: safe ingestion publication, run lifecycle, and recovery.
- MVP-030 and MVP-033: unknown/provenance semantics needed to trust output.
- MVP-040–042: database invariants, concurrency, readiness, production
  bootstrap.
- MVP-050–052: recommendation/admission/constraint semantics and no misleading
  product claims.
- MVP-080, MVP-081, MVP-083: security/health/observability baseline.
- MVP-090, MVP-092, MVP-093, MVP-095: critical tests, CI, deployment smoke,
  and exit gate.

### P1 — required for a quality MVP

- MVP-011 and MVP-013: architecture/dead-surface/compatibility guardrails.
- MVP-021, MVP-024, MVP-031, MVP-032: parser/dependency/taxonomy workflow.
- MVP-041, MVP-043: concurrency and evidence-based persistence performance.
- MVP-053, MVP-060–063: recommendation evaluation and proftest production
  usability.
- MVP-070–073: coherent frontend, partial states, accessibility, generated
  boundary.
- MVP-082: complete operator experience.
- MVP-091 and MVP-094: canonical developer path and truthful documentation.

### P2 — before public beta when not required by a P0 path

- Broader third-university synthetic adapter/regression corpus.
- Additional coverage thresholds after baseline.
- Dependency lock/upgrade automation and richer CI artifact UX.
- Accessibility regression matrix and larger mobile/browser matrix.
- Parser optimization after timing evidence.

### P3 — post-MVP scalability

- Shared Telegram callback state for multi-replica deployment.
- Queue/worker control plane for ingestion if one-replica scheduling is no
  longer sufficient.
- New university adapters and wider source coverage.
- Career Fit, validated Workload Readiness, ML ranking, public sharing,
  reviews/news/social features, and enterprise observability.

## Tasks

Task checkboxes are maintained only in this index. Phase files contain the
implementation detail and do not duplicate progress checkboxes.

### Phase 1 — baseline and exit gates

- [x] MVP-001 Build the five-flow capability truth matrix
- [x] MVP-002 Define the executable MVP production smoke
- [x] MVP-003 Freeze current behavior before risky changes
- [x] MVP-004 Formalize release decisions and unknowns

Details: [phase-01-baseline-and-exit-gates.md](phase-01-baseline-and-exit-gates.md)

### Phase 2 — architecture and tracer migration

- [x] MVP-010 Establish one canonical composition root
- [x] MVP-011 Strengthen architecture gates without flattening architecture
- [x] MVP-012 Migrate tracer entrypoints and seed names
- [x] MVP-013 Resolve dead ports and compatibility ownership

Details: [phase-02-architecture-and-tracer-migration.md](phase-02-architecture-and-tracer-migration.md)

### Phase 3 — ingestion production readiness

- [x] MVP-020 Define safe fetch, redirect, retry, and resource policy
- [x] MVP-021 Make BMSTU and HSE parser contracts explicit
- [x] MVP-022 Add pre-publication quality gates and safe projection
- [x] MVP-023 Make retries, recovery, and source health operational
- [x] MVP-024 Verify parser dependencies and clean deployment inputs

Details: [phase-03-ingestion-production-readiness.md](phase-03-ingestion-production-readiness.md)

### Phase 4 — data quality and provenance

- [x] MVP-030 Introduce explicit classification outcomes
- [x] MVP-031 Build an auditable override and unknown workflow
- [x] MVP-032 Add coverage metrics and taxonomy regression dataset
- [x] MVP-033 Carry field-level provenance and gap severity

Details: [phase-04-data-quality-and-provenance.md](phase-04-data-quality-and-provenance.md)

### Phase 5 — persistence, migrations, and concurrency

- [x] MVP-040 Complete schema and constraint audit
- [x] MVP-041 Add ingestion locks, idempotency, and crash recovery
- [x] MVP-042 Make bootstrap and readiness production-safe
- [x] MVP-043 Measure query behavior before adding performance fixes

Details: [phase-05-persistence-migrations-and-concurrency.md](phase-05-persistence-migrations-and-concurrency.md)

### Phase 6 — recommendation and decision trust

- [x] MVP-050 Define recommendation evidence, confidence, and provenance
- [x] MVP-051 Make fit semantics and product claims truthful
- [x] MVP-052 Make decision constraints honest and effective
- [x] MVP-053 Add recommendation regression and product-quality evaluation

Details: [phase-06-recommendation-and-decision-trust.md](phase-06-recommendation-and-decision-trust.md)

### Phase 7 — adaptive proftest

- [x] MVP-060 Make the session path canonical and migrate legacy endpoints
- [x] MVP-061 Validate signal usefulness and adaptive determinism
- [x] MVP-062 Harden persistence, resume, restart, and frontend UX
- [x] MVP-063 Connect proftest evidence to recommendation and decision

Details: [phase-07-proftest-production-slice.md](phase-07-proftest-production-slice.md)

### Phase 8 — frontend product coherence

- [x] MVP-070 Implement the coherent funnel over existing contexts
- [x] MVP-071 Normalize loading, error, empty, stale, and partial states
- [x] MVP-072 Fix semantics, accessibility, responsive layout, and copy
- [x] MVP-073 Harden generated OpenAPI/client boundary

Details: [phase-08-frontend-product-coherence.md](phase-08-frontend-product-coherence.md)

### Phase 9 — security, auth, ops, observability

- [x] MVP-080 Complete public security baseline
- [x] MVP-081 Verify auth lifecycle and privilege boundaries
- [x] MVP-082 Complete admin/ops ingestion control plane
- [x] MVP-083 Establish minimal observability baseline

Details: [phase-09-security-auth-ops-observability.md](phase-09-security-auth-ops-observability.md)

### Phase 10 — tests, CI, DX, docs, release

- [x] MVP-090 Make the test system critical-logic driven
- [x] MVP-091 Create one canonical local verification/bootstrap path
- [x] MVP-092 Make CI strict, efficient, and explanatory
- [x] MVP-093 Prove production-like deployment and rollback
- [x] MVP-094 Reconcile current docs, archive, and AI workflow
- [ ] MVP-095 Run final exit gate and preserve rollback checkpoints

Details: [phase-10-tests-ci-documentation-and-release.md](phase-10-tests-ci-documentation-and-release.md)

## Commit Plan

Each checkpoint keeps the system runnable and is created only after the listed tests pass.

1. docs(plan): establish MVP production evidence baseline — Phase 1; capability matrix, frozen behavior, and smoke design.
2. refactor(composition): consolidate runtime and retire tracer ownership — Phase 2; canonical composition and runner parity.
3. feat(ingestion): add safe source publication and recovery — Phase 3; BMSTU/HSE fetch, parser, quality, retry, and dependency policy.
4. feat(data): add auditable taxonomy and provenance — Phase 4; classification outcomes, unknown queue, metrics, and evidence.
5. feat(storage): harden migrations and concurrent projection — Phase 5; constraints, locks, readiness, bootstrap, and measured queries.
6. feat(recommendations): expose evidence and honest fit semantics — Phase 6; recommendation, admission, constraints, and regression corpus.
7. feat(proftest): canonicalize the adaptive session flow — Phase 7; legacy migration, signal evaluation, recovery, and handoff.
8. feat(frontend): complete the decision funnel and partial states — Phase 8; generated boundary, accessibility, and user-state UX.
9. feat(security): harden auth, ops, and observability — Phase 9; security controls, lifecycle, admin diagnostics, health, and logs.
10. test(ci): add critical coverage and canonical verification — Phase 10 tasks MVP-090 through MVP-092; test taxonomy, bootstrap, CI gates.
11. chore(release): verify production smoke, docs, and rollback — Phase 10 tasks MVP-093 through MVP-095; deployment, current docs, and final exit gate.

## MVP Production Level Exit Checklist

Promotion is allowed only when every item has a passing command/artifact and
an owner. Unknown is not pass.

1. Discover, refine, shortlist, compare, admission, and final decision flows
   work end to end.
2. No product-visible placeholder is presented as a completed capability.
3. BMSTU and HSE fixture/live-supported ingestion is reproducible and
   source-scoped.
4. Ingestion failures, quality rejection, retry, and recovery are
   diagnosable by run ID.
5. PostgreSQL schema/migrations/constraints/readiness are stable.
6. Critical business rules have meaningful domain/contract/integration tests.
7. Full CI passes from a clean checkout with required artifacts.
8. Production-like deployment is runnable by documented procedure.
9. Frontend handles loading, errors, empty, stale, conflict, and partial data.
10. Recommendation explains score/evidence/uncertainty and provenance.
11. Missing data is represented as a typed status with useful action.
12. Security baseline passes auth, abuse, CSRF/origin, SSRF/PDF, secrets,
    admin, dependency, and sensitive-log checks.
13. Documentation matches code, current migration head, commands, ports,
    supported universities, and capability scope.
14. Critical paths have no tracer shortcut or unowned compatibility runtime.
15. Production smoke passes after clean deploy and restore.
16. A new university can be added through an adapter/data workflow without
    generic core changes unless a real domain concept requires it.

## Deferred Post-MVP Work

The following is deliberately not mixed into MVP blockers:

- Multi-replica Telegram callback state and distributed worker/queue
  orchestration.
- Broad university onboarding, automated semantic discipline classification,
  and large-scale source discovery beyond the supported adapters.
- Career Fit, validated Workload Readiness, labor-market outcome validation,
  ML ranking, and psychological-test claims.
- Public sharing, reviews, social features, news, and guaranteed admission
  predictions.
- Enterprise metrics/tracing platform, long-retention data lake, and
  compliance program.
- Premature parser parallelism, broad cache infrastructure, and query
  optimization without measured production-like traces.

## Roadmap Linkage

Milestone: none

No configured .ai-factory/ROADMAP.md exists in the repository baseline. This
plan is intentionally self-contained and should be linked to a roadmap
milestone only when the product owner creates one.

## Handoff and Verification Notes

Implementation is being executed incrementally from the baseline while
preserving pre-existing user files. Every phase must leave the system runnable
and update the task checkbox only after its phase evidence is verified. The
release status remains Private Alpha transition until the external clean CI
and production-like deployment/restore evidence is attached.

Before handoff, verify:

- all phase links resolve;
- every task ID in the manifest appears exactly once in a phase file;
- no phase file contains task-progress checkboxes;
- the ultra marker occurs exactly once;
- git diff --check passes;
- git status clearly separates this plan bundle from pre-existing user state;
- implementation changes are scoped to this plan; pre-existing user files and
  unrelated worktree state remain untouched and must be separated at handoff.
