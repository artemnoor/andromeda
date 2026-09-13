# Phase 3: Architecture guards

Plan: [index.md](index.md)
Tasks: 3
Depends on: Phase 2 / Task 2

## Objective

Превратить описанные архитектурные правила в deterministic test gate, который обнаруживает новый boundary bypass и не вмешивается в API/composition/infrastructure adapters.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|------|-----------------|----------------|
| `backend/tests/architecture/test_module_boundaries.py` | current two tests | Existing baseline is too permissive (`expected <= actual`) and lacks import policy. |
| `backend/src/andromeda/modules/` | subject module registry | Exact current registry has 11 modules and four layers each. |
| `backend/src/andromeda/modules/proftest/services/{ranking,matching,explanations}.py` | compatibility facades | Exact transitional exception must be explicit, not a general service import allowance. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| `backend/tests/architecture/test_module_boundaries.py` | modify | Exact module/layer registry, outer-boundary guard, cross-module public import analyzer, compatibility allowlist and policy unit tests. |
| `.ai-factory/RULES.md` | modify if needed | Keep test-enforced naming of surfaces exactly synchronized; no unrelated rule expansion. |
| `docs/architecture.md` | modify if needed | Keep guardrail wording aligned with executable test policy. |

## Task 3: Усиленные architecture tests

### Intent

Закрыть именно критический architectural drift: subject module A не может начать зависеть от internal implementation module B незаметно для CI.

### Implementation Steps

1. Define `SUBJECT_MODULES` with all 11 current modules: `universities`, `programs`, `curricula`, `disciplines`, `comparison`, `proftest`, `recommendations`, `admissions`, `admission_fit`, `events`, `campus`.
2. Assert the actual module directory names equal this registry and each module contains all `domain`, `contracts`, `services`, `repository` directories. This makes a new/removed module a deliberate test update.
3. Keep the existing outer-boundary forbidden imports for every Python file under `modules/**/*.py`: `andromeda.infrastructure`, `andromeda.api`, `andromeda.composition`, `andromeda.ingestion`, `sqlalchemy`, `bmstu_parser`, `proftest_spike`. Use normalized AST import names and report path/import in failures.
4. Resolve both absolute and relative imports in each subject module. For a cross-module import, allow only exact canonical paths `...contracts.public` or `...repository.ports`. Reject all other target paths, including cross-module `domain.*`, `services.*`, concrete `repository.*`, module private files and broad package imports.
5. Declare exact `COMPATIBILITY_FACADE_IMPORTS` mapping each of the three existing proftest facade file paths to source module plus imported symbols. Assert their imports are only the expected re-export aliases; they are excluded from runtime interaction violations but cannot expand implicitly.
6. Add helper-level tests for allowed public contract/port paths, rejected internal/relative paths, outer-boundary paths and exact facade module/symbol mapping. Keep all checks local, AST-based and independent of network/database.

### Required Interfaces and Contracts

- Test reports normalized module path such as `modules/comparison/services/aggregation.py -> andromeda.modules.disciplines.domain.areas`.
- `repository.ports` is the only allowed repository path; `repository.models`, concrete repositories and `domain/services` are forbidden cross-module.
- Relative imports are resolved and remain valid only when they stay inside one subject module; a relative import that escapes to another module is subject to the same public-surface rule.
- `api`, `composition`, `infrastructure`, `ingestion` are outside the subject-module scan, but subject modules are forbidden from importing those outer boundaries.

### Error Handling and Logging

Test failures include actionable path/import data; no runtime logging or secret data is involved.

### Tests

- `python -m pytest -q tests/architecture`
- Add cases for exact 11 modules, all four layers, no outer-boundary imports, zero current cross-module violations and exact compatibility allowlist.
- Expected result: architecture tests pass on current tree and would fail on a newly introduced internal cross-module import.

### Acceptance Criteria

- All current modules are covered, including `admissions` and `admission_fit`.
- An internal cross-module import fails the test unless it is the exact documented compatibility façade alias.
- Existing composition/API/infrastructure imports remain outside the guard scope.
- No product code path or runtime behavior changes are introduced by the test itself.

### Verification

- `python -m pytest -q tests/architecture`
- `python -m pytest -q tests`
- Expected result: architecture and full backend test suite pass.

## Phase Risks and Mitigations

- Risk: guard becomes brittle due to formatting. Mitigation: inspect AST nodes, normalize import names and compare exact strings, not source text.
- Risk: compatibility allowlist becomes an escape hatch. Mitigation: fixed file-to-import mapping and a test asserting no other exception exists; document every entry.
- Risk: module registry blocks an intentional future module unexpectedly. Mitigation: failure message explicitly asks to update registry and architecture docs in the same change.

## Phase Completion Checklist

- Task 3 acceptance criteria and architecture/full backend tests pass.
- `index.md` task checkbox updated after verification.
