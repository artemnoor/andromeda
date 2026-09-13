# Cross-module dependency graph

Граф отражает imports в `backend/src/andromeda/modules/**/*.py`, а не направление HTTP или database calls.

```text
admission_fit ──public contracts──> admissions
admission_fit ──public contracts──> programs
admissions ──reader port──> programs
campus ──public contracts──> universities
campus ──public contracts──> programs
campus ──event public surface──> events
comparison ──public contracts──> curricula
comparison ──reader ports──> curricula, disciplines, programs
comparison ──public area surface──> disciplines
proftest ──public contracts──> curricula, disciplines, programs
proftest ──recommendation public port──> recommendations
recommendations ──public contracts──> proftest, disciplines
```

`infrastructure`, `api` и `composition` остаются composition/deployment boundaries и не входят в запрет subject-module imports. Они вправе собирать concrete implementations.

## Guardrail policy

- Публичный контракт: `modules/<module>/contracts/public.py` и явно экспортируемые из него типы.
- Публичный Protocol port: `modules/<module>/repository/ports.py`; это единственный разрешённый cross-module путь внутрь `repository`.
- Запрещены cross-module пути `domain.*`, `services.*`, `repository.*` кроме `repository.ports`.
- Три текущих proftest compatibility-фасада являются не бизнес-взаимодействием, а обратной совместимостью import paths; они допускаются только в точном allowlist теста и должны быть перечислены в `RULES.md`/architecture docs. Любой новый такой alias требует явного изменения allowlist и документации.
- Все cross-module imports должны быть абсолютными и направлены на canonical public surface; relative imports внутри собственного модуля не анализируются как cross-module.
