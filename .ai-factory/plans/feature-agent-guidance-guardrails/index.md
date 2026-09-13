<!-- aif:plan-mode:ultra -->
# Ultra Implementation Plan: постоянные инструкции и архитектурные guardrails Andromeda

Mode: ultra
Branch: feature/agent-guidance-guardrails
Created: 2026-09-13

## Original Request

Цель: создать в Andromeda постоянную систему инструкций и архитектурных guardrails для AI-агентов, чтобы все следующие задачи выполнялись последовательно, безопасно и в рамках текущей архитектуры.

Работай автономно до полного достижения цели. Используй AI Factory skills последовательно. Результат каждого шага используй как вход для следующего.

Используй `aif-warmup`, `aif-explore ultra`, `aif-plan ultra`, `aif-improve +check`, `aif-implement`, `aif-verify --strict` и `aif-review`. Изучи актуальный `main`, AI Factory config, README, `.ai-factory/`, `docs/architecture.md`, architecture tests, module structure, composition/API/infrastructure и текущие modules; ничего не меняй в warmup. Исследуй постоянные инструкции, DESCRIPTION/RULES, актуальность architecture docs, module boundaries, cross-module imports, consistency code vs docs и неявные архитектурные решения. Не создавай новый product scope.

Создай root `AGENTS.md` с обязательным workflow `context → analysis → plan → implementation → tests → verification`, запретом менять scope без запроса, destructive git operations и необоснованного переписывания архитектуры, правилом сначала использовать существующие contracts/modules и обязательными checks после изменений.

Создай `.ai-factory/DESCRIPTION.md` с описанием Andromeda, текущего BMSTU scope, multi-university direction, product flows и функциональных модулей. Создай `.ai-factory/RULES.md`: modular monolith; `domain/contracts/services/repository`; public contracts/ports между модулями; ORM/SQLAlchemy только в infrastructure; university-specific logic только в `ingestion/universities/<university>`; новый вуз = новый adapter; Content Fit, Admission Fit, Career Fit и Workload Readiness не смешивать; canonical IDs и UserProfile — typed contracts; business logic не в API; migrations линейные и безопасные; OpenAPI/generated clients синхронны; microservices/Kafka/CQRS только по отдельному решению.

Обнови `docs/architecture.md` под фактический код, включая `events` и `campus/spatial data`. Усиль architecture tests: включи все актуальные modules; запрети module A импортировать internal `domain/services/repository` module B; разрешай cross-module interaction только через approved public contracts/ports; сохрани запрет infrastructure/API/SQLAlchemy внутри subject modules. Не меняй product behavior.

Проведи strict verification с architecture/backend/mypy/frontend/build/docs/code consistency/CI checks. При реальном blocker используй `aif-fix`, затем повтори verify. На финальном review проверь понятность правил, актуальность docs, отсутствие противоречий и лишнего refactoring/product scope. Условия: `AGENTS.md`, DESCRIPTION, RULES созданы; docs актуальны; guards усилены; business logic не изменена; CI green. Не начинай Personal Route или другие product features.

## Settings

- Testing: yes
- Logging: standard (runtime logging не меняется; для guardrails достаточно существующих диагностических сообщений)
- Docs: yes

## Roadmap Linkage (optional)

Milestone: none
Rationale: в репозитории нет roadmap; задача создаёт постоянный context layer и не добавляет product milestone.

## Research Context

Source: `.ai-factory/research/agent-guidance-guardrails/RESEARCH.md` (Active Summary, Updated: 2026-09-13)

Исследование подтвердило 11 subject modules, отсутствие `AGENTS.md`, `DESCRIPTION.md`, `RULES.md`, неполное дерево в `docs/architecture.md`, недостаточно строгий текущий architecture test и пять конкретных legacy/internal import seams. Полный dependency graph находится в `DEPENDENCY-GRAPH.md` рядом с исследованием.

## Architecture and Decisions

- Сохраняется modular monolith и текущая композиция; новые сервисы, брокеры, карты, Personal Route и deployment units не создаются.
- `modules/<module>/contracts/public.py` — public contract surface.
- `modules/<module>/repository/ports.py` — public typed Protocol surface для reader ports; concrete repository/model implementations остаются в infrastructure.
- Cross-module imports во subject modules разрешены только на `contracts.public` и `repository.ports`; три существующих proftest compatibility facades остаются только как точные documented allowlist exceptions для обратной совместимости import paths.
- Cross-module runtime boundary `proftest → recommendations` переводится на public Protocol contract с обязательной передачей recommendation service из composition root; product API flow не меняется.
- Для устранения текущих bypasses: `area_position` и `EventListResult` экспортируются через public contract surfaces, а потребители переходят на них.
- Architecture tests проверяют exact module registry, все четыре слоя, запреты outer-boundary imports и cross-module import policy.

## Phase Index

1. [Phase 1: Context layer](phase-01-context-layer.md) — Task 1
2. [Phase 2: Public seams and docs](phase-02-public-seams-and-docs.md) — Task 2
3. [Phase 3: Architecture guards](phase-03-architecture-guards.md) — Task 3
4. [Phase 4: Verification and handoff](phase-04-verification-and-handoff.md) — Task 4

## Cross-Phase Dependencies

- Task 2 depends on Task 1 for the authoritative vocabulary and current module list.
- Task 3 depends on Task 2 because its allowlist must match the documented public seams and compatibility policy.
- Task 4 depends on Tasks 1–3 and is the completion gate; it does not add scope.

## Tasks

### Phase 1: Context layer

- [x] Task 1: Создать постоянные инструкции и DESCRIPTION ([details](phase-01-context-layer.md#task-1-постоянные-инструкции-и-description))

### Phase 2: Public seams and docs

- [x] Task 2: Оформить public seams и актуализировать архитектурную документацию ([details](phase-02-public-seams-and-docs.md#task-2-public-seams-и-актуальная-архитектура)) (depends on 1)

### Phase 3: Architecture guards

- [x] Task 3: Усилить deterministic architecture tests ([details](phase-03-architecture-guards.md#task-3-усиленные-architecture-tests)) (depends on 2)

### Phase 4: Verification and handoff

- [ ] Task 4: Выполнить strict verification, review и CI handoff ([details](phase-04-verification-and-handoff.md#task-4-verification-review-и-ci)) (depends on 1, 2, 3)

## Commit Plan

- **Commit 1** (after Tasks 1–2): `docs: add Andromeda agent guidance and public seams`
- **Commit 2** (after Task 3): `test: enforce Andromeda module boundaries`
- **Commit 3** (after Task 4, if required): `chore: record verified agent guardrails`

## Definition of Done

- Root `AGENTS.md`, `.ai-factory/DESCRIPTION.md` и `.ai-factory/RULES.md` созданы и объясняют исполнимый workflow.
- `docs/architecture.md` отражает все текущие modules, включая `events` и `campus` spatial data.
- Subject modules не импортируют внутренние `domain/services/repository` другого subject module; разрешённые public contracts/ports проверяются тестом.
- Existing compatibility facades перечислены явно и не превращаются в общий обход guardrail.
- Архитектурные, backend и type/build checks green; продуктовые endpoint/schema/database/ingestion/scoring flows не изменены.
