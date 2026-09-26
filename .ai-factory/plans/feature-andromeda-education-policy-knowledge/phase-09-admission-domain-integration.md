# Phase 09: Admission cycles, benefits и achievements

Plan: [index.md](index.md)
Tasks: 24-25
Depends on: Phases 05-06

## Цель

Connect temporal/effective policy selection to admissions while preserving owner and behavior of current admissions, admission_fit and admission_benefits vertical slices.

## Текущие точки интеграции и переиспользуемый код

- Stage 2 `modules/admissions` owns offerings, campus scope, exam requirements/choice groups, quotas, passing scores, costs and admission_year.
- The current admissions repository persists mutable current rows only. Policy exact references therefore need an additive immutable `AdmissionOfferingRevision`; `admission_fit` continues consuming current facts through its existing deterministic service.
- modules/admission_fit owns applicant context and deterministic fit evaluation.
- Stage 2 `modules/admission_benefits` owns BVI/100-point Olympiad semantics, profile/level/result-year validity, confirmation/applicant category, special/targeted routes, individual-achievement policies and points, source coverage, and the sole benefit/competitive-score evaluators.
- Stage 2 migrations 0036-0038 already add benefit coverage, applicant category, campus scope and exam-choice groups; do not duplicate these structures in generic policy tables.
- DecisionContext and recommendations remain separate user decision/derived modules.
- Current benefit snapshots retain source-hash keyed rows but do not expose a domain revision number. A generic `DomainRuleRef.owner_revision` integer alone cannot identify an immutable admission-benefit row; add an exact owner content hash to the typed reference/persistence projection before resolving or previewing benefit policy. Reuse the existing source-snapshot rows and do not add a second benefit revision store.

### Факт выполнения и ограничения Task 24

- `DomainRuleRef` now has optional exact owner content hash; new `policy-rule.v3` revisions require it, and new `admission_benefits` policy submissions reject v2 references without it. Existing v1/v2 records remain readable but benefit references without exact hashes resolve unsupported. Additive migration `0051_policy_domain_owner_revision_hash` persists the hash on policy revisions; it creates no benefit revision table and backfills no unverifiable legacy mapping.
- `admission_benefits` owns deterministic revision fingerprints over its typed source-backed rule/policy payload. Decimal and timestamp representations are canonicalized across PostgreSQL/SQLite round trips; mutable ACTIVE/STALE/review status is excluded from the content fingerprint. The infrastructure adapter fetches an exact source-backed revision through owner repository read methods and reports it available only while that owner record is ACTIVE. BVI, 100-point, validity, confirmation and achievement calculations remain in existing evaluator services.
- `AndromedaContainer.effective_policy_resolver()` composes the approved-only resolver, admission-cycle repository, and exact benefit and admissions owner readers. `policy_impact_analyzer()` composes both owner diff adapters. The Task 24 integration path resolves approved exact benefit/achievement references and passes them to the existing `AdmissionDecisionService`; BVI/100-point/validity/confirmation/achievement calculations remain exclusively in existing evaluators. Task 20 review preview and impact are implemented; neither owner adapter approves the policy revision it reads.
- Assistant-facing benefit evaluation now goes through the typed `AdmissionBenefitsPolicyEvaluationService` in the owner module. It accepts only the exact approved benefit owner set with complete source coverage and explicit completeness for relevant applicant dimensions, then delegates unchanged to the existing `AdmissionDecisionService`; missing, stale, partial, ambiguous, or mixed-owner selections fail closed. This bridge does not create a second benefit evaluator.
- Focused checks: the Task 24 integration test and combined owner-repository/source-evidence/policy-impact/module-boundary suite passed 24 tests. Focused Ruff and Mypy passed on the changed source boundary. `git diff --check` passed (only Windows LF/CRLF warnings).
- The typed owner-evaluation contract and its regression tests were added during Task 27 reconciliation; the new complete-input and fail-closed cases are recorded under Phase 10 below.

### Факт выполнения и ограничения Task 25

- Added typed `AdmissionOfferingRevision` owner contracts and a normalized content hash that excludes volatile capture/run timestamps while retaining source identity and semantic fields. `SqlAlchemyAdmissionRepository.sync()` appends an immutable revision only when the latest owner hash changes; repeated sync is idempotent, transitions receive monotonic revision numbers, and historical rows survive current-offering deletion. `get_offering_revision()` returns data only for the requested owner ID, revision and exact hash.
- Additive migration `0053_admission_offering_revisions` follows `0052_policy_approval_preview_fingerprint` and stores the JSONB/JSON snapshot plus relational program/year/hash/recorded-time indexes. No historical revision backfill is possible from the old mutable projection; existing databases get an exact owner revision after a successful source resync. Until then, owner lookup fails closed and current admissions queries remain unchanged.
- `AdmissionsPolicyRuleReader` is composed into policy resolution and impact ports. It only validates exact owner references and emits source-backed typed field diffs; it requires matching university, admission year and explicit program context, resolves each contributing source through the existing knowledge observation registry, and returns blocked/unavailable for missing, inferred or uncaptured evidence. It does not evaluate eligibility or scores. `admission_fit` remains the existing downstream calculator, and `AdmissionBenefitsPolicyRuleReader` remains the only BVI/100-point/validity/confirmation/achievement owner.
- New admissions policy submissions require `policy-rule.v3` exact owner hashes, matching the existing benefits gate. Effective selection remains approval-event gated by the existing resolver. No effects/calculator or Jev operation was added.
- Focused tests: exact owner revision/idempotency and semantic diff/context/evidence fail-closed tests, migration-head/table test, and the admissions policy v3 submission guard. The preserved admissions, fit, benefits, API, migration and architecture regressions passed (51 total). Ruff passed on all touched implementation/test files. Mypy passed on the four changed non-composition source files; composition-wide Mypy still reports only unavailable baseline Jev packages (`typesafe_sdk`, `jevcal.runtime`) in this environment.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-24"></a>

## Task 24: Подключить AdmissionCycle и адаптер выбора benefit rule

### Контракт выполнения

- Files: admissions cycle DTO/repository; read-only adapter from approved policy revision references to exact `admission_benefits` source-backed owner revisions; `DomainRuleRef`/policy owner-rule read port and persistence projection; AndromedaContainer; contract/integration tests. Add models/migrations only for genuinely missing cycle/policy linkage or exact owner-hash persistence after checking the current 0050 head; do not create a second benefit revision table.
- Flow: typed applicant + university/program/campus + admission cycle → deterministic policy selects an exact approved current-owner rule/revision reference (or returns conflict/unknown with ResolutionTrace) → existing `AdmissionDecisionService`, `AdmissionBenefitEvaluator`, `IndividualAchievementCalculator` and `EffectiveCompetitiveScoreCalculator` determine domain applicability, eligibility and scores.
- Keep source-backed dimensions under the current benefit owner: Olympiad identity/profile/level, result-year validity, confirmation threshold and applicant category, route, competition/program/direction scope, achievement rule/policy, source coverage, special rights and quotas. Preserve current `BenefitScope` and unknown/coverage semantics; do not build equivalent BVI/100/confirmation/achievement calculations or a competing benefit applicability engine in generic policy.
- Stage 2 `BmstuAdmissionDocumentCatalog`, benefit capture/parser, coverage table (0036), release gate and repository are reused for the current BMSTU vertical. Their source-coverage/staleness gaps remain domain evidence and cannot be erased by generic policy selection.
- Шаги: define a deterministic content hash over the owner's normalized immutable rule payload and bind it in `DomainRuleRef`; expose exact source-hash keyed owner reads through `AdmissionBenefitReader`; record current owner outputs; require exact approval-event-backed revision for policy selection; add read-only reader/impact adapters; compare fixtures; route only covered approved rows; keep current owner path until parity/reconciliation. Existing `ACTIVE` status or a release check alone is not a substitute for the new explicit per-revision approval event.
- Ошибки и логирование: multiple matching benefits become conflict; missing olympiad/confirmation stays unresolved, not “no benefit”; do not mutate DecisionContext.
- Будущие тесты: current benefits regression; BVI/100 points; olympiad profile/program; result validity; confirmation; route; missing mapping.
- Критерии приёмки: Stage 2 benefit/scoring evaluators remain sole calculators; policy returns selected owner revision refs/ResolutionTrace, while the final result points to domain rule/evidence; feature off preserves current Stage 2 API and contracts.
- Verification: `python -m pytest tests/infrastructure/test_admission_benefits_repository.py tests/integration/test_bmstu_admission_benefits_ingestion.py tests/integration/test_admission_fit_vertical_slice.py tests/architecture/test_admission_benefits_boundaries.py` (Task 24 covered by exact benefit-owner integration in the repository suite).
- Зависимости: Tasks 6, 11-13, 17.
- Откат: switch to existing selector; retain new history.
- Риски: existing benefit validity may overlap common rule time; define precedence before conversion.
- Вне scope: rewrite benefit schema or replace DecisionPolicy.

<a id="task-25"></a>

## Task 25: Интегрировать правила экзаменов, admissions и achievements

### Контракт выполнения

- Файлы: `modules/admissions/contracts/offering_revisions.py`, `modules/admissions/repository/ports.py`, admissions repository/models, `infrastructure/repositories/admission_policy.py`, policy repository guard and composition, migration `0053`; focused repository/adapter regressions and architecture docs. No admission-benefit calculator/API changes.
- Requirements: policy stores applicability/supersession and exact typed owner revision references for exam requirements/thresholds; individual-achievement changes continue to use `AdmissionBenefitsPolicyRuleReader` and its current owner contracts. Federal/BMSTU/direction/program precedence remains in policy revisions. No generic effect computes requirements, eligibility or points. An unrepresentable candidate remains unsupported pending an approved owner contract extension.
- Шаги: keep admissions current tables as the query source; append normalized immutable owner revisions in the same ingestion unit of work; allow policy references only to exact approved `policy-rule.v3` revisions with exact owner hashes; compare normalized typed owner fields/evidence; keep benefit/achievement calculation delegated to the current owner reader/evaluator. Do not backfill unverifiable old revision boundaries; report missing owner history until an exact source sync populates it.
- Ошибки и логирование: unrepresentable rule stays review-required/unsupported; no partial update; unknown program/cycle explicit; manual exception records actor and source.
- Будущие тесты: fourth exam 2028 vs applicants 2027/2028; university/direction exception; achievement point change; route/quota; exception with no evidence.
- Критерии приёмки: only matching cycle/program changes; domain owner remains the only calculator; no unapproved owner revision is selected; existing Stage 2 admissions, fit and benefits remain runnable on old paths during rollout.
- Verification: `python -m pytest tests/infrastructure/test_admission_policy_repository.py tests/infrastructure/test_admissions_repository.py tests/infrastructure/test_admission_cycle_repository.py tests/infrastructure/test_admission_benefits_repository.py tests/integration/test_admission_fit_vertical_slice.py tests/integration/test_bmstu_admission_benefits_ingestion.py tests/api/test_admission_fit_api.py tests/architecture/test_admission_benefits_boundaries.py tests/architecture/test_module_boundaries.py tests/infrastructure/test_alembic_migrations.py` — 51 passed.
- Зависимости: Task 24 and Phase 04 typed owner-reference selector (no domain effect registry).
- Откат: per-effect flags restore current domain behavior.
- Риски: hard-coded behavior may encode undocumented assumptions; require golden parity before removing.
- Вне scope: admission features unrelated to targeted policy questions.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
