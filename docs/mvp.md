# Andromeda MVP scope / Private Alpha transition

## Stage

Private Alpha transition toward MVP Production Level. Core loop:
**Discover → Refine → Shortlist → Compare → Decide**. The production-level
label is reserved for the evidence gate in `docs/mvp-production-level.md`.

## Target user

Абитуриент, который выбирает между несколькими образовательными программами.

## Core job

Понять доступные программы, проверить ограничения поступления, сократить варианты до объяснимого shortlist, сравнить финальных кандидатов и сохранить собственное решение.

## MVP includes

- multi-university catalog: BMSTU and HSE через adapter model;
- curricula, disciplines, admissions, Admission Fit и Content Fit;
- anonymous/account persistence для `DecisionContext` и shortlist;
- explicit final choice с optimistic revision;
- source provenance, source gaps и fail-closed ingestion;
- adaptive profile как необязательный refinement-инструмент;
- comparison summary-first и raw evidence drill-down;
- product analytics, admin ingestion audit, events/campus там, где есть source-backed данные;
- Web и Telegram как consumers общих backend engines.

## Out of MVP

Career Fit, personal career guidance, ML ranking, validated personal Workload Readiness, отзывы, новости, социальные функции, guaranteed admission predictions, external public sharing и массовое покрытие университетов.

## Definition of Done

1. BMSTU и HSE coexist в PostgreSQL с university-scoped IDs.
2. Пользователь может завершить discover → shortlist → compare → final choice без профтеста.
3. Сохранённый shortlist и final choice переживают reload и account transfer с явным conflict outcome.
4. Missing source data не превращается в ноль и объясняется в UI.
5. Live ingestion публикуется только после capture, parse, validation, identity и sanity checks.
6. OpenAPI, generated frontend client, backend/frontend/fullstack/PostgreSQL/proftest/Telegram checks зелёные.
