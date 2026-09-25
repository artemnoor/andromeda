# Research: Universal Educational Analytics Interface

Updated: 2026-09-21 18:20
Status: active
Index: [INDEX.md](INDEX.md)

## Active Summary (input for /aif-plan)
<!-- aif:active-summary:start -->
Topic: Универсальный educational analytics и decision interface для Andromeda
Goal: Подготовить существующий modular monolith к typed аналитическим запросам, произвольному channel-neutral диалогу и будущим Jev/MAX adapters без зависимости домена от транспорта, LLM или Jev.
Scope: Архитектурная эволюция поверх текущих ingestion, canonical University/Direction/Program/Curriculum/Discipline, admissions, Admission Fit, recommendations, comparison и decision modules. Включает отдельные semantic, analytics, entity-resolution, conversation и presentation boundaries, persistent analytical projections, QuerySpec, policy ports, ResponseEnvelope, typed API и тонкую миграцию Telegram/Web seams.
Stakeholders: Пользователь Andromeda; backend/API; ingestion operators; Telegram и будущий MAX/Web transports; будущие Jev policy/classifier adapters; PostgreSQL/SQLAlchemy/Alembic operations.
Constraints: Сохранить PostgreSQL, SQLAlchemy, Alembic, canonical IDs/contracts, current admissions/admission-fit/provenance/source-gap semantics и backwards compatibility. Оставить существующую 22-area taxonomy отдельно от non-exclusive semantic features. Не подключать Jev/LLM как runtime dependency; не принимать raw SQL от внешней модели; не превращать missing в zero; не создавать microservices, Kafka, Redis или AssistantService-монолит без отдельного решения. Все schema changes только Alembic. Subject modules не импортируют ORM/FastAPI/ingestion; university-specific behavior остаётся в ingestion adapters.
Requirements: П persist semantic defaults и curriculum-item overrides с confidence, classification method, classifier/taxonomy versions, source hash/run ID и provenance. Вынести ProgramFingerprint/FingerprintBuilder в общий analytics domain с compatibility imports. Строить и хранить rebuildable program projections после ingestion. Ввести versioned extensible metric registry, explicit workload basis и statuses AVAILABLE/PARTIAL/INSUFFICIENT_DATA/UNAVAILABLE. Реализовать bounded typed QuerySpec и AnalyticsResult/evidence без raw SQL. Добавить backend entity resolvers с explicit ambiguity. Хранить generic QuerySession с slot filling для analytics и admission flows. Создать DecisionPolicyPort и ResponsePolicyPort с deterministic implementations; подготовить Jev seams. Возвращать channel-neutral ResponseEnvelope, добавить /analytics/query и /assistant/query, оставить Telegram/Web thin adapters и PDF report path из готового result.
Decisions: Canonical data остаётся source of truth; semantic data и projections являются versioned derived data и могут быть полностью rebuilt. Первичная semantic классификация — RuleBasedSemanticClassifier через SemanticClassifierPort. Поля semantic values не суммируются до единицы и не заменяют DisciplineAreaWeight. Canonical Discipline с глобальным normalized identity не переписывается сразу: curriculum-item semantic override является обязательным уточнением для одинаковых имён в разных планах; identity split остаётся отдельным compatibility decision. Persistent projections обновляются post-ingestion для affected programs и отдельно отмечают projection failure, не откатывая canonical transaction. Admission Fit остаётся отдельным существующим engine; conversation собирает applicant slots и передаёт typed batch request, а analytics filter использует allow-listed adapter. Существующие comparison/recommendation/decision contracts сохраняются, а ProgramFingerprint становится compatibility alias на analytics projection. Telegram сначала получает общий assistant HTTP contract; resolver/session/response selection постепенно выносятся из Telegram, без второго domain engine.
Risks: Нынешний ProftestCatalogService пересчитывает fingerprints из всего каталога в runtime, а recommendations и decision напрямую используют proftest contract; перенос ownership может сломать compatibility и architecture allowlist. Comparison независимо повторяет hours→credits и area aggregation. Текущая дисциплина глобально уникальна по normalized_name и curriculum item не имеет собственной provenance/semantic таблицы. Post-ingestion projection failure может дать canonical/analytics version skew. QuerySpec может стать обходом безопасности, если validation не будет registry-driven и bounded. Telegram сейчас кэширует полный catalog, хранит только cookie session и сам выбирает text/PNG; миграция должна сохранить callback/session security и OG HMAC boundary. 5,000 программ и 100,000 curriculum items требуют batch repositories/indexes и запрета N+1.
Open questions: Нужен ли в следующем этапе отдельный identity model для одинаковых дисциплин по university/program context, или curriculum-item override достаточно для первой projection version; должен ли QuerySession храниться по anonymous ProfileScope или отдельным owner key; какой production scheduler/runner будет вызывать rebuild после ingestion; будет ли PDF HTML renderer размещён в backend presentation adapter или в Next report route; какие дополнительные semantic features и aliases должны пройти manual review до production rollout.
Success signals: Existing regression/architecture/OpenAPI tests remain green; a fixture ingestion creates semantic rows and persistent projections; one bounded SQL query answers metric comparison without rebuilding fingerprints; missing basis produces explicit insufficient status; evidence can traverse metric → item → semantic classification → canonical/source snapshot; unsupported metrics and ambiguous entities fail typed; deterministic scenarios A–H work without Jev; Telegram remains HTTP-only and can consume ResponseEnvelope; MAX can later reuse the same API without importing backend modules.
Next step: Зафиксировать evidence-backed execution plan по фазам с отдельными migration/projection rollout checkpoints и approval gate перед implementation.
<!-- aif:active-summary:end -->

## Sessions
<!-- aif:sessions:start -->
### 2026-09-21 18:20 — Repository audit for universal analytics boundary
What changed:
- Проверены `.ai-factory` context, project rules, README, architecture/API/Telegram docs, current branch/status/history и Graphify reports.
- Прослежены ingestion adapters/contracts, canonical persistence, discipline taxonomy/classifier, curriculum/program repositories, proftest fingerprint/catalog, recommendations, comparison, admission_fit, DecisionCandidatePipeline, composition root, API routes, Telegram resolver/state/render client и Next OG routes.
Key notes:
- Graphify backend report: 2189 nodes, 6057 edges, no detected import cycles; current graph built from commit `2026fe18`.
- Canonical flow фактически проходит `RawTracerBundle → CanonicalSnapshot → SqlAlchemyIngestionRepository` с source snapshots/raw records и atomic canonical transaction; `IngestRunModel` уже содержит projection lifecycle metadata.
- `DisciplineAreaCode`/`DisciplineAreaWeight` — 22-area mutually-exclusive distribution; `RuleBasedDisciplineClassifier` хранит audit outcome, но semantic feature layer отсутствует.
- `ProgramFingerprint` и `FingerprintBuilder` принадлежат `modules/proftest`; `ProftestCatalogService` строит их из canonical catalog, `CatalogRecommendationRepository` и `CatalogDecisionCandidateSource` используют этот runtime path, persistent metrics отсутствуют.
- `area_distribution()` и `CompareProgramsService` независимо повторяют workload basis/area aggregation; `ComparisonSummaryService` строит summary только для 2–3 program IDs.
- `ProgramResolver` находится только в Telegram и загружает полный `/programs` catalog; generic resolver, QuerySession, `/analytics/query`, `/assistant/query`, ResponseEnvelope и policy ports отсутствуют.
- Telegram flow сам решает, когда текст или OG PNG; Next `/og/*` routes сами вызывают backend и рендерят Satori/ImageResponse. PDF parsing есть только в ingestion, report renderer отсутствует.
Links (paths):
- `backend/src/andromeda/ingestion/contracts/raw.py`
- `backend/src/andromeda/ingestion/contracts/normalized.py`
- `backend/src/andromeda/infrastructure/repositories/ingestion.py`
- `backend/src/andromeda/modules/disciplines/domain/areas.py`
- `backend/src/andromeda/modules/disciplines/services/classifier.py`
- `backend/src/andromeda/modules/proftest/domain/entities.py`
- `backend/src/andromeda/modules/proftest/services/fingerprint.py`
- `backend/src/andromeda/modules/proftest/services/catalog.py`
- `backend/src/andromeda/modules/comparison/services/aggregation.py`
- `backend/src/andromeda/modules/comparison/services/compare_summary.py`
- `backend/src/andromeda/modules/decision/services/candidates.py`
- `backend/src/andromeda/composition/container.py`
- `telegram-bot/src/andromeda_telegram/parsing/program_resolver.py`
- `telegram-bot/src/andromeda_telegram/flows/telegram.py`
- `frontend-next/src/app/og/*/route.tsx`
<!-- aif:sessions:end -->
