# Phase 01 — Foundation: upstream classification, shared definitions and strict ports

Plan: [index.md](index.md)
Tasks: T01–T03
Depends on: repository audit and current contracts

## Objective

Зафиксировать единую vendor-neutral модель Jev-задач и правила интеграции до подключения внешнего runtime. Существующие DecisionModelPort, SemanticClassifierPort, QuerySpec, ResponsePlan и deterministic fallback остаются источниками истины.

## Scope and evidence

Текущий код уже содержит typed decision operations и generic JevTransport, но не содержит shared Question Registry, lock identity, feature flags или реального provider adapter. Это подтверждено чтением backend/src/andromeda/modules/conversation/contracts/policy.py, backend/src/andromeda/infrastructure/jev/adapter.py, backend/src/andromeda/composition/container.py и backend/pyproject.toml.

## Task T01 — Зафиксировать baseline и архитектурные инварианты

### Implementation steps

1. В docs/architecture/integration-seams.md добавить актуальную карту upstream-стратегий и запрет на vendor imports в modules/domain, modules/contracts и modules/services.
2. В docs/architecture.md дополнить dependency graph: canonical → semantic → program_analytics → analytics → conversation → decision model → response policy → channel adapter.
3. Добавить docs/architecture/jev-ecosystem.md с таблицей:
   - jevcal — DEV/EVAL_TOOL;
   - jev-align — DEV/EVAL_TOOL;
   - System One Adapter — DEV/EVAL_TOOL;
   - jevQL — ISOLATED_OPTIONAL_RUNTIME;
   - jev-tree — ISOLATED_OPTIONAL_RUNTIME;
   - awesome-jev — PATTERN_ONLY.
4. Явно зафиксировать, что decision_analytics — telemetry действий, а не catalog analytics; DecisionContext — explicit user decision, а QuerySession — conversation memory.
5. Зафиксировать baseline SHA 8e11ef6, ветку feature/university-admin-control и наличие pre-existing dirty changes; branch creation не выполнять.

### Contracts and compatibility

Публичные Python contracts и API не меняются. Документ должен ссылаться на фактические символы, а не на гипотетические сервисы.

### Logging and security

Документация не должна содержать secrets, реальные API keys, cookies или private profile data. В operational rules указать structured fields без raw prompt.

### Tests and checks

Запустить python backend/scripts/check_architecture.py, git diff --check и существующий docs CI subset. Проверить, что ссылки на paths/symbols разрешаются.

### Acceptance criteria

- upstream classification ровно одна на проект;
- dependency direction и no vendor in domain явно зафиксированы;
- baseline/dirty worktree отражены;
- новых runtime-зависимостей нет.

### Dependencies, rollback and risks

Зависит от repository audit. Rollback — удалить только документационную правку. Главный риск — принять README за runtime capability; каждая capability должна быть подтверждена source/test audit.

## Task T02 — Ввести shared DecisionDefinition и Question Registry

### Implementation steps

1. Создать vendor-neutral contracts в backend/src/andromeda/modules/conversation/contracts/decision_definitions.py:
   - DecisionDefinitionId;
   - DecisionDefinitionKind (intent, metric, next_action, presentation, semantic_feature);
   - DecisionDefinition;
   - DecisionOption;
   - DecisionOutputSchema;
   - DefinitionVersion.
2. Definition должна описывать operation, input schema, allowed choices/score range, evidence policy, timeout class, fallback action, PII policy и required calibration artifact, но не содержать jevcal, typesafe, jevql или jev-tree types.
3. Создать backend/src/andromeda/infrastructure/jev/question_registry.py с typed loader/validator и QuestionRegistryPort либо использовать существующий public port только после проверки ownership.
4. Создать versioned source definitions в backend/config/jev/question-definitions.v1.yaml для current operations: intent, metric, next_action, presentation, semantic_feature.
5. Для каждой definition зарегистрировать schema version, operation name, deterministic fallback, allowed response enum, maximum input size, redaction profile и evaluation dataset key.
6. Expose только immutable lookup API; unknown definition и duplicate id должны быть startup/config errors.
7. Не помещать в registry tool-specific технические параметры: jevcal split/optimizer/cache, jev-align acquisition/review settings и jev-tree/jevQL process flags остаются в собственных validated configs вокруг registry. Registry is the source of truth for instructions, criteria, version and input/output contract only.

### Existing symbols to reuse

DecisionModelOperation, DecisionModelPort, DecisionAction, PresentationFormat, RuleBasedDecisionModel, SemanticClassificationMethod.

### Failure behavior and logging

Missing or malformed registry fails closed at adapter initialization and leaves deterministic composition usable. Log only definition id/version, not input text. Emit definition_load_failed with reason code.

### Tests

- backend/tests/modules/conversation/test_decision_definitions.py;
- backend/tests/infrastructure/test_question_registry.py;
- malformed YAML, duplicate ids, unsupported output, oversized input;
- architecture test proving contracts do not import infrastructure/upstream packages.

### Acceptance criteria

- all external operations reference a registry definition for instructions/criteria/version/schema;
- tool-specific runtime settings remain independently versioned and validated;
- deterministic policy works without registry/provider;
- definitions are versioned and auditable;
- no natural-language prompt is passed as an untyped free-form vendor call.

### Dependencies, rollback and risks

Depends on T01. Rollback is safe because existing adapter can retain a compatibility mapping temporarily. Do not duplicate operation strings in adapters after migration.

## Task T03 — Уточнить typed integration boundary и response envelope для external models

### Implementation steps

1. Расширить backend/src/andromeda/infrastructure/jev/adapter.py: request должен содержать definition_id, definition_version, operation, redacted typed payload, correlation_id, timeout budget и requested output schema.
2. Ввести internal infrastructure contracts JevRequestEnvelope, JevResponseEnvelope, JevUsage, JevFailure; external response must be validated before mapping to DecisionModelPort.
3. Сохранить DecisionModelPort as the only application-facing port. Existing JevTransport.request remains transport-level compatibility seam, but no caller may pass arbitrary operation names after registry migration.
4. Ввести ModelIdentity и DecisionSource metadata: deterministic, Jev, shadow-only, fallback и artifact identity. Metadata не изменяет user facts.
5. Define timeout classes: interactive, enrichment, evaluation; no unbounded retries.
6. Map failures to typed reasons: timeout, transport, auth, schema, budget, rate_limit, artifact_missing, provider_unavailable.

### Existing symbols to reuse

DecisionModelSource, ConfidenceBucket, DecisionModelOperation, JevAdapterConfig, DecisionModelResult and current allowed-template validation.

### Logging and security

Structured events: jev_request_started, jev_request_completed, jev_request_fallback, jev_schema_rejected. Fields: operation, definition version, source, latency_ms, retry_count, fallback_reason, confidence_bucket. Never log payload, tokens, API key or session cookie.

### Tests

- extend backend/tests/infrastructure/test_jev_adapter.py;
- fake transport tests for each failure reason;
- schema rejection tests;
- contract test that arbitrary SQL, template names and actions cannot be returned by provider;
- timeout and retry budget tests.

### Acceptance criteria

- all model output is untrusted and schema-validated;
- provider cannot select arbitrary endpoint/SQL/template;
- deterministic behavior is byte-for-byte compatible when Jev disabled;
- usage and failure metadata are available for observability.

### Dependencies, rollback and risks

Depends on T02. Rollback is feature flag to current RuleBasedDecisionModel; no schema migration. Risk: widening public contracts; keep new metadata optional/defaulted and preserve serialization compatibility.

## Phase Verification

- python backend/scripts/check_architecture.py
- pytest backend/tests/infrastructure/test_jev_adapter.py backend/tests/infrastructure/test_question_registry.py backend/tests/modules/conversation/test_decision_definitions.py -q
- git diff --check

Expected result: contracts validate, vendor imports stay outside application modules, focused tests pass, and only planned files are changed.
