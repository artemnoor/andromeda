# Research: Universal Educational Analytics Interface

Updated: 2026-09-21 18:20
Status: historical architecture research snapshot (2026-09-21); current implementation is authoritative
Index: [INDEX.md](INDEX.md)

> This research records the pre-Public-API implementation state. Use the current
> API and architecture documentation for runtime ownership and supported clients.

## Historical Summary (original input for /aif-plan)
<!-- aif:active-summary:start -->
Topic: Universal educational analytics and decision interface for Andromeda
Goal: Provide typed analytics and channel-neutral conversation through the existing modular monolith and stable Public API v1; future MAX clients use that API boundary.
Scope: Additive evolution over ingestion, canonical education data, admissions, Admission Fit, recommendations, comparison and decision. Semantic, analytics, entity-resolution, conversation and presentation ownership remain inside one backend; Web and future clients consume typed HTTP contracts.
Stakeholders: Andromeda users; backend/API; ingestion operators; Web and future MAX client developers; Jev policy/classifier adapters; PostgreSQL/SQLAlchemy/Alembic operators.
Constraints: Сохранить PostgreSQL, SQLAlchemy, Alembic, canonical IDs/contracts, current admissions/admission-fit/provenance/source-gap semantics и backwards compatibility. Оставить существующую 22-area taxonomy отдельно от non-exclusive semantic features. Не подключать Jev/LLM как runtime dependency; не принимать raw SQL от внешней модели; не превращать missing в zero; не создавать microservices, Kafka, Redis или AssistantService-монолит без отдельного решения. Все schema changes только Alembic. Subject modules не импортируют ORM/FastAPI/ingestion; university-specific behavior остаётся в ingestion adapters.
Requirements: Preserve versioned semantic data, rebuildable projections, bounded typed QuerySpec, explicit ambiguity, generic QuerySession, deterministic policy ports, evidence-backed ResponseEnvelope and the channel-neutral Public API v1. Keep Jev optional and do not let external models submit raw SQL or canonical facts.
Decisions: Canonical data remains source of truth; semantic data and projections are versioned, rebuildable derived data. Existing comparison/recommendation/decision and Admission Fit owners are preserved. Public API v1 is the client boundary over shared handlers. No separate transport business engine is part of the target.
Risks: Proftest/recommendation ownership, comparison aggregation, source provenance, projection rebuilds and bounded QuerySpec validation require regression coverage. The signed OG renderer remains an internal image capability; its HMAC and Public API dependencies must stay explicit. Avoid N+1 reads as the catalog grows.
Open questions: Нужен ли в следующем этапе отдельный identity model для одинаковых дисциплин по university/program context, или curriculum-item override достаточно для первой projection version; должен ли QuerySession храниться по anonymous ProfileScope или отдельным owner key; какой production scheduler/runner будет вызывать rebuild после ingestion; будет ли PDF HTML renderer размещён в backend presentation adapter или в Next report route; какие дополнительные semantic features и aliases должны пройти manual review до production rollout.
Success signals: Existing regression/architecture/OpenAPI tests remain green; analytics results stay bounded and source-backed; missing basis produces explicit insufficient status; evidence retains provenance; unsupported metrics and ambiguous entities fail typed; deterministic behavior works without Jev; all external clients use Public API v1 without importing backend modules.
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
