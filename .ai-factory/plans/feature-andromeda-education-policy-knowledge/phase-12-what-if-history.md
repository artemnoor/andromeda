# Phase 12: What-if, future и historical queries

Plan: [index.md](index.md)
Tasks: 31-32
Depends on: Phases 06, 10 and 11

## Цель

Support scenario evaluation and temporal questions against immutable revisions without changing canonical state, and distinguish current/future/historical/as-known answers.

## Текущие точки интеграции и переиспользуемый код

- Policy resolver, typed impact preview, bitemporal revisions and AdmissionCycle.
- QuerySession typed context from Phase 10.
- Existing canonical snapshot history and audit records; historical completeness must be explicit.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-31"></a>

## Task 31: Реализовать deterministic what-if sandbox

### Контракт выполнения

- Файлы: modules/policy/contracts/what_if.py; service sandbox_evaluator.py; repository read-only snapshot ports; review preview API schema/route; tests.
- Input: current approved effective-policy snapshot plus one validated unapproved RuleCandidate or explicit candidate revision overlay, target cycle/scope/context. A separate `HypotheticalPolicyPreview` path invokes the same pure precedence/applicability kernel in a sandbox but does not call the production Effective Rule Resolver/repository, issue an approval event, or label the candidate effective. Produce baseline-vs-hypothetical selection/domain-owner result, semantic diff and impact.
- No writes: sandbox uses read-only repositories and an in-memory immutable hypothetical overlay; it cannot approve, persist canonical records, mutate applicant/DecisionContext or trigger notifications. Operator preview and user question “if adopted” have distinct authorization and wording. Production resolver still accepts only exact revisions with explicit approval events.
- Ошибки и логирование: unapproved candidate marked hypothetical; malformed/unsupported candidate fails closed; stale snapshot versions reported; no implicit activation.
- Будущие тесты: unapproved candidate hypothetical preview does not enter effective resolver, no database mutation, same input/trace repeatability, authorization, baseline vs candidate for 2027/2028, unsupported owner reference.
- Критерии приёмки: preview includes hypothetical label, assumptions, approved base snapshot/version, candidate revision hash, baseline/candidate ResolutionTrace, diff, impact, missing data and evidence; approval ledger/canonical checksums unchanged.
- Будущая проверка: python -m pytest backend/tests/unit/test_policy_what_if.py backend/tests/api/test_policy_preview.py
- Зависимости: Tasks 13, 17, 18 and 27.
- Откат: disable preview endpoint; no canonical rollback required.
- Риски: user may interpret hypothetical as accepted; envelope must label it prominently and separate from effective answer.
- Вне scope: write-capable simulation or automatic deployment.

<a id="task-32"></a>

## Task 32: Поддержать current/future/historical/as-known-at queries

### Контракт выполнения

- Файлы: policy/knowledge read use cases; API query/history contracts; conversation policy-context parsing; tests/docs.
- Query dimensions: effective at date/admission cycle, historical valid interval, system knowledge as-of timestamp, source publication/capture history. Answer “what did Andromeda know yesterday?” only from system-time revision history.
- Шаги: expose change history and effective policy diff for two cycles; render old/new rules and evidence; distinguish no historic records from known negative; include time-zone/date boundary policy.
- Ошибки и логирование: unreconstructable historical state returns HISTORICAL_STATE_UNAVAILABLE; as-of before first observation is not inferred; invalid timeline returns typed validation.
- Будущие тесты: 2025 historical; current now; 2027 vs 2028; yesterday-known vs newly observed document; “why answer changed?” from revision/evidence chain.
- Критерии приёмки: result identifies valid-time and knowledge-time separately and explains changed answer with version/source history.
- Будущая проверка: python -m pytest backend/tests/integration/test_policy_history.py backend/tests/api/test_policy_history.py
- Зависимости: Tasks 6, 12, 16, 27-28.
- Откат: historical endpoint can be disabled while current policy path continues.
- Риски: early database history may be incomplete; expose coverage start and gaps.
- Вне scope: fabricated backfill of past system knowledge.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
