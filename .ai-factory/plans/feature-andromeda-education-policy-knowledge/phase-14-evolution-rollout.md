# Phase 14: Backfill, rollout, compatibility и documentation

Plan: [index.md](index.md)
Tasks: 36-39
Depends on: previous phases and release approval

## Цель

Evolve current vertical slices additively from the reconciled Stage 2 baseline. Ship each schema slice with its first persistence/write path; do not defer the approval ledger or all migrations until this final phase. This phase verifies the complete migration chain, compatibility/backfill and staged rollout; rollback remains non-destructive.

## Текущие точки интеграции и переиспользуемый код

- Clean Stage 2 baseline is `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`; Alembic head is `0038_admission_offering_scope_and_exam_choices`.
- Revisions 0036-0038 already add benefit coverage/source gaps, confirmation applicant category, campus scope and exam choice groups; existing `SourceSnapshotModel`, `IngestRunModel`, benefit tables and provenance stay owned by their current modules.
- Stage 2 `backend/alembic/env.py` already sizes `alembic_version.version_num` for the longest revision identifier.
- AndromedaContainer composition root and current feature behavior.
- Root ROADMAP.md exists but has no policy intelligence milestone; configured .ai-factory/ROADMAP.md was absent in research.
- Existing plans for universal analytics, admission benefits, Jev Stage 2, admin ops and university admin are historical/design inputs; checkout state is authoritative.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-36"></a>

## Task 36: Согласовать clean baseline и порядок additive migrations

### Контракт выполнения

- Файлы: additive Alembic revisions after verified deployed/code head; `infrastructure/database/models/knowledge.py`, policy models and admissions cycle models; migration/repository tests and database docs.
- Шаги: implementation starts from the clean Stage 2 worktree in Phase 00. Current code parent is 0038; verify deployed head before each migration batch. Add strict successors (expected first new revision 0039 only if 0038 is still the current single head); never edit applied revisions. Stage 2 migration history is part of the baseline, not a future merge.
- Data plan/order: (1) versioned source registry/observations reference existing snapshot hashes and ingest runs; (2) bitemporal claim/change revisions and evidence links; (3) approval-decision ledger exists before/with the first PolicyRuleRevision/RuleCandidate writer and before enabling the resolver; (4) policy references/scopes/conflicts/dependencies; (5) admissions-owned cycle mapping and rebuildable projections as required. Keep boundaries relational/typed and AST/extraction JSONB bounded. Never recreate `source_snapshots`, benefit coverage, benefit scopes, campus/offering identity or exam-choice groups.
- Approval migration invariant: resolver deployment is blocked unless the deployed ledger proves an explicit decision for the exact immutable revision hash. Candidate writes may begin only after pending/approved/rejected audit state is durable; full review UI is not required to enforce the gate.
- Будущие тесты: upgrade empty/populated supported PostgreSQL DB from 0038; migration-head/branch parity; approval FK/immutability constraints; existing Stage 2 0036-0038 and full-chain migration integration suite; downgrade only in disposable CI DB.
- Критерии приёмки: one linear Alembic head on selected implementation branch, no dropped legacy columns/IDs, source snapshot references remain valid, resolver rejects unapproved rows, startup/backfill/old Stage 2 APIs still work.
- Будущая проверка: alembic heads/history/current and migration integration suite.
- Зависимости: all contracts stable and Phase 00 gate.
- Откат: forward-compatible flag disable; no production downgrade that destroys audit history.
- Риски: deployed databases may not yet be at code head 0038 or may contain drift; inspect before choosing the actual parent and preserve a safe forward-only upgrade path.
- Риски: Stage 2 active benefit data has no generic approval event. Never infer approval from `ACTIVE`; keep the existing evaluator path until explicit per-revision adoption is audited.
- Вне scope: migration implementation during current planning turn.

### Результат выполнения Task 36

- Confirmed a single linear Alembic head `0054_claim_predicate_lookup_index`, descending directly from Stage 2 head `0038_admission_offering_scope_and_exam_choices`; revisions 0039–0054 are additive and applied only after 0038. Added a SQLite regression that upgrades to Stage 2 head, inserts an existing-format ingest run and immutable source snapshot, then upgrades to 0054 and asserts both the snapshot/hash and policy approval tables survive. The targeted test passes. PostgreSQL upgrade/constraint parity is still a deployment gate because a usable PostgreSQL test DSN is unavailable locally.
- `test_clean_stage2_head_upgrades_additively_to_one_current_head` passed (**1 passed**); `uv run alembic heads` reports exactly `0054_claim_predicate_lookup_index`.

<a id="task-37"></a>

## Task 37: Backfill recoverable provenance и сохранить legacy contracts

### Контракт выполнения

- Файлы: one-shot/idempotent backfill command under backend/scripts or owner repository service; read-only report; docs/data migration tests.
- Rules: backfill existing benefit/admission source attribution only when Stage 2 source snapshot/locator/hash is present; set unknown source identity, publication/adoption/effective date or system history when unavailable. Do not infer new approval from `RuleDataStatus.ACTIVE` or release-gate pass; explicit human adoption writes approval events for exact rule revisions only. Do not invent policy lifecycle, source trust, legal dates or relations. Keep legacy contracts readable and stable.
- Шаги: dry-run count/sample; field-level provenance coverage report; execute bounded batches with checkpoint/idempotency; verify count/hash and old-vs-new benefit result parity; emit redacted operator audit.
- Будущие тесты: replay idempotency, partial resume, unknown preservation, legacy query parity, source hash link integrity.
- Критерии приёмки: no fabricated history; every migrated record reports coverage/gaps; existing API behavior unchanged until explicit switch.
- Будущая проверка: migration/backfill integration suite on anonymized representative DB.
- Зависимости: Task 36, source provenance model and benefit adapter.
- Откат: stop batch, retain source rows, mark backfill version; corrective forward command only.
- Риски: untracked local user data may not represent production; use a separately approved sanitized baseline.
- Вне scope: converting every catalog record into a universal Fact.

### Результат выполнения Task 37

- No historical generic approval, policy lifecycle or revision boundary can safely be inferred from Stage 2 `ACTIVE` rows. Did not perform a backfill. Added `scripts/report_knowledge_provenance.py`, which is SELECT-only and reports existing benefit source snapshot/run/locator coverage and gaps without inventing trust or legal dates; empty database behavior is covered by a test. Existing admissions offering and benefit contracts remain readable, and exact owner revisions are appended by future successful syncs.
- The inventory command was tested against an empty SQLite database only; run it against the approved sanitized production snapshot before deciding whether any owner-specific source attribution repair is justified.

<a id="task-38"></a>

## Task 38: Включать rollout по capabilities и мониторить parity

### Контракт выполнения

- Файлы: `Settings`, `.env.example`, `AndromedaContainer`, assistant policy-query gate and knowledge operations runbook.
- Rollout order: additive schema; allowlisted source observations/candidates; immutable approval gate; authenticated review; candidate diff/impact; approved-only resolver; domain-owner adapters; assistant verified mode; optional verbalizer last. `ANDROMEDA_KNOWLEDGE_POLICY_ASSISTANT_ENABLED` defaults false and gates assistant claim reads/resolution; source registry is empty/disabled by default, source polling is one-shot/manual, and reviewer/steward account allowlists default empty. Jev flags remain unchanged/off. Production enablement and parity monitoring require deployment owners and are not performed by this implementation.
- Monitor before widening: migration errors, source capture/parser failure, review queue age, conflict count, stale dependency projection, old/new resolver mismatch by context, API latency, Jev calibration and fallback. Stop rollout on unexplained policy mismatch.
- Compatibility: old endpoints/contracts continue; generated OpenAPI is additive; Telegram/Web/MAX call same assistant seam and never evaluate rules.
- Критерии приёмки: each stage has parity/rollback evidence; existing catalog/curricula/analytics/comparison/admissions/benefits/admission_fit/decision/recommendations/proftest remain runnable after every release.
- Будущая проверка: run focused smoke/regression tests per flag and deployment health checks.
- Зависимости: Tasks 33-37 and release owners.
- Откат: set `ANDROMEDA_KNOWLEDGE_POLICY_ASSISTANT_ENABLED=false` for the user read path; clear the specific reviewer/steward capabilities to stop new writes. Additive schema and audit history remain; no destructive rollback.
- Риски: mixed old/new projections; surface version and fall back to explicit unavailable, not stale silent answer.
- Вне scope: deployment to production in this plan.

### Результат выполнения Task 38

- Added the fail-closed assistant rollout flag with an explicit `false` default and container wiring. When off, policy intent returns typed `outside_coverage` before any claim lookup. Added environment/default and no-read-path tests. Runbook documents separate source/reviewer capability gates, manual one-shot polling, rollback and deployment metrics. No Jev flags were modified; no production rollout or parity measurement was performed.

<a id="task-39"></a>

## Task 39: Обновить architecture, operations, API и roadmap docs

### Контракт выполнения

- Файлы: README.md; docs/architecture.md; new docs/architecture/knowledge-policy.md; docs/architecture/query-flow.md; docs/architecture/integration-seams.md; docs/admission-benefits.md; docs/semantic-analytics.md; docs/ingestion-adapters.md; docs/postgresql.md; docs/testing.md; docs/test-matrix.md; docs/api.md; ROADMAP.md. Check configured .ai-factory/ROADMAP.md path before changing/creating it.
- Document current vs target state, ownership matrix, source trust vs policy lifecycle, temporal axes, supported scopes, precedence/conflicts, evidence chain, API/channels, recovery, security limits, feature flags, Jev optional boundary, historic coverage limits and runnable test commands.
- Correct/check migration references against Stage 2 head 0038 and deployed heads; never document old 0035/0022 as current without evidence.
- Шаги: update docs alongside implemented phases; verify every link/file/symbol against final code; regenerate OpenAPI/types from source rather than hand-edit.
- Критерии приёмки: docs distinguish supported from planned capability; no architecture doc promises an unimplemented Jev, LLM, review or cycle path; roadmap ownership/date decisions explicit.
- Будущая проверка: docs link checker/manual API diff, OpenAPI drift checks and docs/testing commands.
- Зависимости: corresponding implementation complete and actual branch baseline recorded.
- Откат: documentation reverts independently; no runtime impact.
- Риски: speculative docs may become false contracts; mark future phases planned until shipped.
- Вне scope: claiming full source-backed coverage before corpus/operator staffing exists.

### Результат выполнения Task 39

- Updated the architecture/API/runbook/performance/PostgreSQL/testing/roadmap documentation to distinguish implemented, disabled-by-default and still unavailable behavior; documented migration head 0054, rollout flag, source and human capability gates, no-backfill rationale, DB validation limits, and the assistant-to-domain-owner impact gap. OpenAPI/generated frontend types were refreshed in the earlier response-contract task; this phase's config gate does not change the public schema.
- Frontend verification: `npm run test:unit` (**28 passed**), `npm run lint` passed, and `OPENAPI_FILE=openapi.json npm run check-api-drift` passed against the checked-in exported spec. Live-server drift check was unavailable because no backend was listening on `127.0.0.1:8000`.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
