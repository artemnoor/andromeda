<!-- aif:research-mode:ultra -->

# Исследование: постоянные инструкции и архитектурные guardrails Andromeda

Topic: permanent agent instructions and architecture guardrails
Slug: agent-guidance-guardrails
Updated: 2026-09-13
Status: complete

## Artifact Index

- [RESEARCH.md](RESEARCH.md) — фактическое состояние проекта, разрывы документации и ограничения для плана.
- [DEPENDENCY-GRAPH.md](DEPENDENCY-GRAPH.md) — зафиксированные cross-module зависимости и допустимые границы.

## Active Summary (input for /aif-plan)

### Findings

- Проект уже является modular monolith: один FastAPI backend, одна infrastructure boundary, SQLAlchemy только в `andromeda.infrastructure`, предметные модули публикуют `contracts.public` и Protocol-порты.
- На `main` фактически присутствуют модули `universities`, `programs`, `curricula`, `disciplines`, `comparison`, `proftest`, `recommendations`, `admissions`, `admission_fit`, `events` и `campus`. `docs/architecture.md` и root README не полностью отражают последние два модуля.
- Постоянные инструкции отсутствуют: нет root `AGENTS.md`, `.ai-factory/DESCRIPTION.md` и `.ai-factory/RULES.md`. Конфигурация `.ai-factory/config.yaml` уже задаёт их пути и русский язык артефактов.
- Текущий architecture test проверяет набор слоёв и запрет infrastructure/API/SQLAlchemy, но не проверяет уникальные cross-module зависимости и не включает `admissions`/`admission_fit` в expected boundary set.
- Реальные нарушения/неоднозначности для guardrail ограничены известными переходными связями: `comparison → disciplines.domain.areas`, `campus → events.contracts.results/events.domain`, `proftest → recommendations.repository.ports/recommendations.services.*`, `admissions → programs.repository.ports`. Остальные cross-module imports используют public contracts или reader ports.

### Decisions for planning

- Создать только instruction/context artifacts и укрепить архитектурные tests; продуктовые use cases, API behavior, schemas, database и ingestion не менять.
- Считать `modules/<module>/contracts/public.py` публичным contract surface.
- Считать `modules/<module>/repository/ports.py` публичным Protocol surface только для typed reader ports; concrete repository internals остаются закрытыми. Это соответствует существующему коду и позволяет избежать необоснованной массовой миграции портов.
- Убрать из runtime cross-module imports внутренних `domain` и `services`, исправив public re-export/port boundary там, где это не меняет поведение. Compatibility facades, которые только поддерживают старые import paths, зафиксировать отдельным явным allowlist и документировать как переходный adapter, не разрешая аналогичные исключения для бизнес-логики.
- Не создавать `.ai-factory/ARCHITECTURE.md` и roadmap без необходимости: пользовательский scope требует root instructions, DESCRIPTION, RULES и обновления `docs/architecture.md`; existing human architecture document остаётся источником фактической схемы.

### Non-goals

- Не добавлять Personal Route, новые события/кампус-функции, карту, маршрутизацию или новые deployment units.
- Не делать microservices/Kafka/CQRS/rewrite architecture.
- Не переписывать main history и не менять runtime business behavior.

## Sessions

### 2026-09-13 — ultra exploration

- Read-only warmup: git state, CI evidence, AI Factory config, README, docs, module tree, API/composition/infrastructure and architecture tests.
- Parallel explorers inspected persistent documentation gaps, module imports and application composition. No files or repository state were changed by explorers.
- Evidence was cross-checked against current source paths and tests before planning.
