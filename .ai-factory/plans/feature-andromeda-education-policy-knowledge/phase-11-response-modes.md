# Phase 11: ResponseEnvelope и три режима ответа

Plan: [index.md](index.md)
Tasks: 28-30
Depends on: Phase 10

## Цель

Represent verified facts/rules/impact/evidence/uncertainty in channel-neutral ResponseEnvelope and support deterministic, constrained-verbalization and clearly unverified fallback modes.

## Текущие точки интеграции и переиспользуемый код

- modules/presentation ResponseEnvelope, ResponsePlan, ResponsePolicyPort and allowed templates.
- Stage 2 typed `AssistantResult`/ResponseEnvelope route, including admission assumptions and entity-resolution evidence metadata; preserve these fields and existing generated OpenAPI clients.
- Provider-neutral dependency pattern in infrastructure; no LLM verbalization adapter is a core dependency.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-28"></a>

## Task 28: Расширить ResponseEnvelope для policy/evidence/relevance

### Контракт выполнения

- Файлы: modules/presentation/contracts/response.py and response policy implementation; API schema assistant.py; OpenAPI export and generated frontend types; contract tests.
- Additive typed sections: response mode, user-facing status, claim/policy state, source trust shown separately, known facts, published/effective dates, affected scope/cycle, exceptions, applicability/actionability, impact delta, uncertainty/missing data, last checked, evidence locators/source links and as-of knowledge time. Include typed structured `ResolutionExplanation` projected from mandatory `ResolutionTrace` (trace ID/version, selected references, relevant rejection reasons/conflicts and provenance refs); do not replace this with LLM prose or expose private reviewer/profile data. Keep channel-neutral; do not leak every internal enum.
- Compatibility: retain existing response_type/template/data/evidence behavior, define old-client defaults and avoid changing old fields' meaning; generated OpenAPI remains source for frontend.
- Ошибки и логирование: no evidence means no verified answer; inaccessible evidence says unavailable; link validation and safe URI handling; response does not expose private reviewer metadata.
- Будущие тесты: contract schema, serialization of old/new envelopes, status mapping table, evidence locator, generated OpenAPI drift.
- Критерии приёмки: envelope can render trusted answer, proposal, future applicability, conflict and insufficient-data states with typed ResolutionTrace explanation, without channel-specific business logic; old Stage 2 fields retain meaning.
- Будущая проверка: python backend/scripts/export_openapi.py; npm run generate-api and npm run check-api-drift in frontend-next.
- Зависимости: Task 27 and product wording review.
- Откат: additive fields optional; clients ignore unknown fields; disable new template mapping.
- Риски: current generic data dictionary may encourage untyped payload; add named typed sections and version them.
- Вне scope: LLM narrative content.

<a id="task-29"></a>

## Task 29: Реализовать deterministic и constrained verbalization modes

### Контракт выполнения

- Файлы: presentation ResponsePolicy and optional ResponseVerbalizerPort; provider-neutral infrastructure adapter only after provider selection; deterministic renderer; contract and integration tests.
- Mode 1: fully source-backed typed result with deterministic response and structured resolver explanation; Jev may only help bounded query/entity understanding.
- Mode 2: assemble verified structured facts/rules/status/dates/impact/exceptions/evidence/uncertainties first; optional LLM verbalizer receives only that result and may return a validated presentation plan (ordering/reference IDs), while factual values and citations are rendered server-side from verified fields. No generated new facts, dates, policy status or evidence.
- Provider remains optional; missing/timeout/invalid output falls back to deterministic renderer. Redact profile data; enforce output size/time/cost limits and provider telemetry without prompts/secrets in logs.
- Будущие тесты: model-added fact rejected, unknown evidence ID rejected, nondeterministic prose cannot alter typed envelope, provider unavailable fallback, output injection/sanitization.
- Критерии приёмки: core works with no LLM package/network; mode 2 changes phrasing only and preserves identical typed factual payload.
- Будущая проверка: python -m pytest backend/tests/unit/test_response_verbalizer.py backend/tests/integration/test_assistant_knowledge_query.py
- Зависимости: Task 28 and human provider/data policy gate.
- Откат: disable port; deterministic mode remains.
- Риски: even reference selection can distort emphasis; bound ordering and preserve required status/evidence sections.
- Вне scope: mandatory DeepSeek/runtime LLM or free-form trusted prose.

<a id="task-30"></a>

## Task 30: Добавить явно unverified fallback вне coverage

### Контракт выполнения

- Файлы: presentation mode routing; optional general-response port only if product/provider decision approved; API contract and tests.
- Mode 3 is allowed only for questions outside Andromeda coverage; mark unverified/outside coverage in ResponseEnvelope and visually separate from verified evidence path. It is not stored as claim/rule/fact, cannot affect decisions and cannot be represented as verified answer.
- Ошибки и логирование: if no configured model/provider, return typed unsupported response. Never include general answer in canonical index or derived policy refresh.
- Будущие тесты: outside-coverage routing, status display, no persistence, no effect on next deterministic query.
- Критерии приёмки: a client can distinguish all 3 modes and a general answer can never be mistaken for verified knowledge.
- Будущая проверка: assistant mode routing API tests.
- Зависимости: Task 28 and explicit fallback product policy.
- Откат: disable fallback and return unsupported.
- Риски: user may ignore uncertainty label; channel templates must display it prominently.
- Вне scope: general LLM answering for policy-covered questions.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
