# Phase 13: Regression, evaluation, security и performance gates

Plan: [index.md](index.md)
Tasks: 33-35
Depends on: all runtime phases before broad rollout

## Цель

Close end-to-end behavior with golden scenarios, migration/repository/architecture/E2E coverage, Jev evaluation gates, and measured operational/security limits.

## Текущие точки интеграции и переиспользуемый код

- backend/tests architecture, contract, PostgreSQL, integration and API suites.
- docs/test-matrix.md, docs/testing.md, Alembic migration tests, OpenAPI drift checks.
- Existing ingestion fetch/PDF security controls and Jev eval/calibration path if integrated.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-33"></a>

## Task 33: Добавить golden scenarios и temporal/conflict regression

### Контракт выполнения

- Файлы: fixtures and tests across backend/tests/unit, contracts, repositories, integration, API/e2e; use existing organization.
- Mandatory scenarios: A rumor; B official proposal; C adopted future rule vs 2027; D applicable 2028 applicant; E university exception; F direction exception; G Olympiad BVI/100 points; H individual achievement change; I supersession; J authoritative conflict; K source disappears but snapshot remains; L duplicated news; M unknown exception returns insufficient data; N what-if does not mutate canonical state.
- Add vertical chain: allowlisted official document → SourceSnapshot → parsed Claim → pending rule candidate plus exact-hash `PENDING_SUBMITTED` event → authorized human `APPROVED` event → approved-only resolver/ResolutionTrace → existing domain-owner evaluator → assistant impact question → deterministic ResponseEnvelope/provenance. Assert that the pending revision never enters the effective resolver and that the personalized result comes from the existing owner evaluator; do not substitute generic policy calculations.
- Layer tests: unit temporal/status/precedence/DSL; contract serialization; PostgreSQL uniqueness/FK/index/migration; architecture boundaries; ingestion-to-review integration; assistant/API/OpenAPI and channel-neutral E2E.
- Failure coverage: proposal not effective; resolver rejects missing/stale/non-approve approval events; trace includes rejected candidate and reason; unresolved conflict does not emit eligibility; absent data never becomes false/zero; unknown scope; cycle missing; Jev fails closed.
- Критерии приёмки: all A-N pass on supported PostgreSQL and API stack; Stage 2 migration/API/Jev-boundary/evaluation/admission/conversation regression suites plus catalog/curriculum/comparison/fit/benefit/proftest/recommendation/decision/assistant flows remain runnable.
- Будущая проверка: focused pytest modules per phase, then documented backend test-matrix command; run only during implementation.
- Зависимости: feature phases 02-12.
- Откат: preserve old regression suite as gate; do not weaken or suppress failures.
- Риски: fixture truth can drift; every legal fixture carries source, capture, locator and review decision.
- Вне scope: treating generated model output as golden truth.

### Результат выполнения Task 33

- Added and passed the source-backed BVI vertical regression in `tests/infrastructure/test_knowledge_candidate_repository.py`: captured official snapshot → typed Olympiad claim → exact policy revision and pending audit → human approval → approved-only resolver trace → actual `AdmissionBenefitsPolicyEvaluationService` → existing `AdmissionDecisionService` eligibility result → deterministic assistant `ResponseEnvelope` with source locator. The companion exam scenario proves the exact pending revision is absent from resolution before approval. Existing A–N focused regressions cover proposal/future applicability, exceptions, conflicts, absent data, supersession, duplicate observations and what-if isolation.
- Final full backend command `uv run pytest -q --tb=short` → **1095 passed, 10 skipped, 164 warnings** in 944.52s after installing the locked dev/evaluation/Jev/browser extras. The 18 tests previously blocked by absent optional Jev dependencies passed on rerun. PostgreSQL integration scenarios were separately run on an isolated loopback-only PostgreSQL 17 cluster: **8 passed** across admission benefits, ingest repeatability/concurrency, API smoke and user-profile persistence; these exercise migration-to-head at `0054_claim_predicate_lookup_index`. The repeatability test now checks its own inserted-row delta and remains valid when a dedicated test database contains prior fixtures.
- Full production-deployment load, representative PostgreSQL EXPLAIN at target volume, and p95 measurements remain deployment/pilot measurements; they are not inferred from the ephemeral regression database. All other security, architecture, OpenAPI, Jev-gate and migration regressions in the backend run passed.

<a id="task-34"></a>

## Task 34: Поставить fail-closed Jev evaluation gates

### Контракт выполнения

- Файлы: extend existing Stage 2 `backend/evals/jev/` harness/manifests/report scripts and CI/release documentation; keep Jevcal/calibration policy operation-scoped.
- Corpus requirements are specified in Task 22: 500 deterministic golden synthetic matching cases per production-used matching operation, independently authored labels before inference, ambiguity/adversarial/paraphrase/typo strata. Existing Stage 2 corpora and locks are not reused as ground truth for new operations.
- Promotion metrics include hallucinated relations, false MATCH, false NO_MATCH, unresolved recall, incorrect override, incorrect scope and incorrect temporal applicability; decision thresholds signed off before model run.
- Tests: regression corpus across model/prompt/provider; separate new operation/definition lock artifacts; do not modify existing Stage 2 calibration locks; no promotion on missing labels, threshold regression, timeout spike or unsupported candidate.
- Критерии приёмки: Jev remains optional and shadow/off until thresholds and owner approve; this plan never enables Jev flags or changes current locks; deterministic behavior never depends on evaluation service availability.
- Будущая проверка: integrated Jev eval command and CI dry run.
- Зависимости: Tasks 21-23 and designated evaluation owner.
- Откат: calibration lock disables operation without database rollback.
- Риски: metric averages can hide a dangerous stratum; gate each safety metric/stratum.
- Вне scope: automatic threshold relaxation.

### Результат выполнения Task 34

- Reused the Stage 2 Jev evaluation harness via `backend/evals/jev/manifests/knowledge-policy-gates.v1.json` and its test. It registers no production policy operation; Jev policy prediction/shadow/assisted flags remain off and no calibration lock was edited. Existing olympiad matching cases are not treated as policy ground truth. New Jev policy promotion remains gated on the independently authored 500-case corpora and safety metrics specified in Task 22.
- The new policy gate test module passed in the final regression run; no Jev operation was promoted or enabled.

<a id="task-35"></a>

## Task 35: Задать security, performance и operational budgets

### Контракт выполнения

- Файлы: ingestion/API security docs, repository query plans, indexes/migration, structured logging configuration, ops runbook and load fixtures.
- Threat model: SSRF/redirect rebinding, malicious/oversize PDFs, decompression/parser exhaustion, unsafe rendered text, secret leakage, unauthorized review, replay, race on approval, DSL execution injection.
- Controls: reuse allowlist, DNS/public-IP validation and recheck per redirect, byte/page/time caps, MIME signature validation, no arbitrary URLs, role+scope auth, CSRF/session protections where web applies, immutable audit, idempotency, no eval/exec.
- Data model/indexes: composite btree by source/capture, claim/canonical identity and recorded time, review status/created, rule ID/revision/lifecycle, scope keys, valid/system time and admission cycle. Add GIN or range indexes only after representative EXPLAIN evidence. JSONB only for bounded AST/extracted payload; keep query keys relational.
- Scale: dozens of universities, thousands of programs, tens of thousands of documents, hundreds of thousands of facts/relations. Bound page sizes and graph traversal; batch loads avoid N+1. No premature billion-object/materialized graph design.
- Observability: counts/lag/failures by parser/review status, refresh staleness, conflict queue age, API latency/query count, Jev calibration only; no secrets/body/profile in logs.
- Будущие тесты: adversarial ingestion/API security; authorization; rate/size limits; representative Postgres EXPLAIN; bounded graph query; query count; refresh recovery.
- Критерии приёмки: budgets documented and met on representative corpus; sensitive-data review; no unrestricted host fetch or executable rule payload.
- Будущая проверка: pytest security/repository tests plus representative PostgreSQL load/EXPLAIN runbook.
- Зависимости: model/API/ops settled.
- Откат: reduce page/graph limits or disable ingestion/review endpoints; additive indexes can stay.
- Риски: premature index proliferation and test-only SQLite gaps; Postgres integration tests are authoritative for DB behavior.
- Вне scope: distributed cache, Kafka or optimization for billions of rows.

### Результат выполнения Task 35

- Added `scripts/profile_queries.py` cases for registry polling and approved-revision scans, batch-loaded approved revision approval/provenance associations (bounded 6 SELECTs for 3 revisions), and a regression test for query count. Added a read-only Stage 2 benefit provenance inventory command and an operations runbook with fetch/parser/traversal/poll bounds, auth/SSRF/audit and recovery rules. A disposable PostgreSQL 17 temp-table profile copied the live claim schema/indexes and ran the current bounded predicate/as-known lookup over 200,000 synthetic unreviewed claims (2,000 matching BVI claims): 271.492 ms on this workstation; the plan used the predicate index but the latest-revision aggregate performed a sequential scan and an external merge sort (16,864 kB disk). This is a useful pre-pilot signal, not a production p95/SLA: the fixture is synthetic and local, and no signed latency threshold exists. `docs/performance.md` keeps production-scale PostgreSQL load/p95 as deployment measurements; the integration suite separately verifies Alembic migration-to-head and PostgreSQL-backed existing product slices.
- Targeted candidate/provenance repository tests passed; Ruff passes on the changed Jev adapter and regression tests. After the locked optional extras were installed, repository-wide `uv run mypy` passed with **678 source files checked**. The Stage 2 Jev-align imports remain deliberately treated as untyped optional SDK seams using narrow `import-untyped` ignores. PostgreSQL 17 integration and Alembic upgrade tests passed as recorded under Task 33; representative load/EXPLAIN/p95 remain a deployment measurement, not a SQLite claim.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
