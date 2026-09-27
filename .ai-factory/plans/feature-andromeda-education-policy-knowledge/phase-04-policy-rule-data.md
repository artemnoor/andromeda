# Phase 04: Правила как данные и typed DSL

Plan: [index.md](index.md)
Tasks: 10-11
Depends on: Phase 01 and Phase 02; candidate staging from Phase 03

## Цель

Задать минимальное versioned policy representation и deterministic selector без произвольного кода. Policy owns legal/policy applicability and selection of an approved domain revision; the domain owner/evaluator remains responsible for every domain calculation.

## Текущие точки интеграции и переиспользуемый код

- Stage 2 `modules/admission_benefits/services/evaluator.py`, `confirmation.py`, `validity.py`, `individual_achievements.py`, `competitive_score.py` and public typed `AdmissionBenefitRule`/`IndividualAchievementRule`/`BenefitScope` contracts.
- Stage 2 admissions offerings, campus scope, exam choice groups, coverage status and applicant category contracts/migrations.
- `modules/admissions` and `modules/admission_fit` remain owners of their typed records and calculations.
- modules/analytics registry/allowlist approach as validation pattern only.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-10"></a>

## Task 10: Задать bounded policy selector DSL и immutable approval ledger

### Контракт выполнения

- Files: `modules/policy/contracts/rule_ast.py` (rename to selector/applicability AST if clearer); `domain/rule.py` and `field_registry.py`; `PolicyApprovalEvent`/submission-command contracts and repository port; `docs/architecture/knowledge-policy.md`; SQL models for versioned rule revisions and immutable policy-approval events.
- AST v1 is a bounded selector, not an eligibility calculator: versioned typed predicates over policy applicability context (registered jurisdiction, scope, cycle, valid/system time and typed domain references) plus `DomainRuleRef(owner_module, canonical_rule_id, owner_revision)`. It may choose/return a source-backed domain revision; it may not contain per-applicant benefit calculations or effects such as `grant_bvi`, `grant_100_points`, `set_achievement_points`, `confirm_exam`, or point arithmetic.
- Domain routing: `PolicySelection` is sent to the owning typed port. `admission_benefits` remains the only evaluator for BVI, 100-point Olympiad benefit, confirmation thresholds, Olympiad-result validity and individual-achievement eligibility/points. `admissions`/`admission_fit` own their corresponding requirements and fit/score semantics. Unsupported new domain behavior remains unsupported until an explicit owner contract/evaluator change is approved; it is never implemented as a generic policy effect.
- Bounds: schema version; max depth 8, nodes 64, list members 32, text/scalar 512. No eval/exec, SQL, dynamic import, arbitrary operators, fields, or executable strings. Scope/evidence/validity/lifecycle/approval and target references remain typed relational columns/refs; JSONB only stores bounded predicate payload.
- Approval gate ships with the first persisted `PolicyRuleRevision`/`RuleCandidate`. In one repository transaction, append an initial immutable `PolicyApprovalEvent(kind=PENDING_SUBMITTED)` bound to the exact revision hash, submitter/ingest operation, capability, reason and recorded time; candidate/revision persistence without this event is rejected. Authorized human actions append `APPROVED`, `REJECTED` or `WITHDRAWN`; each new edit is a new revision with its own pending event. The current state is a deterministic projection of the ordered event history, not a mutable `approved_at`. `policy` owns this event ledger; `knowledge` review calls it through a typed command port. The resolver repository exposes only the exact revision whose current state is approved; direct DTO input cannot bypass the gate.
- Шаги: define predicate/type registry and domain-reference adapters; define `PolicyApprovalEvent` transitions and append-only constraints; deliver the additive migration and submission repository transaction that persists candidate/revision plus `PENDING_SUBMITTED` before any policy write endpoint/consumer; document schema version; include a non-benefit selection example and the fourth-exam scenario as a typed owner reference, not a generic score effect.
- Persistence owner: a policy-owned application command invokes the policy repository/Unit of Work to persist the candidate revision and its initial pending event atomically. Knowledge review calls typed policy commands and never writes the policy ledger directly. Until an authorized human approval command is available, all policy candidates remain pending and the resolver returns no effective rule for them.
- Approval-event concurrency: assign a unique monotonic sequence per revision and validate the state transition under the same transaction/lock; competing approvals cannot reorder history or produce two effective states. Keep this approval ledger policy-owned; Knowledge review invokes it only through the typed command port.
- Errors: unknown field/operator/version/owner contract, missing initial pending event, stale approval hash, invalid event transition or absent approved state → UNSUPPORTED_RULE / PENDING_REVIEW and fail closed; never partially apply.
- Будущие тесты: typed operator matrix, resource limits, malicious execution rejection, candidate plus pending event atomicity, revision/approval hash binding, immutable append-only audit, transition authorization, stale approval rejection, resolver cannot read pending/unreviewed revision, version round trip.
- Критерии приёмки: no policy candidate/revision is persisted without a pending event in the same transaction; only an exact revision with valid approved state enters the effective resolver; any edit loses approval; no extracted candidate/news claim/Jev suggestion/hypothesis/unreviewed revision can enter it; adding a domain data value may need no generic code, while a new operation must be implemented by its domain owner.
- Будущая проверка: python -m pytest backend/tests/unit/test_policy_ast.py backend/tests/contracts/test_policy_contracts.py
- Зависимости: Phase 01 approval/ownership contracts, Phase 02 temporal contracts, Phase 03 candidate vocabulary. Approval persistence is mandatory before the first rule-candidate write path and before Phase 05 resolver implementation.
- Откат: keep AST inert behind disabled resolver flag.
- Риски: accidental general-purpose language; keep registry intentionally small.
- Вне scope: formulas, scripts, user-authored SQL, LLM executable output.

### Выполнение Task 10

- Реализовано в `backend/src/andromeda/modules/policy/` и `backend/src/andromeda/infrastructure/`: закрытый AST `policy-selector.v1`; source-backed, content-hashed `PolicyRuleRevision`; immutable approval event contracts/service/repository; PostgreSQL models и additive migration `0044_policy_selector_approval.py`.
- `SqlAlchemyPolicyRuleRepository.submit_revision()` валидирует accepted source assertions и evidence allowlist, затем атомарно пишет exact revision, claim/evidence references и `PENDING_SUBMITTED`. `PolicyApprovalCommandService` требует typed capability и привязывает каждое решение к exact revision hash. Неподтверждённые revision records не имеют resolver read path; resolver появится в следующих задачах и обязан читать только approved history.
- AST v1 содержит только bounded `all`/`any`/`equals`/`in`/`exists` predicates по закрытому registry; policy хранит `DomainRuleRef` и не вычисляет eligibility, benefit, confirmation или points.
- Проверено: `23 passed` для `tests/unit/test_policy_ast.py`, `tests/infrastructure/test_knowledge_candidate_repository.py`, `tests/infrastructure/test_alembic_migrations.py`; targeted Mypy `18 source files`; targeted Ruff; `alembic heads` → `0044_policy_selector_approval (head)`; `git diff --check`.
- При чтении строгих JSON/tuple contracts SQL JSON arrays/enums преобразуются в зарегистрированные tuple/enum типы до validation; некорректные stored nodes отклоняются как persisted conflict.

<a id="task-11"></a>

## Task 11: Добавить deterministic applicability validation и domain dispatch

### Контракт выполнения

- Файлы: `modules/policy/services/applicability.py` and pure typed results; owner-specific selection/dispatch ports; policy unit tests and domain regression fixtures.
- Flow: typed cycle/scope/time context → validate bounded applicability predicates → select exact approved `DomainRuleRef` values → call the owner port for domain calculation. Policy returns applicability/selection/explanation and does not emit benefit eligibility or point values itself.
- Benefit boundary: route selected existing `AdmissionBenefitRule`/`IndividualAchievementRule` references through current `admission_benefits` service/evaluator. Stage 2 `AdmissionDecisionService`, `AdmissionBenefitEvaluator`, `IndividualAchievementCalculator` and `EffectiveCompetitiveScoreCalculator` remain sole calculators. Until the approved adapter exists, current benefit service remains the only path.
- Ошибки и логирование: unknown input is UNKNOWN, not false. Missing fields return incomplete selection. Unsupported predicate/owner revision fails closed. ResolutionTrace stores canonical revision/evidence references and reasons, not private profile payload.
- Будущие тесты: repeatability, unknown-vs-false, exact revision dispatch, no domain score/eligibility calculation in policy module, existing benefits output parity.
- Критерии приёмки: pure selector imports no DB/FastAPI/Jev; domain service output remains unchanged and is attributable to its own rule/evidence.
- Будущая проверка: future focused selector and admission-benefits regression suites.
- Зависимости: Task 10.
- Откат: feature flag bypasses new selector; existing owner services remain active.
- Риски: ambiguous/incompatible owner references must block dispatch and surface in ResolutionTrace.
- Вне scope: generic domain calculator, benefit evaluator replacement, or auto-activation of candidates.

### Выполнение Task 11

- Добавлены чистый трёхзначный evaluator selector AST и typed context (`PRESENT` / `UNKNOWN` / `UNAVAILABLE`); неизвестное поле остаётся `INDETERMINATE`, а смешанные `all`/`any` обрабатываются детерминированно.
- `PolicyApplicabilityService` принимает только `ApprovedPolicyRuleReader`, сверяет exact revision hash, затем обращается к typed owner read port за тем же `DomainRuleRef`. Pending/stale revisions, неизвестный context, отсутствующий owner port/rule и недоступный owner дают отдельные fail-closed состояния без selection.
- На этом шаге owner port только подтверждает точную domain revision. Он не считает eligibility/points; вызов существующих доменных evaluator остаётся интеграционным Task 24, когда появится полный typed admission context.
- Новые файлы: `modules/policy/contracts/applicability.py`, `domain/applicability.py`, `services/applicability.py`, `services/ports.py`, `tests/unit/test_policy_applicability.py`; расширен закрытый field registry и approved-only repository read port.
- Проверено: 14 policy unit/repository tests passed; 7 module-boundary architecture tests passed; targeted Mypy `19 source files`; Ruff policy paths.
- Effective resolver с temporal cycle mapping, scope precedence, overrides и mandatory `ResolutionTrace` остаётся Tasks 12–14; данный selector assessment сам по себе не заявляет effective applicability.


## Риски фазы и меры снижения

- Risk: domain-effect language recreates the Stage 2 admission-benefits calculator. Mitigation: AST contains only applicability predicates and typed owner-rule references; add an architecture test that policy cannot compute benefit/score semantics.
- Risk: schema lands without an immutable approval record or before an approval UI. Mitigation: the ledger and resolver gate ship before policy candidate writes; UI is not a prerequisite for enforcing approval.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
