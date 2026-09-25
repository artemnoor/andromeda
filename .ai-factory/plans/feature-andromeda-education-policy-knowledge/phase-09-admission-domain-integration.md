# Phase 09: Admission cycles, benefits и achievements

Plan: [index.md](index.md)
Tasks: 24-25
Depends on: Phases 05-06

## Цель

Connect temporal/effective policy selection to admissions while preserving owner and behavior of current admissions, admission_fit and admission_benefits vertical slices.

## Текущие точки интеграции и переиспользуемый код

- Stage 2 `modules/admissions` owns offerings, campus scope, exam requirements/choice groups, quotas, passing scores, costs and admission_year.
- modules/admission_fit owns applicant context and deterministic fit evaluation.
- Stage 2 `modules/admission_benefits` owns BVI/100-point Olympiad semantics, profile/level/result-year validity, confirmation/applicant category, special/targeted routes, individual-achievement policies and points, source coverage, and the sole benefit/competitive-score evaluators.
- Stage 2 migrations 0036-0038 already add benefit coverage, applicant category, campus scope and exam-choice groups; do not duplicate these structures in generic policy tables.
- DecisionContext and recommendations remain separate user decision/derived modules.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-24"></a>

## Task 24: Подключить AdmissionCycle и адаптер выбора benefit rule

### Контракт выполнения

- Files: admissions cycle DTO/repository; read-only adapter from approved policy revision references to the current admission_benefits repository/service; policy owner-rule selection port; AndromedaContainer; contract/integration tests. Add models/migrations only for genuinely missing cycle/policy linkage after checking 0038.
- Flow: typed applicant + university/program/campus + admission cycle → deterministic policy selects an exact approved current-owner rule/revision reference (or returns conflict/unknown with ResolutionTrace) → existing `AdmissionDecisionService`, `AdmissionBenefitEvaluator`, `IndividualAchievementCalculator` and `EffectiveCompetitiveScoreCalculator` determine domain applicability, eligibility and scores.
- Keep source-backed dimensions under the current benefit owner: Olympiad identity/profile/level, result-year validity, confirmation threshold and applicant category, route, competition/program/direction scope, achievement rule/policy, source coverage, special rights and quotas. Preserve current `BenefitScope` and unknown/coverage semantics; do not build equivalent BVI/100/confirmation/achievement calculations or a competing benefit applicability engine in generic policy.
- Stage 2 `BmstuAdmissionDocumentCatalog`, benefit capture/parser, coverage table (0036), release gate and repository are reused for the current BMSTU vertical. Their source-coverage/staleness gaps remain domain evidence and cannot be erased by generic policy selection.
- Шаги: record current owner outputs; require exact approval-event-backed revision for policy selection; add read-only adapter; compare fixtures; route only covered approved rows; keep current owner path until parity/reconciliation. Existing `ACTIVE` status or a release check alone is not a substitute for the new explicit per-revision approval event.
- Ошибки и логирование: multiple matching benefits become conflict; missing olympiad/confirmation stays unresolved, not “no benefit”; do not mutate DecisionContext.
- Будущие тесты: current benefits regression; BVI/100 points; olympiad profile/program; result validity; confirmation; route; missing mapping.
- Критерии приёмки: Stage 2 benefit/scoring evaluators remain sole calculators; policy returns selected owner revision refs/ResolutionTrace, while the final result points to domain rule/evidence; feature off preserves current Stage 2 API and contracts.
- Будущая проверка: python -m pytest backend/tests/integration/test_admission_benefits.py backend/tests/integration/test_admission_fit.py backend/tests/architecture/test_admission_benefits_boundaries.py
- Зависимости: Tasks 6, 11-13, 17.
- Откат: switch to existing selector; retain new history.
- Риски: existing benefit validity may overlap common rule time; define precedence before conversion.
- Вне scope: rewrite benefit schema or replace DecisionPolicy.

<a id="task-25"></a>

## Task 25: Интегрировать правила экзаменов, admissions и achievements

### Контракт выполнения

- Файлы: policy-to-owner reference adapters; admissions/admission_fit and admission_benefits ports/contracts only where required; later API schemas; vertical regression tests.
- Requirements: policy stores applicability/supersession and typed owner revision references for exam requirements/thresholds and individual-achievement changes; include federal baseline, BMSTU exception and narrower direction/program scope. No generic effect computes those requirements, eligibility or points. Every candidate maps to an existing owner contract or stays unsupported until that owner adds an approved extension.
- Шаги: integrate one vertical slice at a time; after review, normalize into the canonical owner contract/revision and link the policy revision; compare deterministic domain-owner results; remove legacy branches only after parity evidence. No unrelated cleanup.
- Ошибки и логирование: unrepresentable rule stays review-required/unsupported; no partial update; unknown program/cycle explicit; manual exception records actor and source.
- Будущие тесты: fourth exam 2028 vs applicants 2027/2028; university/direction exception; achievement point change; route/quota; exception with no evidence.
- Критерии приёмки: only matching cycle/program changes; domain owner remains the only calculator; no unapproved owner revision is selected; existing Stage 2 admissions, fit and benefits remain runnable on old paths during rollout.
- Будущая проверка: python -m pytest backend/tests/integration/test_admission_fit.py backend/tests/integration/test_admission_benefits.py backend/tests/api/test_admission_fit.py
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
