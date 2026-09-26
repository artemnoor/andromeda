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

### Выполнение Task 15

- Knowledge owns KnowledgeClaimRelationRevision: exact source/target claim revisions, stable endpoint identity, immutable content hash/revisions, optional half-open valid interval, review state and 1–64 source evidence locators. CONTRADICTS has canonical symmetric endpoint ordering; self links and duplicate evidence are rejected.
- Added knowledge_claim_relations and knowledge_claim_relation_evidence plus additive migration 0047_typed_knowledge_relations. Composite claim-revision FKs, immutable revisions, uniqueness/check constraints, provenance FKs and endpoint/review/time indexes keep storage relational and auditable.
- Added KnowledgeRelationRepository and SQLAlchemy adapter. It accepts only candidate/unresolved state until a reviewer event capability exists, validates endpoint existence/knowledge time, allowlisted captured evidence, valid-time intersection and bounded DERIVED_FROM cycle checks. Canonical reads explicitly require APPROVED, so proposed edges are not effective dependencies.
- Policy reuses PolicyRuleRelation and policy_rule_relations; added only the REQUIRES edge kind, exact target approval checks and bounded directed cycle validation. Precedence ignores REQUIRES because a dependency does not decide rule precedence. APPLIES_TO is a typed edge derived from PolicyScope, and IMPLEMENTS from DomainRuleRef; neither duplicates canonical revision fields in another table. AFFECTS remains a derived impact output.
- Added typed policy dependency nodes/edges and deterministic traversal output with edge IDs, cycles, stable ordering, explicit truncation and hard depth 8/node 1000/input-edge 10000 bounds.
- Files: knowledge relation public contracts and port; infrastructure/database/models/knowledge_relations.py, relation repository and exports; policy dependency contracts/traversal; additive Alembic 0047_typed_knowledge_relations; repository/migration/unit tests.
- Verified: policy dependency/typed relation/migration focus 4 passed; knowledge candidate repository, policy applicability/temporal, conversation policy and architecture boundaries 36 passed; Ruff and focused Mypy passed. Migration test upgrades an empty SQLite database to the new head.
- Human approval transitions for edges remain intentionally deferred to Tasks 18–20; current persistence cannot mark a candidate edge approved without that capability.

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

### Выполнение Task 16

- Existing source-byte/observation diffs and exact claim-cluster diffs remain in Knowledge ownership. Added policy-diff.v1 contracts and deterministic builders for exact policy revisions and effective sets from two immutable ResolutionTrace.v2 values.
- Revision projection compares selector schema/nodes, owner-rule references, scope, family/authority, lifecycle, bitemporal and source milestones, claim references, typed relations, approval state and normalizer version. Values are canonical typed JSON scalars/fields; each changed field carries its before/after evidence references.
- Effective-set diff includes both trace IDs, context fingerprints, university/cohort/cycle and temporal axes, exact selected rule revisions/evidence, and resolved status. Conflicted traces produce AMBIGUOUS with their conflict snapshot; blocked/indeterminate traces produce INCOMPLETE. Cross-cohort comparison remains explicit because each side records its exact cohort/context.
- A missing historical revision is UNKNOWN and emits INCOMPLETE; it is never represented as REMOVED. Only caller-confirmed absence can produce added/removed fields. Parser/normalizer version changes are explicit fields. No applicant context payload or generated prose is stored.
- Domain owner semantic details enter only through owner-namespaced typed diff entries plus their exact evidence; the policy module does not interpret BVI, point totals, confirmation, or achievement semantics. This supports a 75→80 score or BVI→100-point explanation when emitted by the current domain owner.
- Files: modules/policy/contracts/semantic_diff.py, services/semantic_diff.py, public/service exports, tests/unit/test_policy_diff.py.
- Verified: unit diff/dependency suite plus knowledge repository, policy applicability/temporal, conversation policy and architecture boundaries: 43 passed; focused Ruff and Mypy passed.
- No diff table/migration is required: output is reproducible from immutable source/canonical revisions and exact resolution traces; review DTO storage is deferred to Task 20.

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

### Факт исполнения

- Добавлены `PolicyImpactPreview` и `PolicyImpactAnalyzer`: сравнивают exact current/candidate `ResolutionTrace`, ограничивают обход зависимостей, перечисляют affected typed nodes/evidence и делегируют доменную разницу только owner adapter-у. Конфликт, несовпадающий контекст, отсутствующие dependency roots, cycle, truncation и неизвестный owner result дают partial/uncertain/blocked результат. Trace IDs типизированы; policy не пересчитывает admission benefits.
- Добавлены `PolicyProjectionRefreshCommand/Record/Attempt`, порт и сервис `PolicyDependencyRefreshService`. Dirty markers строятся только из exact revisions, которые подтверждены `ApprovedPolicyRuleReader`; unapproved revisions не могут инициировать refresh. Затронутые root, owner domain rule и известные impact targets получают отдельные typed projection keys.
- Добавлены SQLAlchemy adapter и additive migration `0048_policy_projection_refresh`: generation-guarded dirty/ready/failed state, idempotent повторная инвалидация, bounded batch, retry для failed, immutable attempt ledger и отклонение результата старого поколения. Изменение canonical данных и refresh остаются разными транзакционными шагами; refresh вызывается после commit и не требует полного catalog rebuild.
- Composition exposes rule/refresh repositories и typed service factory; конкретный projection builder остаётся port-ом до появления владельцев конкретных derived projections.
- Проверки: `pytest tests/unit/test_policy_impact.py tests/unit/test_policy_diff.py tests/unit/test_policy_dependencies.py tests/infrastructure/test_policy_dependency_refresh.py tests/infrastructure/test_alembic_migrations.py tests/architecture/test_module_boundaries.py -q` — 34 passed; focused Ruff — passed; focused Mypy с `--follow-imports=silent` — passed; `git diff --check` — exit 0. Полный Mypy отдельно зависит от внешних Jev packages, зафиксированных в Task 1 baseline.
- Rollback: migration downgrade отказывает при наличии refresh history; projection consumers могут игнорировать очередь и считать результат unavailable, сохраняя canonical revisions.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
