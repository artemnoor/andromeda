# Phase 01: Canonical vocabulary и ownership

Plan: [index.md](index.md)
Tasks: 3-4
Depends on: Phase 00 decisions

## Цель

Зафиксировать typed contracts и единственного владельца каждой новой canonical-сущности до миграций. Не вводить универсальную таблицу facts и не переносить ownership работающих предметных модулей.

## Текущие точки интеграции и переиспользуемый код

- modules/admissions: AdmissionOffering, ExamRequirement, Quota, PassingScore, TuitionCost и admission_year.
- modules/admission_benefits: AdmissionBenefitRule, Olympiad/Profile, IndividualAchievementPolicy/Rule, BenefitScope и существующая provenance.
- modules/ingestion: RawSourceRecord, RawSourceSnapshot, IngestRun; immutable content адресуется hash.
- modules/entity_resolution: canonical catalog IDs, exact/alias/ambiguous resolution.
- modules/semantic: versioned derived classifications, review/confidence/evidence patterns; curriculum ontology остаётся отдельной.
- modules/conversation, modules/presentation, modules/analytics: typed query/result/evidence patterns.
- Shared SourceAttribution / BenefitProvenance: расширять только после inventory сериализованных consumers.
- Stage 2 Jev: current QuestionRegistry/TypeSafe/calibration seams and bounded entity resolution; reuse these adapters and locks without duplicating them.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-3"></a>

## Task 3: Утвердить ownership vocabulary без параллельных canonical stores

### Контракт выполнения

- Файлы: создать docs/architecture/knowledge-policy.md; обновить ссылки в docs/architecture.md, docs/architecture/integration-seams.md и docs/architecture/query-flow.md.
- Существующие symbols: AdmissionBenefitRule, AdmissionOffering, SourceAttribution, RawSourceSnapshot, QuerySession, ResponseEnvelope, DecisionContext.
- Contracts: describe SourceIdentity/SourceRegistryRevision, SourceObservation, EvidenceRef, ClaimCandidate, ChangeCandidate, PolicyRuleRevision, RuleCandidate, immutable `PolicyApprovalEvent`, PolicyApplicabilityContext, EffectiveRuleResult, mandatory ResolutionTrace, ImpactPreview and ReviewItem as target DTOs.
- Approval invariant and ownership: `policy` owns its append-only, exact-hash `PolicyApprovalEvent`; `knowledge` owns ReviewItem and review-command workflow. Define the approval state machine before a rule-candidate writer exists. The same transaction that first persists a `PolicyRuleRevision`/`RuleCandidate` must append `PENDING_SUBMITTED` for that exact revision hash, attributed to its submitting actor or ingestion operation. Authorized human approve/reject/withdraw actions append later events through a typed policy command port; edits create a new hash/revision and a new pending event. Current approval state is a deterministic projection of event history, never a mutable `approved_at`; `ACTIVE` alone is not approval. Resolver v1 accepts only the exact explicitly approved revision.
- Шаги: сверить понятия с public contracts; закрепить единственного owner для каждой сущности; разделить source assertion, approved domain data, policy lifecycle и derived output; обозначить решения, требующие human approval.
- Ошибки и логирование: отсутствие свидетельства означает UNKNOWN/INSUFFICIENT_DATA, не false/zero; конфликт нельзя разрешать выбором строки. Audit не включает полный applicant profile или секреты.
- Будущие тесты: contract ownership inventory, запрет ORM/FastAPI imports из subject modules, JSON serialization compatibility.
- Критерии приёмки: ownership matrix index содержит owner, canonical/derived, writer, readers, persistence owner для Source, SourceSnapshot, Claim, Fact, Relation, Rule, RuleCandidate, ChangeEvent, EffectivePolicy, ReviewItem, Impact, UserRelevance, QuerySession и ResponseEnvelope; ни у одной canonical-сущности нет двух owners.
- Будущая проверка: python -m pytest backend/tests/architecture/test_module_boundaries.py backend/tests/architecture/test_layer_directions.py
- Зависимости: human decisions in Phase 00 Task 2.
- Откат: до runtime изменений можно уточнить только architecture docs.
- Риски: Fact может ошибочно пониматься как новая универсальная сущность; в плане это source-backed assertion/поле, принадлежащее предметному модулю.
- Вне scope: таблица KnowledgeObject/Fact, перенос ownership catalog или benefits, graph DB.

<a id="task-4"></a>

## Task 4: Описать module boundaries, public ports и lifecycle contracts

### Контракт выполнения

- Файлы: docs/architecture/knowledge-policy.md, docs/architecture/integration-seams.md, docs/architecture/query-flow.md, docs/semantic-analytics.md.
- Proposed modules: ровно два новых logical bounded contexts: modules/knowledge/{domain,contracts,services,repository} для source registry/observations, claims/evidence/change candidates and immutable approval audit; modules/policy/{domain,contracts,services,repository} для typed policy revisions, applicability, deterministic resolution/trace and dependency semantics.
- Existing modules remain owners: admissions, admission_benefits, catalog/programs, conversation/presentation and ingestion retain their data and responsibilities.
- Do not add: separate change_intelligence, review or knowledge_entity_resolution; general-purpose object registry.
- Ports: knowledge source-observation/candidate/review-command ports; policy candidate-submission/approval-audit/approved-effective-rule/candidate-preview/dependency/trace ports. The Knowledge review workflow invokes policy approval through a typed port; it does not own or write policy approval rows. Subject modules do not import SQLAlchemy, FastAPI, Jev SDK or university parsers.
- Шаги: draw dependency direction; identify cross-module typed contracts; confirm benefits evaluator remains sole benefit calculation engine; document anti-corruption adapter between existing benefit rules and common temporal/effective selector.
- Reuse `SemanticReviewWorkflow` only for proposal-hash, source-hash freshness, actor/time, reviewed-artifact and diff-report invariants. Its curriculum semantic tables and artifacts do not become generic policy review persistence or the effective-policy approval gate.
- Ошибки и логирование: unknown contract version or ambiguous reference returns typed fail-closed result; never coerce canonical IDs.
- Будущие тесты: module dependency graph and sole composition-root guard.
- Критерии приёмки: module design fits AndromedaContainer and each new module owns one repository boundary; existing product vertical slices remain intact.
- Будущая проверка: python -m pytest backend/tests/architecture/test_module_boundaries.py backend/tests/architecture/test_composition_root.py
- Зависимости: Task 3.
- Откат: clarify docs before public contract/migration rollout; later API changes must be additive.
- Риски: knowledge can become a god module; restrict it to source assertions, evidence, change intake and review workflow.
- Вне scope: generic CRUD for every domain, physical service deployment.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
