# Phase 00: Исходный baseline и архитектурные gates

Plan: [index.md](index.md)
Tasks: 1-2
Depends on: none

## Цель

Перед первым runtime change зафиксировать исполняемый baseline, решить судьбу незакоммиченного worktree и принять решения о владельцах данных, источниках авторитета и human approval. Обычный production код этой фазы не меняет.

## Current-Code Evidence

| Path | Symbols / state | Why it matters |
|---|---|---|
| Git state | Плановая checkout `feature/andromeda-education-policy-knowledge` remains at `efc1699772400f71c8cef0004b1ef8ca4f6cb1b8`, the same source commit as `feature/semantic-catalog-analytics-baseline`; it is not the implementation base | Keep plan artifacts here; do not implement from this branch |
| Git state | At reconciliation start the worktree had 122 status entries (63 tracked paths plus untracked data/plan artifacts) | Preserve all pre-existing changes; do not use this dirty worktree for implementation |
| Git remote | `git ls-remote` and `origin/feature/jev-ecosystem-stage-2` both resolve to `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`; this adds 29 commits / 294 changed paths over the previous baseline | Stage 2 is the selected current code baseline, not a future merge candidate |
| Plan visibility | Stage 2 contains neither this plan bundle nor the linked `.ai-factory/research/universal-educational-analytics/RESEARCH.md`; `$aif-implement` accepts an explicit `@path` override | Carry only the plan/research artifact allowlist in a plan-only commit and invoke the bundle by explicit path |
| Database | Stage 2 migration chain ends at `0038_admission_offering_scope_and_exam_choices`; 0036-0038 already add benefit source coverage, applicant category, campus scope and exam-choice groups | Future migrations continue additively from current Stage 2 after checking deployed database heads |
| Jev runtime | `QuestionRegistry`, `TypeSafeJevTransport`, `CascadeCalibrationAdapter`, Jev runtime/composition, `JevAdmissionCandidateSelector`, hierarchical resolution and eval tooling are present | Extend through current typed seams; do not recreate or enable them in this plan |
| Source ingestion | `RawSourceSnapshot`, content-addressed `SourceSnapshotModel`, `IngestRun`, retry/idempotency/heartbeat and university adapters are present | Reuse capture/persistence; do not add a second snapshot/provenance store |
| Review | `SemanticReviewWorkflow` has hashed proposals, stale-source checks, reviewer/time and publish-after-review; it is curriculum-semantic-specific, not a durable general policy approval ledger or operator UI | Reuse invariants only; policy has its own minimal immutable approval contract |
| Scheduling | `.github/workflows/source-health.yml` is a scheduled read-only probe; `deploy/yc/compose.yaml` has no ingestion worker | Health monitoring is precedent, not policy-document polling or its production scheduler |
| docs/architecture.md | modular monolith, AndromedaContainer, source adapters | Сохраняет runtime boundaries |
| .ai-factory/plans/feature-universal-educational-analytics/index.md | Status complete; ownership/query contracts | Важен для reuse, но не заменяет checkout |
| .ai-factory/plans/feature-admission-benefits-special-rights/index.md | Status complete; admission_benefits owner | Ранее выбранные benefit contracts не перепроектировать с нуля |

## Файлы для изменения

| Path | Action | Required change |
|---|---|---|
| docs/architecture/knowledge-policy.md | create | Зафиксировать одобренные решения и implementation baseline |
| `.ai-factory/plans/feature-andromeda-education-policy-knowledge/**` | stage/carry unchanged in a plan-only commit | Include `index.md` and the 15 direct phase files only |
| `.ai-factory/research/universal-educational-analytics/{INDEX.md,RESEARCH.md,C4-CONTAINER.md,C4-CONTEXT.md,DEPENDENCY-GRAPH.md}` | stage/carry unchanged in the same plan-only commit | These exact linked source artifacts preserve the plan's hashed Research Context and research-bundle entrypoint; no other dirty research files |
| Runtime, migrations, API | none in Task 1 | Establish and record the green Stage 2 baseline before the first runtime change |

<a id="task-1"></a>

## Task 1: Перенести plan bundle на clean Stage 2 ветку и подтвердить green baseline

### Intent

Сделать bundle видимым `$aif-implement` в новой implementation branch без merge старой planning branch, затем доказать, что кодовая база Stage 2 была green до первого runtime изменения. Не потерять и не включить случайно остальные пользовательские изменения из dirty planning checkout.

### Implementation Steps

1. Re-check `git ls-remote origin refs/heads/feature/jev-ecosystem-stage-2`, its tracking ref and exact SHA; record planning branch/HEAD/status and preserve all existing staged, tracked and untracked paths. Do not switch, reset, rebase, stash or clean the planning checkout.
2. Validate the exact artifact allowlist: `.ai-factory/plans/feature-andromeda-education-policy-knowledge/` (index plus 15 direct phase files) and the five named linked research-bundle files. Confirm the embedded `Research Context` SHA256 matches the source `Active Summary`; do not include any other untracked plans, reports, data or runtime files.
3. Stage only that allowlist on the planning branch; inspect `git diff --cached --name-only`, `--stat` and `--check`. Create one `docs(plan): reconcile policy knowledge plan with Stage 2` plan-only commit. Its complete file list must be contained in those two allowlisted planning/research paths; do not commit any runtime code or the old branch's unrelated changes.
4. Create a new clean worktree and implementation branch directly from verified Stage 2 SHA `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`; cherry-pick only the plan-only commit. Do not merge the planning branch. Confirm the picked commit's parent is the selected Stage 2 baseline, and that `git diff --name-only <Stage-2-SHA>..HEAD` contains only the plan bundle and those five linked research artifacts. No Python, migration, API, generated-client or other runtime path may appear.
5. Run `$aif-implement @.ai-factory/plans/feature-andromeda-education-policy-knowledge/index.md` (or the bundle directory) so discovery does not depend on implementation branch naming. Confirm it resolves this ultra marker and its 15 linked phases.
6. Before any runtime edit, establish baseline green on this clean branch: `git diff --check`; run the Stage 2 canonical `python scripts/andromeda.py full` gate from repository root; inspect `alembic heads --verbose` and `alembic history --verbose` from `backend/`; verify the exact Stage 2 commit's required CI jobs are green, including PostgreSQL/browser jobs when they are not covered by local `full`.
7. Record the Stage 2 code SHA, plan-only commit SHA, exact commands/results and a commit-bound CI run URL/ID in the implementation task/PR handoff (no new repository report). If any required baseline gate fails or CI evidence is missing, stop before changing runtime code and classify the failure as baseline or environment state.

### Required Interfaces and Contracts

- Reuse Stage 2 `DecisionModelPort`, `QuestionRegistryPort`/`QuestionRegistry`, `TypeSafeJevTransport`, `CascadeCalibrationAdapter`, `JevDecisionModelAdapter`, `JevAdmissionCandidateSelector`, `AndromedaContainer` wiring and current semantic/entity-resolution ports. Do not create another Jev client, question registry, calibration framework or composition root.
- Add new Jev definitions and calibration artifacts only as separately versioned, operation-scoped additions after independent evaluation. Do not modify existing lock artifacts or enable any Jev flag in this plan. A Jev choice can propose only an ID from a bounded persisted set and can never change canonical or resolver state.
- `policy` remains a deterministic resolver/selector. It never calculates BVI, 100-point Olympiad benefits, confirmation, benefit validity, individual-achievement eligibility or points; those outcomes are delegated to the current domain owner/evaluator.
- Artifact contract: carry only the plan bundle and the five exact files that make its linked research bundle valid; cherry-pick that artifact-only commit onto a branch whose parent is the verified Stage 2 SHA. Use explicit `@.ai-factory/plans/feature-andromeda-education-policy-knowledge/index.md`; do not depend on branch-name auto-discovery.
- Baseline contract: no runtime task starts until canonical full local checks and required SHA-bound CI checks pass on the clean Stage 2-derived branch, except the one explicitly user-accepted environment limitation recorded below for exact code SHA `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`. Any later baseline must satisfy the canonical full gate or receive its own explicit user decision. Record results against the Stage 2 code SHA, not merely the new plan-only commit SHA.

### Error Handling and Logging

- Plan-only commit includes an unexpected path, cherry-pick changes code, branch parent differs from Stage 2, or plan lookup fails → stop; do not merge the old branch or guess a replacement plan path.
- Any red/missing baseline check stops all runtime work, except the exact SHA-specific environment limitation accepted by the user and recorded below; retain command output/CI link and classify baseline versus environment failure before proceeding.
- Any remote/deployed migration-head drift stops the dependent schema work and requires normal reconciliation; never rewrite published history.
- Во время этой read-only сверки не печатать environment secrets, полный source body, cookies или токены.

### Tests

- Future Task 1 gates, run before any runtime edit: `git diff --check`; from repository root `python scripts/andromeda.py full` (Stage 2 canonical local backend, architecture, mypy, OpenAPI drift, frontend unit/lint/build, ingestion, migrations and smoke gates); from `backend/`, `uv run --locked --extra dev python -m alembic heads --verbose` and `uv run --locked --extra dev python -m alembic history --verbose`; verify all required CI jobs for exact code SHA `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`, including CI-only PostgreSQL/browser checks. Keep `git status --short` clean after generated checks.
- This reconciliation runs none of those tests/builds/migration commands; the list is for future implementation Task 1 only.

### Acceptance Criteria

- The plan is discoverable in the implementation worktree through the explicit `@` path; the plan-only cherry-pick contains only the allowlisted plan/research artifacts, and no old runtime code was merged.
- The new worktree is clean, derived from Stage 2 SHA `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`, with the plan-only commit as its only added commit before implementation.
- All listed local gates and required CI checks are green before any runtime change, or the user explicitly accepts the exact SHA-specific environment limitation recorded below; evidence records code SHA, plan commit SHA, migration head 0038, commands/results and CI run.
- Existing planning-worktree edits remain untouched except for the explicitly allowlisted plan-only commit; all other pre-existing paths remain unstaged/uncommitted.

### Verification

- Verify `git rev-parse HEAD^` in the implementation branch equals the selected Stage 2 SHA before implementation begins, and inspect the plan-only commit's full path list against the allowlist.
- Verify explicit `$aif-implement @.../index.md` resolves one ultra marker and all phase files.
- Confirm the required baseline commands and commit-bound CI run pass at the Stage 2 code SHA; if not, no implementation task is unblocked unless the user explicitly accepts the documented environment limitation for that exact SHA.
- Verify the existing planning checkout and its pre-existing user paths were not changed beyond the exact plan/research paths included in the plan-only commit.

### Task 1 completion evidence (2026-09-25)

- Code baseline: `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`; implementation branch `codex/andromeda-education-policy-knowledge` parent is this SHA. Plan-only artifact commit: `8fab087de2e438d8239d64b14290aab5fc345e45`; its changed paths are the approved plan/research allowlist only. Current HEAD is that artifact commit before implementation changes.
- Hosted CI for the exact Stage 2 code SHA completed green: [workflow run 42](https://github.com/artemnoor/andromeda/actions/runs/35992252146), including backend, Jev offline, PostgreSQL integration, browser/frontend, packaging and fullstack jobs.
- Local checks passed against the clean Stage 2-derived source tree: backend `python -m pytest -q` (926 passed, 9 skipped); architecture tests (35 passed); Alembic linear history/head (`0038_admission_offering_scope_and_exam_choices`); frontend unit (25 passed), lint, production build and generated OpenAPI drift. `git diff --check` passed. Frontend-generated `next-env.d.ts` was restored and the worktree was clean after baseline checks.
- `python scripts/andromeda.py full` could not complete locally because the environment could not resolve Jev dependencies and PyPI DNS (`files.pythonhosted.org`) failed. Existing-environment mypy likewise lacked `jev_align`; no code failure was established. The user explicitly accepted the exact-SHA hosted CI plus these local checks and directed continuation. This exception applies only to this pinned baseline; re-run the gate for any later baseline SHA.
- Local baseline run limitations are recorded rather than described as a successful full local run. No runtime, migration, API, Jev flag or calibration-lock changes were made in Task 1.

<a id="task-2"></a>

## Task 2: Утвердить ownership, пилот и human approval

### Intent

В текущем продукте нет общего образовательного source registry, policy lifecycle или policy-specific review authority. Stage 2 supplies reusable ingestion/review/Jev seams but not these policy capabilities. До persistence/API надо одобрить минимальный bounded context, пилот и ответственность за канонизацию.

### Implementation Steps

1. Создать ADR в docs/architecture/knowledge-policy.md: два новых subject modules — knowledge и policy; без change_intelligence и review module.
2. Зафиксировать, что domain canonical facts остаются у их текущих owners, а общая Claim хранит утверждение источника только до нормализации/approve; универсальной таблицы facts нет.
3. Выбрать первую проверяемую вертикаль: одна федеральная норма с будущим admission cycle, BMSTU-specific exception и затем один срез Admission Benefits/Individual Achievement. Разрешить только версионированный allowlist и ограниченные pollers; запретить общий crawl/news feed в пилоте.
4. Утвердить publishers/hosts/feed endpoints для allowlist, trust tier, обязанность правовой проверки и actor, который может одобрить exact rule revision. University editor по умолчанию только предлагает candidate; назначенный policy steward утверждает явно и аудируемо.
5. Утвердить владельца admission-cycle mapping в `admissions`; отсутствие source-backed сопоставления означает BLOCKED_BY_MISSING_DATA.
6. Выбрать operational scheduler/runner и допустимую частоту discovery. Stage 2 `source-health` — read-only CI probe, а `deploy/yc/compose.yaml` не содержит ingestion worker; discovery должен запускаться bounded command через выбранный operations/deployment runner, без отдельного сервиса.
7. Для новых domain semantics, которые не помещаются в существующий owner contract/evaluator, утвердить владеющий модуль и отдельный contract/evaluation change. Generic policy не становится domain calculator.

### Required Interfaces and Contracts

- Ни public API, ни DB schema пока не меняются.
- Ни один source trust tier не означает legal adoption; отдельное решение по policy lifecycle понадобится для каждой candidate.

### Error Handling and Logging

- Если нет утверждённого reviewer/capability, allowlisted primary/official source set либо operational scheduler owner, пилот ограничивается read-only observations/claims без effective-rule write path.
- Не создавать fake default cycle или default source authority.

### Tests

- Ревью архитектурной таблицы dependency direction и решения с владельцами модулей.
- Команда после документации: rg -n "modules/(knowledge|policy)|modules/admission_benefits|DecisionModelPort" docs/architecture/knowledge-policy.md.

### Acceptance Criteria

- ADR называет data owners, source trust steward, review actor, первый use case и non-goals.
- ADR подтверждает запреты на микросервисы, Kafka, multi-DB, graph DB, arbitrary crawl, generic policy benefit calculator и путь из unreviewed candidate в Effective Rule Resolver.

### Verification

- Сопоставить ADR с .ai-factory/RULES.md, docs/product-principles.md, docs/architecture.md и этим планом.
- Все неутверждённые поля оформлены как человеческие блокирующие решения, а не допущения реализации.

## Риски фазы и меры снижения

- Риск: реализация начнётся из старой/грязной plan checkout. Митигация: отдельный clean worktree на проверенном Stage 2 SHA обязателен.
- Риск: поздняя интеграция Stage 2 продублирует Jev/admission contracts/migrations. Митигация: Stage 2 уже является baseline; до каждой будущей фазы проверяется только advancement remote head.
- Риск: ACTIVE legacy benefit rows будут ошибочно приняты за explicit approval. Митигация: ACTIVE сам по себе не является approval event; требуется reviewed per-revision adoption перед передачей строки policy resolver.
- Риск: health probe будет принят за scheduler ingestion. Митигация: зафиксировать operational owner и scheduled runner отдельно.
- Риск: нет legal reviewer. Митигация: не включать effective rules без утверждённого review actor.

## Проверка завершения фазы

- Task 1 pins future execution to clean Stage 2 worktree; the dirty planning checkout remains reconciliation context only.
- Task 2 closes source allowlist, reviewer, pilot, scheduler and novel-domain-owner decisions before policy writes or scheduled acquisition.
- ADR опубликован и блокирующие решения закрыты.
