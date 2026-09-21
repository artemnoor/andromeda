# Phase 07 — Runtime wiring, feature flags and observability

Plan: [index.md](index.md)
Tasks: T18–T21
Depends on: Phases 01–06 and all optional adapter contracts

## Objective

Подключить staged runtime так, чтобы deterministic path оставался default, Jev мог работать в shadow mode, а production enablement требовал calibrated artifacts и explicit capabilities.

## Task T18 — Add settings and capability flags

### Implementation steps

1. Extend backend/src/andromeda/infrastructure/config/settings.py with typed settings:
   JEV_ENABLED, JEV_SHADOW_ENABLED, JEV_CALIBRATION_ENABLED, JEV_CALIBRATION_LOCK_PATH, JEV_RUNTIME_PROVIDER, JEV_ALIGN_CAPTURE_ENABLED, JEVQL_ENABLED, JEVQL_ENDPOINT, JEV_TREE_ENABLED, JEV_TREE_ENDPOINT, JEV_MAX_ROWS, JEV_MAX_CHARS, JEV_TIMEOUT_SECONDS, JEV_MAX_CONCURRENCY and evaluation-only SYSTEM_ONE_ENABLED.
2. Defaults are disabled, bounded and safe for ANDROMEDA_ENV=test.
3. Cross-setting validation:
   - enabled runtime requires endpoint/transport and lock;
   - shadow may run without user-impacting gate;
   - provider endpoint must be allow-listed and not user-controlled;
   - max budgets stay within hard caps.
4. Update deployment examples and secret documentation, never commit values.
5. Preserve redacted Settings logging.

### Tests

- settings default/production validation;
- invalid combinations;
- endpoint SSRF/URL policy;
- environment parsing;
- no secret value in repr/logs.

### Acceptance criteria

- current tests run with all new flags off;
- one optional component does not enable others;
- invalid production configuration fails closed.

### Dependencies, rollback and risks

Depends on T03, T13 and T16. Rollback is defaults-only; no migration.

## Task T19 — Wire Jev decision model and shadow policy in composition root

### Implementation steps

1. Create backend/src/andromeda/infrastructure/jev/typesafe_client.py with a production TypeSafeJevTransport implementing the existing JevTransport contract through the pinned official typesafe-sdk API. If the selected deployment uses a TypeSafe-compatible HTTP endpoint instead, implement that as a separately named transport with the same typed envelope and an explicit provider identity; do not hide it behind the evaluation-only System One Adapter.
2. The production client must perform real registered decision operations: send the definition_id/version, typed payload and requested output schema; validate the response; map usage/latency/retry metadata; enforce timeout/rate-limit policy; and expose a health/version check. It must not accept SQL, arbitrary prompts, user endpoints or unregistered operations.
3. Add contract tests against a fake TypeSafe SDK/compatible endpoint and one opt-in provider smoke test. Pin the exact SDK/endpoint protocol version in the optional production Jev dependency manifest.
4. Update backend/src/andromeda/composition/container.py to construct:
   - deterministic RuleBasedDecisionModel/policy always;
   - optional JevDecisionModelAdapter backed by the real TypeSafeJevTransport only when settings, capability, provider health and calibration lock validate;
   - ShadowDecisionModel executing Jev side-by-side but returning deterministic result;
   - optional semantic/predicate/tree adapters independently.
5. Keep AssistantService and domain services unaware of settings/vendor names. They receive existing DecisionPolicyPort, DecisionModelPort, SemanticClassifierPort and analytics ports.
6. Preserve deterministic fallback if adapter construction, health check, lock, schema or provider fails.
7. Do not inject System One, jevcal or jev-align clients into production composition. jevQL/jev-tree are separate optional capabilities and do not implement the decision model.
8. Include startup capability report with enabled/disabled reason codes and the selected provider/model/lock identity without secrets.

### Tests

- composition matrix across flags;
- production TypeSafeJevTransport request/response contract with fake SDK/endpoint;
- provider health/version failure and usage/retry mapping;
- backend/tests/modules/conversation/test_shadow_policy.py;
- exact deterministic result unchanged with Jev unavailable;
- adapter health failure;
- lock mismatch;
- optional dependencies absent;
- no network call in test default.

### Acceptance criteria

- Jev is optional infrastructure;
- a real production TypeSafe-compatible client exists behind DecisionModelPort;
- System One Adapter remains eval-only and is never used as the production client;
- shadow mode has zero user-visible influence;
- production mode cannot start without valid lock/definition/artifact;
- MAX/Web/Telegram consume same assistant contracts.

### Dependencies, rollback and risks

Depends on T18 and T03. Rollback is config flag off and deterministic composition. Risk: circular imports; architecture checker must enforce direction.

## Task T20 — Add safe structured observability and cost/latency accounting

### Implementation steps

1. Extend existing logging/metrics infrastructure with query_id, session_id_hash, operation, definition_id/version, decision source, confidence bucket, latency/retries/token usage if provider returns it, analytics population/coverage, semantic classifier/projection version, fallback reason, cache hit/miss and optional runtime budget.
2. Emit aggregate shadow comparison telemetry: agreement/disagreement, confidence delta, expected action class, not raw response/prompt.
3. Add retention/redaction rules and sampling. session_id_hash is keyed/non-reversible.
4. Keep decision_analytics separate from these operational/model metrics or introduce clearly named observability sink; do not reuse catalog tables.

### Tests

- log schema tests;
- redaction tests for cookies/secrets/raw profile;
- metric-cardinality constraints;
- shadow disagreement report;
- provider usage mapping.

### Acceptance criteria

- operators can explain fallback;
- no sensitive payload appears in logs;
- shadow comparison works by case/definition without content leakage.

### Dependencies, rollback and risks

Depends on T19 and existing telemetry. Rollback disables optional metrics, not safety logs.

## Task T21 — Lock dependency packaging and runtime compatibility

### Implementation steps

1. Add separate manifests for Python dev/eval, isolated jevQL service and isolated jev-tree service. Do not put all projects in backend/pyproject.toml default dependencies.
2. Pin Python >=3.11 application; System One Adapter only dev/eval; jevcal/jev-align source revisions; jevQL Go release and Linux architecture; jev-tree Node >=22; official TypeSafe SDK only in chosen optional Jev provider extra after API contract tests.
3. Add license inventory in docs/architecture/jev-ecosystem.md; verify MIT/Apache/CC0 compatibility and preserve notices.
4. Add CI jobs testing optional imports in own environments and core import without them.
5. Record upstream SHA/release, install mode, supported OS and cache/security assumptions.

### Tests

- clean core install;
- optional eval install;
- isolated service smoke tests;
- license/package audit;
- Windows developer path;
- PostgreSQL integration with optional services off.

### Acceptance criteria

- production core image excludes dev/eval-only packages;
- unsupported platform disables optional capability explicitly;
- lockfiles/source revisions reproducible.

### Dependencies, rollback and risks

Depends on T04, T10, T13 and T16. Rollback removes optional packaging entries; core lock remains intact.

## Commit checkpoint C6

After T18–T21: commit disabled-by-default runtime wiring, flags, observability and separate dependency manifests. No production flag flip.

## Phase Verification

- pytest backend/tests/infrastructure backend/tests/modules/conversation -q
- python backend/scripts/check_architecture.py
- mypy backend/src
- core install/import test with optional dependencies absent

Expected result: deterministic composition remains default, shadow mode cannot change responses, the production TypeSafe client is contract-tested, settings fail closed, and optional packages are not required by core startup.
