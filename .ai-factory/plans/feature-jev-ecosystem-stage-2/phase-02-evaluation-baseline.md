# Phase 02 — Evaluation baseline: System One Adapter and task corpus

Plan: [index.md](index.md)
Tasks: T04–T05
Depends on: Phase 01 / Tasks T01–T03

## Objective

Получить воспроизводимый baseline и приватный evaluation harness до того, как Jev сможет влиять на production decisions. Official System One Adapter используется только как DEV/EVAL_TOOL, не как runtime dependency.

## Task T04 — Изолировать official System One Adapter в evaluation toolchain

### Implementation steps

1. Добавить optional development extra в backend/pyproject.toml для system-one-adapter-python с pinned compatible version; не добавлять его в default production dependency set.
2. Создать backend/scripts/evaluate_system_one.py:
   - читает versioned DecisionDefinition;
   - формирует typed examples;
   - вызывает official SystemOneAdapterClient/async client;
   - сохраняет only sanitized structured outputs;
   - records input/output tokens, latency, retries and provider/model identity;
   - maps responses through the same DecisionModelPort contract.
3. Reuse backend/src/andromeda/modules/conversation/services/evaluation.py and extend it with an evaluator adapter, rather than a second evaluator framework.
4. Add optional provider configuration through environment/secret manager; fail before execution if key is missing.
5. Pin lockfile and document supported Python/runtime versions. System One Adapter is not imported by application composition.

### Failure behavior and logging

A failed row is marked provider_error; evaluation continues only under explicit --allow-failures mode and reports denominator. Never store raw free-form user text in reports unless a local encrypted/private corpus is explicitly selected.

### Tests

- backend/tests/evaluation/test_system_one_evaluator.py with fake official-client protocol;
- usage/retry mapping;
- missing key, timeout and malformed structured response;
- packaging test proving importing andromeda.composition.container does not require System One package.

### Acceptance criteria

- baseline runs offline with deterministic fake;
- real System One invocation is opt-in;
- generated report distinguishes provider error from low quality;
- no production path imports the adapter.

### Dependencies, rollback and risks

Depends on T01–T03. Rollback is removal of optional extra/script; existing deterministic evaluator remains. Risk: upstream release/API drift; pin and test public API at install time.

## Task T05 — Создать canonical decision corpus и replay protocol

### Implementation steps

1. Создать backend/evals/jev/:
   - corpus/decision-cases.v1.jsonl;
   - schemas/decision-case.schema.json;
   - labels/decision-labels.v1.jsonl;
   - README.md describing ownership and privacy.
2. Corpus covers intent, metric, next_action, presentation, semantic feature classification and degraded cases: complete admission query; missing EGE subjects; university ambiguity; multi-program comparison; unsupported metric; unavailable data; response format; semantic value requiring review.
3. Each case stores typed input fixture, expected allowed output(s), clarification semantics, case_id, definition version and dataset split. Do not store secrets/private profiles.
4. Extend backend/src/andromeda/modules/conversation/services/evaluation.py for deterministic replay, provider replay and shadow comparison with stable case IDs.
5. Add backend/scripts/check_eval_artifacts.py rejecting secrets, cookies, access tokens and unredacted personal-data patterns.

### Logging and observability

Reports contain case IDs, operation, decision source, confidence bucket, latency and failure reason. Raw text is excluded by default; debug mode can point to a local ignored directory.

### Tests

- corpus JSON schema validation;
- split determinism;
- duplicate case IDs;
- allowed output validation;
- privacy scanner fixtures;
- replay equivalence for deterministic policy.

### Acceptance criteria

- same corpus produces reproducible aggregate reports;
- no production data is required to run tests;
- every Jev definition has train/dev/heldout case or is explicitly marked not_calibratable;
- empty/partial corpus blocks enablement rather than producing a fake quality score.

### Dependencies, rollback and risks

Depends on T02. Rollback deletes only new evaluation artifacts. Risk is label leakage; heldout split is immutable during a calibration run.

## Commit checkpoint C1

After T01–T05: commit documentation, shared definitions, envelope contracts and baseline harness as one reviewable checkpoint. Do not enable external runtime.

## Phase Verification

- pytest backend/tests/evaluation -q
- python backend/scripts/check_eval_artifacts.py
- uv run python backend/scripts/evaluate_decision_model.py --help

Expected result: deterministic replay is reproducible, sanitized corpus checks pass, and core composition imports without optional evaluator packages.
