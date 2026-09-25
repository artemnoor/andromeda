# Phase 06: Dependencies, semantic diff и impact

Plan: [index.md](index.md)
Tasks: 15-17
Depends on: Phase 05

## Цель

Add typed relational edges and rebuildable diff/impact projections on PostgreSQL. Use graph semantics without graph database or canonical per-user answer storage.

## Текущие точки интеграции и переиспользуемый код

- Ingestion post-commit derived-refresh pattern and SqlAlchemyDerivedRefreshAdapter.
- Analytics evidence/gap/provenance result patterns and canonical IDs.
- DecisionContext can be read for an explicit user query, never mutated by policy refresh.
- Semantic version/rebuild patterns, not curriculum feature ontology.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-15"></a>

## Task 15: Задать типизированные relation и dependency contracts

### Контракт выполнения

- Файлы: modules/knowledge/contracts/relations.py; modules/policy/contracts/dependencies.py; owning models/repositories/migration; architecture and PostgreSQL tests.
- Normalize: knowledge owns evidence/claim relations SUPPORTED_BY, CONTRADICTS, CLARIFIES, DERIVED_FROM. Policy owns APPLIES_TO, EXCEPTION_TO, OVERRIDES, SUPERSEDES, AMENDS, IMPLEMENTS, REQUIRES. AFFECTS is derived impact output, not canonical legal edge.
- Edge data: stable ID, typed endpoints, relation kind, source evidence or human actor, recorded/valid interval when relevant, review state; FK/unique/idempotency constraints. Provenance on each edge.
- Cardinality: one SourceObservation may yield many Claims; each Claim asserts from one observation but can have multiple precise locators; one logical ChangeCandidate may link many Claims and source observations; each Relation row has exactly one typed subject and one typed target plus provenance references; one ReviewItem targets one candidate revision at a time. An absent edge is allowed and is not a negative relation.
- Safety: endpoint-kind registry; reject self-edge and cycles in precedence/dependency subgraphs; initial traversal depth 8 and at most 1000 nodes, with explicit truncation.
- Будущие тесты: allowed endpoint matrix, duplicate insertion, cycles, temporal scope, traversal cap and indexes.
- Критерии приёмки: no implicit JSON link list; every edge is typed, attributable and owned by one context.
- Будущая проверка: python -m pytest backend/tests/architecture/test_module_boundaries.py backend/tests/integration/test_knowledge_relations.py
- Зависимости: Tasks 3, 7 and 13.
- Откат: disable traversal, retain audit records.
- Риски: generic edges hide bad semantics; enforce registry and endpoint combinations.
- Вне scope: graph database or arbitrary path-query API.

<a id="task-16"></a>

## Task 16: Формировать semantic diff до approval

### Контракт выполнения

- Файлы: knowledge/policy diff contracts and services; revision repository queries; review DTO; unit fixtures.
- Diff layers: source bytes; parsed fields; typed claim; candidate versus canonical object; policy selector/domain references/scope/time/approval; effective rules by context; impact and `ResolutionTrace`. Include before/after values, field evidence, locator and uncertainty. Text-only document diff is insufficient.
- Шаги: compare normalized typed values with stable canonical IDs; identify added/removed/changed/incomparable fields; attach evidence per field; version diff schema.
- Ошибки и логирование: missing old version is incomplete, not deletion; parser version change is visible; do not store applicant PII.
- Будущие тесты: minimum 75 to 80; all-program to A/B/C scope; BVI to 100 points; explicit removal vs missing source; AST schema migration.
- Критерии приёмки: reviewer sees diff pre-approval and can reproduce canonical/effective diff from stored versions.
- Будущая проверка: python -m pytest backend/tests/unit/test_policy_diff.py backend/tests/integration/test_knowledge_diff.py
- Зависимости: Tasks 9, 13 and 15.
- Откат: old source/canonical versions remain readable; output is versioned.
- Риски: normalization can hide distinctions; retain source claim and normalization explanation.
- Вне scope: AI narrative as evidence.

<a id="task-17"></a>

## Task 17: Вычислять bounded impact и incremental refresh

### Контракт выполнения

- Файлы: modules/policy/contracts/impact.py; services/impact_analyzer.py and dependency_refresh.py; repository ports; targeted infrastructure refresh adapter; tests.
- Derived chain: changed source/candidate → claims → canonical domain owner → dependencies → programs/olympiad profiles/admission contexts → decision metric/result. Projection is rebuildable and tagged with policy version, input revisions and calculated time.
- ImpactPreview compares current approved policy against a simulated candidate; returns affected canonical IDs, old/new typed domain-owner results, mandatory current/candidate ResolutionTrace references, affected dimensions, evidence and missing inputs. Do not persist every applicant profile's impact or mutate DecisionContext/shortlists.
- Actionability values: NOT_APPLICABLE, FUTURE_ONLY, INFORMATIONAL, ACTION_RECOMMENDED, ACTION_REQUIRED, UNCERTAIN, BLOCKED_BY_MISSING_DATA. Give a reason; no emotional worry classifier.
- Refresh: changed approved canonical revision marks only reverse dependencies dirty; idempotently run after canonical commit; failed refresh exposes stale/version skew. Impact explanation consumes the same typed resolver trace; it does not reconstruct precedence independently.
- Ошибки и логирование: cap returns partial/truncated; missing dependency is unknown; projection failure does not rollback canonical transaction; no profiles in logs.
- Будущие тесты: exam impacts only mapped cohort; olympiad→profile→program; achievement change; idempotent targeted rebuild; stale marker; what-if without mutation.
- Критерии приёмки: deterministic current-vs-candidate impact; isolated change avoids full catalog rebuild.
- Будущая проверка: python -m pytest backend/tests/unit/test_policy_impact.py backend/tests/integration/test_policy_dependency_refresh.py
- Зависимости: Tasks 12-16 and admission/benefits adapters.
- Откат: disable impact projection and return explicit unavailable; canonical rules remain.
- Риски: stale projection and missing edge; gate rollout on completeness and full-rebuild reconciliation.
- Вне scope: global recommendation reranking or notification fan-out.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
