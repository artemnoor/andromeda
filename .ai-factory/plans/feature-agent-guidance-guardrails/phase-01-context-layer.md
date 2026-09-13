# Phase 1: Context layer

Plan: [index.md](index.md)
Tasks: 1
Depends on: none

## Objective

Создать постоянные root/project instructions, которые новый AI-агент сможет прочитать до работы и применить без знания истории предыдущих сессий.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|------|-----------------|----------------|
| `README.md` | project overview and current flows | Источник пользовательского описания BMSTU scope и команд запуска. |
| `docs/architecture.md` | modular monolith, boundaries, storage | Источник архитектурной терминологии и существующих решений. |
| `backend/src/andromeda/modules/` | 11 subject modules | Точный список актуальных функциональных модулей для DESCRIPTION/RULES. |
| `.ai-factory/config.yaml` | `paths.*`, `language.*`, `git.*` | Канонические пути артефактов и язык: русский текст, технические токены без перевода. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| `AGENTS.md` | create | Mandatory context → analysis → plan → implementation → tests → verification workflow, scope and git safety guardrails, evidence-first handoff. |
| `.ai-factory/DESCRIPTION.md` | create | Andromeda identity, BMSTU source-backed scope, multi-university direction, product flows, stack and current modules. |
| `.ai-factory/RULES.md` | create | Actionable architecture/data/API/migration rules from the request, plus explicit compatibility-facade policy. |

## Task 1: Постоянные инструкции и DESCRIPTION

### Intent

Закрепить правила, которые сейчас существуют только в коде, `README` и `docs/architecture.md`, не объявляя исторические планы активными.

### Implementation Steps

1. Создать `AGENTS.md` в repository root. Указать, что агент обязан сначала прочитать этот файл, resolved AI Factory context, `README.md`, relevant docs and tests; сформулировать шесть последовательных фаз workflow.
2. В `AGENTS.md` описать scope guard: не добавлять Personal Route/новые features без запроса, не переписывать main history, не делать force-push/rebase/destructive git operations; перед изменением фиксировать affected files and contracts.
3. Создать `.ai-factory/DESCRIPTION.md` на русском языке с техническими именами без перевода: Andromeda modular monolith, BMSTU canonical/source-backed data, multi-university adapter direction, flows comparison/proftest/recommendations/admissions/admission_fit/events/campus, API/OpenAPI/frontend and storage.
4. Создать `.ai-factory/RULES.md` как короткий hard-rule список. Отдельно описать разрешённые public surfaces `contracts.public` и `repository.ports`, boundary исключения compatibility facades и правило “composition/API/infrastructure могут wiring concrete implementations, subject modules — нет”.

### Required Interfaces and Contracts

- Документы не создают runtime API, environment variables или database schema.
- `AGENTS.md` должен использовать точные команды/термины `git diff`, `pytest`, `mypy`, `OpenAPI`, `generated clients`, без обещания автоматически менять main.
- `DESCRIPTION.md` и `RULES.md` должны ссылаться на фактические пути `backend/src/andromeda/modules`, `backend/src/andromeda/api`, `backend/src/andromeda/infrastructure`, `backend/src/andromeda/ingestion/universities/<university>`.

### Error Handling and Logging

Это docs-only task: runtime error handling и logging не меняются. Документы требуют не логировать secrets, cookies, токены и профили целиком при диагностике.

### Tests

Проверить наличие файлов, UTF-8, обязательных terms/sections и отсутствие product scope в `backend/tests/architecture/test_agent_guidance_artifacts.py`. Основной автоматический тест для import policy появится в Task 3.

### Acceptance Criteria

- `AGENTS.md`, `.ai-factory/DESCRIPTION.md`, `.ai-factory/RULES.md` существуют.
- Будущий агент получает однозначный порядок работы и запреты scope/git/architecture.
- Правила не противоречат текущим events/campus/recommendations/admission_fit flows.

### Verification

- `Get-Content AGENTS.md, .ai-factory/DESCRIPTION.md, .ai-factory/RULES.md`
- Expected result: файлы читаются как UTF-8, используют русский prose и стабильные technical tokens.

## Phase Risks and Mitigations

- Risk: документация станет слишком общей и непроверяемой. Mitigation: фиксировать реальные paths, commands, public surfaces и current module names.
- Risk: RULES запретит уже существующий composition wiring. Mitigation: явно ограничить запрет subject modules и разрешить composition/API/infrastructure boundary.

## Phase Completion Checklist

- Task 1 acceptance criteria выполнены.
- Required documentation checks pass.
- `index.md` task checkbox обновлён после проверки.
