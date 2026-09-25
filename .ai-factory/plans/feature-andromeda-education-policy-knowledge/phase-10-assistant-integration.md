# Phase 10: Conversation и assistant queries

Plan: [index.md](index.md)
Tasks: 26-27
Depends on: Phases 05, 09

## Цель

Add policy/change questions to the existing assistant query flow and typed session context; do not build a second assistant or move business logic to channels.

## Текущие точки интеграции и переиспользуемый код

- Stage 2 `ConversationIntent`, `QueryFrame`, `QuerySession`, parser/session services and persistent repository; session already tracks explicit/inferred admission year, study form, funding, university scope, resolution cache/evidence and parser version.
- Stage 2 `AssistantService` → parser/entity resolution → existing `DecisionPolicyPort`/typed request → execution → result/evidence; `DecisionModelPort` and Jev-backed `DecisionPolicyPort` are already composed behind fail-closed runtime gates.
- Existing `/assistant/query`, `AssistantResult` (including batch `admission_requests`) and channel-neutral ResponseEnvelope; preserve these Stage 2 API/schema additions.
- Stage 2 `EntityResolverService`/`HierarchicalResolutionService` and `JevAdmissionCandidateSelector` are composed by `AndromedaContainer`; QuerySession preserves canonical resolution cache and evidence. Do not add another resolver.
- MAX, Telegram and Web are planned/currently thin channel adapters through the shared API.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-26"></a>

## Task 26: Расширить intent, parser и typed QuerySession context

### Контракт выполнения

- Файлы: `modules/conversation/contracts/public.py`, `domain/session.py`, parser/compiler and assistant/query-session services; API assistant schema/route; existing session repository only if typed JSON serialization needs extension; OpenAPI/frontend generated types and tests. Decision definition contracts already live at `modules/conversation/contracts/decision_definitions.py`.
- Intent: add one broad KNOWLEDGE_POLICY_QUERY covering status/change/history/applicability/impact, not dozens of intents. Keep UNKNOWN and existing intents stable.
- Context: optional nested PolicyQueryContext with admission year, university/program/direction, route, cycle, valid-time as-of, system-time as-known-at, resolved source/change/rule ID, what-if candidate and input provenance. Reuse the existing Stage 2 typed admission slots (year, study form, funding, university scope) rather than duplicating them. Add one versioned nested knowledge context instead of more flat slots or raw string history; store only trace/reference IDs, not a full ResolutionTrace or profile transcript.
- Шаги: inspect local model shape/serialization; define slot transitions and clarification triggers; preserve existing JSON session reads with default absent context; update parser and policy port request compilation.
- Ошибки и логирование: ambiguous entity asks a typed follow-up; missing admission year is BLOCKED_BY_MISSING_DATA; never infer personal profile/decision context silently.
- Будущие тесты: rumor question, follow-up “does it affect me?”, year slot fill, session reload, expiry, backward-compat old session JSON, ambiguity.
- Критерии приёмки: multi-turn state persists typed slots and source of each slot; existing analytics/admission conversation scenarios pass unchanged.
- Будущая проверка: python -m pytest backend/tests/unit/test_conversation_engine.py backend/tests/api/test_assistant_query.py
- Зависимости: Task 25 and existing assistant implementation.
- Откат: feature flag routes new intent to existing clarification/unsupported response.
- Риски: QuerySession grows into a generic event store; keep one bounded nested context and current revision/expiry semantics.
- Вне scope: second chatbot/backend or channel-specific policy logic.

<a id="task-27"></a>

## Task 27: Добавить policy lookup в assistant orchestration

### Контракт выполнения

- Файлы: extend current `modules/conversation/services/assistant.py`, query compiler and use-case contracts; API `routes/assistant.py`/schemas; `AndromedaContainer`; integration/API tests. Keep domain resolution behind the new typed `policy`/`knowledge` ports.
- Flow: natural language → existing parser/entity/session → deterministic DecisionPolicy → typed policy query request → source/claim/rule lookup → applicability/effective resolver/impact → typed evidence result → existing ResponsePolicy. Do not query ORM from API or assistant directly.
- Use cases: “is fourth exam adopted?”, “from when?”, “does BMSTU have exception?”, “what changes for 2027/2028?”, “what changed vs prior rule?”, “what is not known?”.
- Error/logging: outside coverage returns typed unsupported/unverified result; unresolved conflict and missing evidence remain explicit; trace correlates session/request IDs but redacts personal attributes.
- Будущие тесты: vertical source-backed question; current/future/historical intent; no evidence; conflict; multi-turn year clarification; old AssistantResult clients.
- Критерии приёмки: same /assistant/query owns old and new paths; full evidence/result exists before response formatting; current decision APIs unchanged.
- Будущая проверка: python -m pytest backend/tests/api/test_assistant_query.py backend/tests/integration/test_assistant_knowledge_query.py
- Зависимости: Task 26, Phase 05 resolver, Phase 09 adapters.
- Откат: disable new intent handler; old intent routing stays registered.
- Риски: Stage 2 DecisionPolicy controls assistant actions, not legal/policy resolution; keep those responsibilities distinct and route rule applicability to the deterministic `policy` resolver.
- Вне scope: news search endpoint as a second answer engine.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
