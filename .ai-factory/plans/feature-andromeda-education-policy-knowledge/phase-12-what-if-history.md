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

### Результат выполнения Task 31

- Переиспользованы уже имеющиеся `PolicyHypotheticalSandbox`, exact pending revision/approval ledger ports, immutable approved snapshot, shared applicability/precedence kernel, semantic diff и domain-owner impact comparison. Sandbox не вызывает `EffectivePolicyResolver`, не пишет approval/canonical rows и не меняет applicant/DecisionContext.
- Hypothetical candidate trace, approved current trace, snapshot hash, candidate revision hash, diff, impact, evidence и assumptions уже представлены обязательным typed `PolicyHypotheticalPreview`; review API preview защищён reviewer authorization. Существующее API test подтверждает отказ unauthenticated caller.
- Добавлена temporal regression: revision, selector которой ограничен 2028, в preview для admission cycle 2027 остаётся `selector_not_matched` и не входит в effective rules. Существующие тесты покрывают preview repeatability, current-vs-candidate diff и отсутствие repository writes; pending-only approval gate остаётся неизменным.
- Проверки: `uv run --locked pytest tests/unit/test_policy_what_if.py tests/api/test_knowledge_ops.py -q` — `6 passed`; Ruff — чисто; focused mypy на production what-if contract/service — чисто. Попытка типизировать весь legacy unit-test module выявила ранее существовавшие untyped test helpers/URL annotation; runtime tests и изменённая implementation типизированы.
- Новых API, migrations, persistence или production runtime изменений не потребовалось; Task 17/18 review preview уже предоставлял нужный seam.

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

### Результат выполнения Task 32

- Расширен существующий `PolicyQueryContext`: effective admission year(s), valid-time date, system knowledge-time cutoff и history focus остаются разными typed значениями в `QuerySession`. Parser поддерживает ISO-date valid-time, exact/as-yesterday knowledge-time, одиночный historical cycle и bounded chronological pair для сравнения двух кампаний.
- Assistant продолжает работать через существующий `/assistant/query`. Для одного historical cycle policy resolver использует approved application-window start как valid-time, если вопрос не задаёт точную дату; сравнение разрешает оба цикла по их собственным approved start dates при одном `as_known_at`. В каждом trace/API projection есть valid-time и trace/evidence; response включает оба ResolutionExplanation и typed effective-policy semantic diff.
- Исторический claim lookup использует bitemporal repository cut-off. Отсутствующее состояние на запрошенную дату выдаёт `historical_state_unavailable`, а не «правила не было». Proposal/source assertion остаётся раздельным с effective policy; effective resolution по-прежнему принимает только approved revisions.
- Boundary принято детерминированно: date-only knowledge cutoff — конец указанного UTC дня (`23:59:59.999999Z`); «вчера» — предыдущий UTC день; date-only valid-time сохраняет существующее начало UTC-дня; cycle default — `00:00Z` начала официального application window. Actual selected instants присутствуют в response traces. Недоступное окно цикла оставляет resolution blocked.
- Добавлены parser/session, query, empty-history, yesterday, two-cycle resolver/diff и projection/render regressions. Persistence использует уже существующие claim/policy revision history; schema/migrations не менялись.
- Проверки: focused policy/conversation/presentation — `33 passed`; API/OpenAPI JSON Schema/architecture — `20 passed`; session/repository checks — `7 passed`; focused mypy — чисто; Ruff — чисто; OpenAPI regeneration, `npm run check-api-drift` и `npx tsc --noEmit` — успешно.
- Ограничение: история до первого сохранённого immutable revision не восстанавливается и не backfill-ится. API сообщает недоступность исторического состояния.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
