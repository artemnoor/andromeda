# Phase 08: Bounded Jev-assisted semantics

Plan: [index.md](index.md)
Tasks: 21-23
Depends on: Stage 2 baseline (Phase 00), Phase 03 approval-gated candidates and Phase 07 operator workflow

## Цель

Use Jev only for bounded understanding/linking via the already-integrated Stage 2 typed ports, Question Registry, TypeSafe transport, calibration and runtime composition. Deterministic validation and explicit human approval remain required.

## Текущие точки интеграции и переиспользуемый код

- Stage 2 `modules/conversation/contracts/decision_definitions.py` (`DecisionModelPort`, `QuestionRegistryPort`), `infrastructure/jev/{adapter,question_registry,typesafe_client,calibration,runtime,admission_resolution}.py`, `AndromedaContainer` and fail-closed capability reports are present and wired.
- Existing operations include shared Question Registry/TypeSafe transport for bounded decision operations and a separately versioned/locked `resolve_olympiad_profile` operation via `JevAdmissionCandidateSelector` and existing `BoundedCandidateSelector`.
- Stage 2 `SemanticClassifierPort` is for curriculum semantic features; do not use curriculum taxonomy or review tables as the legal/policy ontology.
- jevcal locks, jev-align workflows, jevQL and jev-tree integrations are already documented/tested; retain their current roles and boundary.
- Existing deterministic parser/policy fallback and richer QuerySession remain available without Jev/provider.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-21"></a>

## Task 21: Определить bounded operations через существующий Jev seam

### Контракт выполнения

- Files: existing module-owned typed operation port only where needed; versioned question-definition artifact under `backend/config/jev/`; extend current `infrastructure/jev/adapter.py`/runtime/composition only for genuinely new registered operations; `backend/evals/jev/` corpora/manifests; architecture tests.
- Reuse `resolve_olympiad_profile` for Olympiad/profile matching; do not add a duplicate operation/client. New claim classification, relation-candidate classification or policy-type recognition may be added only as a new bounded definition with owner-module contracts; deterministic narrowing supplies all candidate IDs and evidence spans.
- Candidate tasks: claim type classification, selection among bounded existing IDs, relation type classification from an allowed registry, source wording to bounded policy type. Inputs are deterministic fields and capped evidence span; output contains an allowed enum/candidate ID, never a newly invented canonical ID.
- Guardrail: deterministic narrowing → current QuestionRegistry definition and TypeSafe transport → registered/calibrated bounded answer → typed ID/schema validation → deterministic domain validation → immutable approval/review when needed. Jev cannot make facts, legal/effective status, SQL, eligibility decisions, relations outside the supplied ontology or arbitrary IDs.
- Reuse: use Stage 2 QuestionRegistry/TypeSafe, timeout/fallback/calibration/telemetry, the existing composition root and operation-specific locks. Do not create `KnowledgeJevClient`, provider abstraction, second registry or second candidate resolver. Keep Jev optional/unavailable without affecting staging/resolver correctness.
- Ошибки и логирование: timeout/schema/calibration/unknown ID gives unresolved and deterministic fallback; redact source body/profile from vendor logs unless separately approved.
- Будущие тесты: allowed ID enforcement, limits/retry/circuit, fallback, calibration lock.
- Критерии приёмки: model cannot change canonical/effective result without validation and an explicit approval event for the exact revision; core has no Jev dependency; existing Stage 2 operations/locks retain their hashes and behavior.
- Будущая проверка: python -m pytest backend/tests/unit/test_jev_adapter.py backend/tests/architecture/test_module_boundaries.py
- Зависимости: Stage 2 baseline and explicit operation-specific capability/evaluation decision in Phase 00.
- Откат: disable adapter; deterministic path continues.
- Риски: reusing an unrelated Stage 2 lock can falsely appear to calibrate a new operation; require operation/definition-specific lock identity and held-out evidence.
- Вне scope: new provider stack or eligibility classifier.

### Task 21 completion evidence (2026-09-26)

- Stage 2 already provides the only currently justified matching operation:
  `resolve_olympiad_profile` through `QuestionRegistry` → TypeSafe transport →
  `JevDecisionModelAdapter` → `JevAdmissionCandidateSelector`. The selector is
  called only for a deterministic candidate set of 2–8 persisted Olympiad
  profile IDs, validates the returned ID against that set, and fails closed
  to unresolved. No second resolver or Jev client was introduced.
- The implemented policy source normalizer deterministically preserves exact
  text offsets, snapshot evidence and a provisional claimed-stage hint; all
  extracted assertions stay `NEEDS_REVIEW`. It does not decide legal status or
  create relations/rules. A relation suggestion has no safe consumer yet:
  `KnowledgeReviewTargetRef` and the immutable action contract have no exact
  relation-revision target, so reviewers cannot approve/reject a relation
  candidate through the current queue. No claim, relation, source-status or
  rule-type Jev operation is registered until an owner review seam exists.
- No Question Registry definition, TypeSafe behavior, Jev runtime/composition,
  feature flag, calibration artifact or calibration lock was changed. In
  the Stage 2 checkout no dedicated Olympiad-profile lock is present; runtime
  requires its own lock path and is disabled by default. Decision/next-action
  locks cannot calibrate profile selection.
- Verification: `backend/tests/infrastructure/test_question_registry.py`,
  `backend/tests/infrastructure/test_jev_adapter.py`, the Jev runtime tests and
  `backend/tests/architecture/test_module_boundaries.py` passed (30 tests).
  The only
  Jev-enabled domain path remains optional; knowledge/policy canonicalization
  and the approved-only resolver do not consume model predictions.

<a id="task-22"></a>

## Task 22: Задать независимый Jev evaluation lifecycle

### Контракт выполнения

- Файлы: extend existing `backend/evals/jev/` harness/exporters/manifests/operation captures; new versioned corpus/labels/report and CI/release gate docs; no separate eval framework.
- Ground truth: independently authored/reviewed before model runs; deterministic synthetic/golden corpus, bounded candidates, held-out split, prompt/model/provider/version hashes and adjudication reason.
- Minimum: at least 500 independently authored deterministic golden synthetic relationship/entity matching cases per production-used matching operation family, if it will affect production staging/canonical decisions. Stage 2 Olympiad-profile or next-action corpora/locks do not satisfy a new operation's corpus. Include ambiguity, near-match, missing target, adversarial relation prompt, paraphrase/typos and non-match strata.
- Metrics: false MATCH, false NO_MATCH, unresolved recall, hallucinated relation, wrong relation type, incorrect override, incorrect scope, incorrect temporal applicability; breakdown by stratum and fail-closed thresholds approved before rollout.
- Будущие тесты: ground-truth manifest exists before inference; leakage/integrity; deterministic report; calibration lock; regression on prompt/model/provider changes.
- Критерии приёмки: predictions are never ground truth; uncalibrated or regressed operation remains shadow/off; false-positive safety gates block use.
- Будущая проверка: extend the Stage 2 Jev evaluation command/harness; reuse current tooling, but do not treat Stage 2 labels/predictions/locks as ground truth for new operations.
- Зависимости: Task 21 and evaluation owner.
- Откат: lock/disable operation; retain prediction audit for offline analysis.
- Риски: independent labels cost time; no production use before corpus and threshold sign-off.
- Вне scope: model-generated labels as ground truth.

### Task 22 completion evidence (2026-09-26)

- Reused the existing Stage 2 evaluator and the separately stored,
  versioned Olympiad/profile v2 cases and provider observations. Added
  `backend/evals/jev/manifests/knowledge-policy-gates.v1.json`, which binds
  the existing operation definition and golden corpus hashes, records its
  120 cases and 58/62 train/heldout split, states the source-backed
  deterministic label origin, and records the missing operation-specific
  calibration lock as production-ineligible. Provider observations are not
  copied into the expected labels.
- No policy-specific operation is registered, so there is no policy model
  prediction to evaluate and no dummy corpus was added. The manifest freezes
  the lifecycle required before a future operation can be registered:
  independent ground truth before inference, at least 500 synthetic golden
  matching cases for production staging/canonical use, ambiguity/adversarial
  strata, required false-positive/unresolved metrics, operation artifact
  hashes and off/shadow-only failure behavior.
- Added dependency-free manifest/corpus integrity tests; those and Question
  Registry tests passed (12 tests). Optional `jevcal` calibration tests were
  attempted but the global Python environment lacks `jevcal`; an offline
  locked evaluation-extra run could not install it because the cached
  `scipy==1.17.1` wheel is unavailable and network access is disabled. Those
  calibration tests are not reported as passing. Jev remains uncalibrated and
  production-disabled.

<a id="task-23"></a>

## Task 23: Добавить shadow rollout и Jev audit

### Контракт выполнения

- Файлы: existing Jev/Question Registry composition and settings; operation-specific opt-in capability flag/lock path (future implementation only); candidate audit metadata; operator metrics/docs; integration tests.
- Шаги: preserve all Stage 2 defaults and locks; deterministic-only baseline; new operation shadow predictions hidden from applicant and canonical output; compare with independent reviewers/golden labels; assisted candidate selection only after Task 22; relation/rule still requires deterministic validation and exact-revision approval. This plan does not enable any existing/new Jev flag or change calibration lock.
- Observability: operation ID, candidate IDs, model/provider/prompt version, latency/error/calibration state, outcome/reviewer label; redact body/PII. Calibration locks change only through separate release decision.
- Критерии приёмки: off/shadow/assisted states are separate; timeout has deterministic fallback; no prediction is automatically applied.
- Будущие тесты: flags, lock state, provider unavailable, stale prompt regression.
- Будущая проверка: approved Jev eval gate plus backend integration suite.
- Зависимости: Tasks 21-22 and operations decision.
- Откат: turn operation off; shadow artifacts remain audit-only.
- Риски: confidence can be mistaken for truth; UI labels predictions and keeps human reviewer responsible.
- Вне scope: enabling new production operations in this planning iteration.

### Task 23 completion evidence (2026-09-26)

- The gate manifest records knowledge/policy rollout as `off`; there is no
  policy-specific operation or exact relation-review consumer to shadow. No
  runtime setting, Jev flag, calibration lock or applicant path was added or
  enabled. Existing Jev defaults and Stage 2 locks remain unchanged.
- Added an explicit future audit-field contract: operation/definition
  identity and version, candidate-set hash, prompt hash, provider/model,
  operation-specific lock identity, latency, error/fallback, reviewer outcome
  and timestamp. Raw source text and applicant profile data are forbidden in
  this audit record.
- Added a regression that the existing admissions selector is disabled under
  default `Settings`, alongside the existing missing-lock fail-closed test.
  Knowledge/policy stays deterministic and approved-only; no prediction is
  surfaced or applied.
- Combined Jev registry/adapter/runtime, policy evaluation gate and
  architecture boundary verification: 34 tests passed. Focused Ruff passed;
  `git diff --check` passed with only Git's existing CRLF conversion notices.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
