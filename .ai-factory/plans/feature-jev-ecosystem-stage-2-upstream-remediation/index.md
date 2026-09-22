<!-- aif:plan-mode:ultra -->
# Ultra Implementation Plan: Stage 2 upstream Jev ecosystem remediation

Mode: ultra
Branch: `feature/jev-ecosystem-stage-2`
Target HEAD: `105dacb029a6b38a27aed5c16affb359189d609e` (`105dacb`)
Created: 2026-09-22
Status: implementation complete; all planned tasks are checked below.

## Original Request

aif-plan ultra

Работай ТОЛЬКО с текущей веткой `feature/jev-ecosystem-stage-2`, текущий HEAD `105dacb`. Это remediation/fix pass поверх уже реализованного Stage 2. Не перестраивай архитектуру заново, не создавай новые параллельные слои и не переписывай Semantic Layer, AnalyticsEngine, QueryFrame/QuerySession, DecisionModelPort, QuestionRegistry, ResponsePlan или существующие typed ports.

Цель — довести Stage 2 от архитектурной подготовки до реальной интеграции upstream Jev ecosystem, используя настоящий код библиотек, а не локальные имитации. Обязательно проверить текущий код и upstream source для jevcal, jev-align, System One Adapter, jevQL, jev-tree и official TypeSafe SDK. Исправить реальное использование jevcal, runtime calibration gate, недостаточный calibration corpus, реальное использование jev-align, production Jev client, embedded-first jevQL, deterministic narrowing перед jev-tree, разделение Shared Question Registry и tool-specific configs, а System One Adapter оставить только eval-интеграцией. План должен быть подробным, repository-grounded, implementation-ready; в рамках этой команды код не реализовывать.

## Settings

- Testing: yes
- Logging: verbose during implementation, production-safe structured logging
- Docs: yes, after the corresponding implementation phase
- Database migrations: no new schema change is planned for this remediation; existing Alembic head remains unchanged unless implementation evidence proves a storage change unavoidable.
- Branch policy: no checkout, merge, rebase, push, or worktree creation; all later implementation is constrained to the branch and baseline above.

## Scope Anchor and Baseline

This bundle is a new remediation plan. The previous bundle at `.ai-factory/plans/feature-jev-ecosystem-stage-2/` remains historical Stage 2 planning context and must not be overwritten. Its architectural seams are inputs, not permission to repeat the Stage 2 build. The first implementation checkpoint must prove that the worktree is still clean at `105dacb` before any code change.

## Research Context

The repository audit and upstream source audit were performed against the current branch and these pinned upstream revisions:

| Ecosystem component | Upstream revision inspected | Verified role | Planned integration mode |
|---|---|---|---|
| [jevcal](https://github.com/abhixhek/jevcal/tree/ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f) | `ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f` | calibration metrics, compile/lock, runtime Cascade, check | real optional evaluation dependency behind thin Andromeda loader/CI wrapper |
| [jev-align](https://github.com/sutro-sh/jev-align/tree/3d997fc76593036655c28d4964de43b55f81fe2c) | `3d997fc76593036655c28d4964de43b55f81fe2c` | uncertainty acquisition, human labels, GEPA candidate, pending/accept gate | real upstream driver behind existing semantic review boundary |
| [System One Adapter](https://github.com/typesafe-ai/system-one-adapter-python/tree/adffc2eab300a4fa3c0e92252d4ffd6ceaa53700) | `adffc2eab300a4fa3c0e92252d4ffd6ceaa53700` (`v0.2.0`) | external-model/eval adapter | eval-only; never production domain dependency |
| [jevQL](https://github.com/kylemclaren/jevql/tree/274532af852e8edfb7715ec6dca1113e589cb191) | `274532af852e8edfb7715ec6dca1113e589cb191` | embedded Python SDK, private/shared engine, SQL/judge cache | existing `SemanticPredicatePort` adapter; embedded SDK first, configured process/service fallback |
| [jev-tree](https://github.com/reachjalil/jev-tree/tree/95bff63bd653fee4dc71f33f9431dce0f81e2ca3) | `95bff63bd653fee4dc71f33f9431dce0f81e2ca3` (`npm 0.1.0`) | bounded hierarchical selection | keep existing Node bridge and adapter; add provenance/smoke/threshold proof |
| [official TypeSafe SDK](https://github.com/typesafe-ai/typesafe-sdk-python/tree/0ffd094c72ed9445223060b24ed7a56aa781fb4) | `0ffd094c72ed9445223060b24ed7a56aa781fb4` (`v0.7.1`) | production `TypeSafeClient.system_one`, typed answers, model list/usage | real production client behind existing `DecisionModelPort` adapter |

The upstream audit is repository-grounded rather than README-only: the inspected source exposes jevcal `compile_question`, `build_lock`, `runtime.Cascade` and `check`; jev-align `ClimbSession`, `RunStore`, `acquire`, `add_label`, `optimize`, `decide`, and `build_function_artifact`; jevQL `Jevql`, `judge`, `query`, `health`, and `close`; jev-tree `createJevTree`; and TypeSafe SDK `TypeSafeClient`, `ChoiceAnswer.probabilities`, `NoulAnswer`, `models.list()` and typed usage.

## Confirmed / Partial / Incorrect Hypotheses

| Hypothesis | Verdict | Evidence and consequence |
|---|---|---|
| 22 broad discipline areas and many-to-many area weights already exist | Confirmed | Current `discipline_area_weights`, `DisciplineAreaCode`, and comparison/fingerprint consumers remain untouched. |
| `FingerprintBuilder` aggregates area workload from hours/credits into `ProgramFingerprint` | Confirmed | Existing proftest/program analytics code is a compatibility source; this remediation does not extract or rename it. |
| `AdaptiveQuestionSelector` is useful adaptive logic | Confirmed, bounded | It remains proftest-specific; do not make it the generic Jev dialogue policy. |
| `DecisionContext` must remain explicit user choice, not conversation memory | Confirmed | QueryFrame/QuerySession already own generic state; no new state layer is introduced. |
| OG renderer and Telegram `RendererClient` are presentation patterns | Confirmed | Existing ResponsePlan and rendering seams remain; no Jev/tool-specific UI is added. |
| `decision_analytics` is catalog analytics | Incorrect | It is action telemetry; it must not be reused for calibration/catalog metrics. |
| BMSTU/HSE ingestion must be Jev-independent | Confirmed | No source adapter, canonical transaction, repository, or Alembic migration receives Jev imports. |
| Stage 2 already uses upstream jevcal | Incorrect | `backend/scripts/jevcal_calibrate.py` implements local threshold/ECE logic; `TOOLS.lock` only records a commit. |
| Stage 2 already uses upstream jev-align | Incorrect | `backend/scripts/jev_align_workflow.py` owns local export/review/publish and does not call upstream uncertainty/GEPA. |
| Current TypeSafe integration is entirely fake | Incorrect / partial | `typesafe_client.py` does call `TypeSafeClient`, but pins stale `0.6.0`, does not expose raw probability evidence to a trust gate, and hardcoded confidence buckets are not calibration acceptance. |
| Current jevQL embedded integration is real | Incorrect | It looks for nonexistent public `jevql.EmbeddedClient`; upstream Python SDK exposes `Jevql`. Private/shared payloads also do not implement the upstream protocol. |
| Current jev-tree is an architectural imitation | Incorrect / partial | The Node bridge calls actual `createJevTree`; deterministic narrowing and the `>255` candidate threshold already prevent calls for small sets. Add proof and packaging checks, not a redesign. |
| Current calibration corpus is production evidence | Incorrect | The current fixture has three observations per definition with one held out; it is wiring evidence only. |

## Current Repository State

The current Stage 2 code already contains the reusable boundaries that this pass must preserve:

```text
QuestionRegistry
  ├─ DecisionModelPort → JevDecisionModelAdapter → TypeSafeJevTransport
  ├─ SemanticPredicatePort → jevQL transports/adapter
  ├─ HierarchicalResolutionService → JevTreeAdapter → Node bridge
  └─ SemanticReviewWorkflow / QueryFrame / QuerySession / ResponsePlan
```

The important current paths are:

- `backend/src/andromeda/infrastructure/jev/question_registry.py` and `backend/config/jev/question-definitions.v1.yaml` — shared definitions, instructions, criteria, versions, options, fallback and timeout policy.
- `backend/src/andromeda/infrastructure/jev/adapter.py`, `runtime.py`, and `typesafe_client.py` — provider adapter, startup lock validation, official-client wrapper, typed fallback path.
- `backend/scripts/jevcal_export.py` and `jevcal_calibrate.py` — current local export/calibration implementation to replace with upstream invocation.
- `backend/scripts/jev_align_workflow.py` — current local semantic review workflow to reduce to an upstream jev-align driver plus existing human approval boundary.
- `backend/src/andromeda/infrastructure/jevql/{config,transport,adapter}.py` — existing optional semantic predicate seam; transport implementation is the remediation target.
- `backend/src/andromeda/infrastructure/jev_tree/{config,transport,adapter}.py`, `backend/jev-tree-bridge/src/index.mjs`, and `backend/jev-tree-bridge/package-lock.json` — actual jev-tree integration and its reproducibility boundary.
- `backend/evals/jev/system_one_evaluator.py` — evaluation-only System One path; it must use the actual v0.2.0 API but must not become runtime business logic.
- `backend/pyproject.toml`, `backend/uv.lock`, and `backend/evals/jev/TOOLS.lock` — dependency and provenance changes.
- `docs/architecture/integration-seams.md`, `docs/architecture/jev-rollout.md`, `backend/evals/jev/README.md`, `docs/testing.md`, and `.github/workflows/andromeda-ci.yml` — documentation and CI gates.

## Architectural Decisions

1. **No new bounded context.** Remediation changes stay inside existing `infrastructure/jev`, `infrastructure/jevql`, `infrastructure/jev_tree`, `evals/jev`, scripts, configuration, CI and docs.
2. **Question Registry remains the semantic source of truth** for definition id/version, instructions, criteria, expected input/output and fallback. Tool-specific jevcal, jev-align, jev-tree and System One configuration may remain separate adapters/config files and must not be forced into one universal schema.
3. **Calibration is an upstream artifact, not a second local confidence engine.** Andromeda stores and validates the real jevcal lock plus a small manifest; it does not reimplement threshold selection, ECE, confidence measures or GEPA.
4. **Runtime trust is a per-definition gate.** Raw TypeSafe probabilities/confidence flow into the upstream jevcal-compatible runtime decision. UI confidence buckets remain telemetry only and cannot accept a production Jev decision.
5. **Fixture and production calibration datasets are separate.** Fixture data proves schema/wiring. Production enablement requires configurable minimum support/heldout evidence, model and definition compatibility, and an explicit non-shadow status.
6. **jev-align proposes; people publish.** Upstream uncertainty selection and GEPA produce a pending proposal. Existing human approval publishes a new semantic version and triggers controlled rebuild. No automatic semantic mutation is allowed.
7. **Production Jev uses the official TypeSafe SDK.** System One Adapter is evaluation-only and does not satisfy the production-client requirement.
8. **jevQL is upstream-SDK-only and platform-aware.** Use `Jevql()` for the upstream embedded/private engine path; use `Jevql(url=..., token=...)` for an explicitly configured shared service; otherwise return unavailable and use deterministic fallback. Do not create an Andromeda-owned process protocol or bespoke HTTP client when the upstream SDK already owns both modes.
9. **jevQL consumes bounded candidate rows, not model-generated SQL.** Stable/materialized metrics are used first. Runtime semantic judging is permitted only for a registered, unmaterialized predicate after deterministic narrowing and row/size budgets.
10. **jev-tree remains a last-stage selector.** It is called only after deterministic narrowing and only when the candidate set exceeds the configured threshold; a set of 20 programs must never invoke it.
11. **No Alembic migration is planned.** Calibration locks, reports and jev-align run artifacts are versioned files/artifacts, not canonical database facts. If implementation discovers a schema requirement, it is a blocking decision and cannot be silently added.
12. **Fail closed.** Missing/stale/incompatible lock, unavailable provider, malformed external output, unsupported platform or exceeded budget returns deterministic fallback/unresolved or an explicit unavailable result; it never silently treats uncertainty as approval or missing data as zero.

## Target Data and Control Flow

```text
QuestionRegistry + eval corpus exporter
        ├─ jevcal CLI/API → real decisions.lock.json + report
        │                         ↓
        │                  CalibrationLoader → ConfidenceGate
        └─ System One Adapter / deterministic fixtures (eval only)

QuestionRegistry + sanitized semantic stories
        → upstream jev-align ClimbSession.acquire/add_label/optimize
        → pending proposal
        → existing human review
        → new semantic version + controlled rebuild

canonical/materialized metric rows
        → deterministic narrowing
        → registered semantic predicate
        → real jevQL.Jevql.judge (embedded/private/shared)
        → existing SemanticPredicateResult

canonical entity candidates
        → deterministic narrowing
        → JevTreeAdapter only for large candidate sets
        → canonical id/hash validation

official TypeSafeClient.system_one
        → typed raw probability observation
        → per-definition CalibrationGate
        → DecisionModelPort typed decision or deterministic fallback
        → existing QueryFrame/QuerySession/ResponsePlan
```

## Phase Index

1. [Phase 01: Baseline, upstream pins and dependency proof](phase-01-baseline-and-dependencies.md) — Tasks 1–3
2. [Phase 02: Shared exports and evaluation corpus](phase-02-shared-exports-and-eval.md) — Tasks 4–5
3. [Phase 03: TypeSafe client, jevcal artifact and runtime gate](phase-03-jevcal-runtime-gate.md) — Tasks 6–9
4. [Phase 04: Real jev-align semantic loop](phase-04-jev-align-semantic-loop.md) — Tasks 10–11
5. [Phase 05: Production decision-policy wiring](phase-05-production-typesafe-client.md) — Task 12
6. [Phase 06: Real jevQL runtime](phase-06-jevql-runtime.md) — Tasks 13–15
7. [Phase 07: jev-tree proof, integrated evaluation and rollout](phase-07-tree-evaluation-rollout.md) — Tasks 16–19

## Cross-Phase Dependencies

- Task 1 is the baseline gate for every later task; no implementation may proceed if branch or HEAD drift is detected.
- Task 2 must precede Tasks 4, 6, 7, 10 and 13 because lockfiles and optional groups determine reproducible imports.
- Task 3 defines the registry-to-tool mapping consumed by both jevcal and jev-align; it must not create duplicate definition ownership.
- Tasks 4–5 produce the exact datasets and typed evaluation observations consumed by Tasks 7–9 and 17.
- Task 6 upgrades the official TypeSafe SDK before any jevcal artifact is consumed by runtime code.
- Tasks 7–9 must complete in order: real upstream jevcal artifact, direct `jevcal.runtime.Cascade` reuse, then fixture/production enablement; a real client without a fail-closed gate is not a valid rollout.
- Tasks 10–11 depend on the shared corpus/registry and existing semantic review owner; they must complete before semantic-derived production rebuilds are permitted.
- Task 12 depends on Tasks 6, 8 and 9 and wires the already-validated client/gate into `DecisionModelPort` without creating a second gate.
- Tasks 13–15 depend on Task 2 and preserve `SemanticPredicatePort`; Task 15 verifies metric-first routing from existing AnalyticsEngine/materialized projections.
- Task 16 is deliberately isolated and depends only on current jev-tree adapter/bridge behavior; it must not block unrelated deterministic flows.
- Tasks 17–19 are final gates and depend on all prior tool integrations, exact pins, test fixtures and documentation facts.

## Tasks

### Phase 01: Baseline, upstream pins and dependency proof

- [x] Task 1: Freeze the remediation baseline and audit manifest ([details](phase-01-baseline-and-dependencies.md#task-1-freeze-the-remediation-baseline-and-audit-manifest))
- [x] Task 2: Pin real upstream packages and prove reproducible installation ([details](phase-01-baseline-and-dependencies.md#task-2-pin-real-upstream-packages-and-prove-reproducible-installation)) (depends on 1)
- [x] Task 3: Add a registry-to-tool export contract without duplicating Question Registry ownership ([details](phase-01-baseline-and-dependencies.md#task-3-add-a-registry-to-tool-export-contract-without-duplicating-question-registry-ownership)) (depends on 1, 2)

### Phase 02: Shared exports and evaluation corpus

- [x] Task 4: Export the registry/corpus into the exact upstream jevcal input format ([details](phase-02-shared-exports-and-eval.md#task-4-export-the-registrycorpus-into-the-exact-upstream-jevcal-input-format)) (depends on 2, 3)
- [x] Task 5: Make System One Adapter evaluation use the real v0.2.0 API and shared registry ([details](phase-02-shared-exports-and-eval.md#task-5-make-system-one-adapter-evaluation-use-the-real-v020-api-and-shared-registry)) (depends on 2, 3)

### Phase 03: TypeSafe client, jevcal artifact and runtime gate

- [x] Task 6: Upgrade the official TypeSafe SDK adapter before calibration wiring ([details](phase-03-jevcal-runtime-gate.md#task-6-upgrade-the-official-typesafe-sdk-adapter-before-calibration-wiring)) (depends on 2, 5)
- [x] Task 7: Invoke upstream jevcal to produce the real calibration artifact ([details](phase-03-jevcal-runtime-gate.md#task-7-invoke-upstream-jevcal-to-produce-the-real-calibration-artifact)) (depends on 4, 5, 6)
- [x] Task 8: Reuse jevcal.runtime.Cascade for the per-definition fail-closed runtime gate ([details](phase-03-jevcal-runtime-gate.md#task-8-reuse-jevcalruntimecascade-for-the-per-definition-fail-closed-runtime-gate)) (depends on 6, 7)
- [x] Task 9: Separate fixture calibration from production enablement and stale-lock checks ([details](phase-03-jevcal-runtime-gate.md#task-9-separate-fixture-calibration-from-production-enablement-and-stale-lock-checks)) (depends on 7, 8)

### Phase 04: Real jev-align semantic loop

- [x] Task 10: Replace local uncertainty/optimization logic with upstream jev-align ClimbSession ([details](phase-04-jev-align-semantic-loop.md#task-10-replace-local-uncertaintyoptimization-logic-with-upstream-jev-align-climbsession)) (depends on 2, 3, 9)
- [x] Task 11: Keep human approval as the semantic publish gate and version controlled rebuild ([details](phase-04-jev-align-semantic-loop.md#task-11-keep-human-approval-as-the-semantic-publish-gate-and-version-controlled-rebuild)) (depends on 10)

### Phase 05: Production decision-policy wiring

- [x] Task 12: Wire production Jev health, calibration compatibility and deterministic fallback ([details](phase-05-production-typesafe-client.md#task-12-wire-production-jev-health-calibration-compatibility-and-deterministic-fallback)) (depends on 6, 8, 9)

### Phase 06: Real jevQL runtime

- [x] Task 13: Replace the fake EmbeddedClient path with upstream Jevql.judge ([details](phase-06-jevql-runtime.md#task-13-replace-the-fake-embeddedclient-path-with-upstream-jevqljudge)) (depends on 2)
- [x] Task 14: Use the upstream Jevql SDK for embedded/private and shared modes ([details](phase-06-jevql-runtime.md#task-14-use-the-upstream-jevql-sdk-for-embeddedprivate-and-shared-modes)) (depends on 13)
- [x] Task 15: Enforce materialized-metric priority, wire jevQL into AnalyticsExecutor and add security/observability ([details](phase-06-jevql-runtime.md#task-15-enforce-materialized-metric-priority-wire-jevql-into-analyticsexecutor-and-add-securityobservability)) (depends on 13, 14)

### Phase 07: jev-tree proof, integrated evaluation and rollout

- [x] Task 16: Wire jev-tree into EntityResolver and prove large-candidate-only invocation ([details](phase-07-tree-evaluation-rollout.md#task-16-wire-jev-tree-into-entityresolver-and-prove-large-candidate-only-invocation))
- [x] Task 17: Run one source-backed evaluation harness through deterministic, Jev and System One paths ([details](phase-07-tree-evaluation-rollout.md#task-17-run-one-source-backed-evaluation-harness-through-deterministic-jev-and-system-one-paths)) (depends on 5, 9, 12, 15, 16)
- [x] Task 18: Add CI gates, optional external smoke checks and architecture boundary checks ([details](phase-07-tree-evaluation-rollout.md#task-18-add-ci-gates-optional-external-smoke-checks-and-architecture-boundary-checks)) (depends on 2, 7, 10, 13, 16, 17)
- [x] Task 19: Update integration documentation and perform final rollout/rollback verification ([details](phase-07-tree-evaluation-rollout.md#task-19-update-integration-documentation-and-perform-final-rolloutrollback-verification)) (depends on 12, 15, 17, 18)

## Commit Plan

- **Commit 1** after Tasks 1–3: `chore(jev): pin upstream ecosystem and freeze stage2 remediation baseline`
- **Commit 2** after Tasks 4–6: `feat(jev): pin production typesafe client and evaluation contracts`
- **Commit 3** after Tasks 7–9: `feat(jevcal): enforce real cascade calibration artifact at runtime`
- **Commit 4** after Tasks 10–11: `feat(jev-align): connect active learning to human semantic review`
- **Commit 5** after Task 12: `feat(jev): wire production policy behind calibrated gate`
- **Commit 6** after Tasks 13–15: `feat(jevql): use upstream embedded judge with bounded fallbacks`
- **Commit 7** after Tasks 16–19: `test(jev): verify ecosystem integrations and rollout guards`

Every commit must be independently runnable, must not include unrelated Stage 2 changes, and must pass the phase-specific tests before the next checkpoint.

## Blocking Open Questions

1. **Production jevcal support size:** the implementation must read the actual upstream minimum-support behavior and configure the production minimum from that evidence; it must not invent a target sample size. Fixture mode may run with the current tiny corpus only for schema/wiring.
2. **jevQL Windows deployment:** upstream embedded wheels do not include Windows in the inspected package matrix. Implementation must choose the configured private/shared fallback or explicit unavailable status for the deployment environment after checking CI/runtime OS. It must not create a local replacement engine.
3. **Official TypeSafe endpoint:** the adapter must use the configured official TypeSafe-compatible endpoint and model naming already supported by current deployment configuration. If the current secret/endpoint contract cannot satisfy SDK v0.7.1, implementation must stop at configuration migration and not bypass the SDK with a bespoke HTTP client.

These are bounded implementation gates, not permission to redesign the architecture.

## Definition of Done

- The branch remains `feature/jev-ecosystem-stage-2` and the implementation starts from `105dacb` without mixing the prior university-admin or Stage 2 baseline changes.
- `jevcal` and `jev-align` are real pinned upstream dependencies/tools invoked by the repository; local threshold/ECE/uncertainty/GEPA implementations are removed or reduced to adapters/exporters/validators.
- A real jevcal lock/report is produced, validated against registry/model/version/corpus metadata, and per-definition thresholds actually decide Jev acceptance versus deterministic fallback.
- Production Jev uses official TypeSafe SDK code; System One Adapter is evaluation-only.
- jevQL uses the real Python `Jevql` API or an explicitly configured upstream-compatible process/service, with embedded-first behavior where supported and no model-generated SQL.
- jev-tree is called only after deterministic narrowing for genuinely large candidate sets and its package/runtime provenance is tested.
- Fixture evidence cannot enable production; stale, insufficient, incompatible or unavailable external artifacts fail closed.
- Existing Semantic Layer, AnalyticsEngine, QueryFrame/QuerySession, DecisionModelPort, QuestionRegistry, ResponsePlan, canonical ingestion, repositories, database schema and public flow contracts remain intact.
- Relevant unit, integration, architecture, CI, documentation and rollback checks pass; no implementation task remains vague or delegated to inference.
