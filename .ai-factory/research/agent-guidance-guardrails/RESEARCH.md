# Фактическое состояние и ограничения

## Репозиторий и CI

- Текущая ветка: `main`.
- `HEAD` и `origin/main`: `b4d42e4244f5880a618c810290da24b33e98729b`.
- Последний известный GitHub Actions run `34769710750` на этом SHA завершён успешно; зелёные jobs: `backend`, `frontend`, `fullstack`, `postgresql-integration`, `proftest-integration`, `proftest-spike`.
- Рабочее дерево содержит только pre-existing untracked AI Factory/Codex и пользовательские файлы; их нельзя удалять или массово включать в изменения.

## Стек и фактический поток

Andromeda — Python 3.11+, FastAPI, Pydantic, SQLAlchemy/Alembic и TypeScript frontend. Данные идут от `ingestion/universities/bmstu` через canonical contracts в subject modules, затем через infrastructure repositories в PostgreSQL/SQLite и FastAPI/OpenAPI. Composition root wires concrete services and repositories; API routes не должны знать ORM.

Subject modules на `main`:

`universities`, `programs`, `curricula`, `disciplines`, `comparison`, `proftest`, `recommendations`, `admissions`, `admission_fit`, `events`, `campus`.

У каждого есть `domain`, `contracts`, `services`, `repository` (у `comparison` repository минимален). `backend/tests/architecture/test_module_boundaries.py` сейчас не включает `admissions` и `admission_fit` в expected set.

## Контекстные артефакты

`.ai-factory/config.yaml` уже задаёт:

- `paths.description = .ai-factory/DESCRIPTION.md`;
- `paths.architecture = .ai-factory/ARCHITECTURE.md`;
- `paths.rules_file = .ai-factory/RULES.md`;
- `paths.docs = docs/`;
- `paths.plan = .ai-factory/PLAN.md`, `paths.plans = .ai-factory/plans/`;
- `language.ui/artifacts = ru`, `language.technical_terms = keep`;
- `git.base_branch = main`, `git.create_branches = true`.

При этом `AGENTS.md`, `DESCRIPTION.md`, `RULES.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `RESEARCH.md` и `.ai-factory/rules/base.md` отсутствуют на диске. Существующий `.ai-factory/PLAN.md` — завершённый исторический consolidation ledger, а старые plan-файлы не являются активными инструкциями.

## Документация и дрейф

`docs/architecture.md` правильно описывает modular monolith, storage boundary, public contracts и основные content/admission flows, но его дерево модулей и текст не отражают `events` и `campus`. Root README также перечисляет не все фактически реализованные модули. Этот scope требует обновить architecture doc; обновление API reference не требуется, поскольку задача не меняет HTTP contracts.

## Current architecture test

Текущий test делает две проверки:

1. наличие subject module layers;
2. отсутствие в `modules/**/*.py` imports `andromeda.infrastructure`, `andromeda.api`, `sqlalchemy`, `bmstu_parser`, `proftest_spike`.

Не проверяются:

- все текущие subject modules;
- импорт module A внутренних `domain`, `services` и concrete `repository` module B;
- наличие явного списка разрешённых cross-module public surfaces;
- отдельное правило для legacy compatibility facades.

## Boundary evidence

Разрешаемые существующие связи:

- `comparison`, `proftest`, `recommendations`, `admission_fit`, `campus` используют public contracts других модулей;
- `comparison`, `proftest`, `admissions` используют typed reader ports из `repository.ports`, которые являются Protocol-only boundary;
- composition/API/infrastructure могут импортировать concrete services, repositories и ORM, поскольку находятся вне subject module boundary.

Связи, которые guardrail должен закрыть или явно оформить:

- `comparison.services.aggregation` импортирует `disciplines.domain.areas.area_position`;
- `campus.contracts.results` импортирует `events.contracts.results.EventListResult` и `events.domain.entities.Event`;
- `proftest.services.proftest` импортирует recommendation reader port и concrete recommendation service/ranking;
- `proftest.services.{ranking,matching,explanations}` — legacy compatibility re-exports concrete recommendation services;
- `admissions.services.admissions` импортирует `programs.repository.ports.ProgramReader`.

Рекомендуемая минимальная реализация: перенести cross-module runtime boundary на public contract/port imports; сохранить только явно перечисленные compatibility facades как backward-compatible import aliases с тестом на закрытый allowlist. Такой allowlist не должен разрешать обычным module services/domain/contracts добавлять новые service/domain imports.

## Acceptance constraints

- Docs и tests должны быть deterministic и runnable без внешнего сервиса.
- Architecture checks должны падать при новом запрещённом import path, но не ломать текущий application wiring в `api`, `composition`, `infrastructure`, `ingestion`.
- Changes must be documentation/tests/context only, кроме минимальных public re-export/port boundary edits needed to make the guard truthful; no endpoint, schema, database, ingestion or scoring behavior changes.
