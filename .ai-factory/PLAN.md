# План consolidation Andromeda в main

Ветка-источник: `feature/interactive-map-data` (`1fb8b0201541867d4ee32e7d892158fa8db298df`)
Целевая ветка: `main`
Дата: 2026-09-13

## Цель

Безопасно объединить накопленную цепочку Andromeda в `main`, не добавляя новый
product scope и не запуская Personal Route. Итогом должна стать стабильная
базовая точка для следующего этапа.

## Ограничения

- Не выполнять force-push, rebase опубликованных веток или удаление веток.
- Не мержить завершённые feature-ветки по одной.
- Не менять business logic; разрешать только реальные integration conflicts.
- Проверить миграции, SQLite/PostgreSQL, OpenAPI, frontend, fullstack и E2E.

## Tasks

- [x] Task 1: Проверить remote Git graph, merge-base, ancestry и patch-equivalence
  всех заявленных веток.
- [x] Task 2: Проверить merge preview, состав итоговой ветки и integration surfaces
  (`alembic`, modules/API, frontend/OpenAPI, CI) перед изменением `main`.
  Критерии: `git merge-tree --write-tree` без конфликтов, `git diff --check`
  чистый, одна Alembic head с линейной историей, map-agnostic campus API
  присутствует, OpenAPI/generated client и CI wiring присутствуют.
- [x] Task 3: Объединить только `origin/feature/interactive-map-data` в актуальный
  `main` через безопасный non-destructive merge.
- [x] Task 4: Выполнить strict verification итоговой `main`, включая локальные
  SQLite/PostgreSQL-capable gates и regression suites. Зафиксировать результаты
  backend pytest/mypy, compileall, чистой SQLite migration, OpenAPI drift,
  frontend unit/build, fullstack fixture и Playwright; PostgreSQL отметить как
  локально выполненный либо как проверенный disposable/remote gate с причиной
  пропуска локального запуска.
- [x] Task 5: Выполнить независимые review и security checklist по session
  cookies/profile persistence, API validation, DB/secrets, CORS/headers и
  events/campus endpoints; исправлять только подтверждённые blockers через
  отдельный fix cycle.
- [x] Task 6: Push `main`, дождаться полного remote CI green и подтвердить
  стабильный итоговый SHA. Remote Actions run `34769391787` на SHA
  `18df9ebec87e60aecd614539870ae3489e37d729` завершился `success`; jobs
  `backend`, `frontend`, `fullstack`, `postgresql-integration`,
  `proftest-integration` и `proftest-spike` зелёные.

## Merge decision

`feature/interactive-map-data` cumulative по содержимому и ancestry для всех
веток кроме remote PostgreSQL lineage. PostgreSQL storage/CI commits уже входят
в итоговое дерево как patch-equivalent `e7a432b`/`ac6ac8d`; дублирующий remote
lineage `77fb9e0`/`dce195e` отдельно не мержится.

## Verification policy

- Testing: yes
- Logging: standard (консолидация не добавляет runtime code)
- Docs: warn-only; не создавать новый product documentation scope

## Execution evidence

- Merge preview: `git merge-tree --write-tree` без конфликтов; `git diff --check`
  чистый.
- В `main` вошла целиком `origin/feature/interactive-map-data`; все локальные
  feature tips являются его предками. Remote PostgreSQL tip имеет другой commit
  identity, но его два дерева и patch-id совпадают с уже включённой локальной
  lineage, поэтому отдельно не мержился.
- Исправлены подтверждённые integration blockers: byte-stable LF для
  hash-addressed fixtures, Windows-safe OpenAPI drift checks и SQLite downgrade
  в `0002_comparison_identity`; для последнего добавлен regression test.
- Verification: backend `239 passed, 4 skipped`; `mypy` 270 files; `compileall`;
  SQLite Alembic upgrade/ingest/fullstack; PostgreSQL 16 disposable exact gate
  `8 passed` и fullstack; frontend OpenAPI drift, `10 files / 19 tests`, build;
  Playwright `28 passed`; proftest-spike `52 passed`, strict mypy 55 files,
  frontend unit/build, drift и `4 passed` browser tests.
- Security: tracked secrets absent, `npm audit` reports 0 vulnerabilities,
  session cookie is HttpOnly/SameSite/secure-configurable, inputs are strict,
  SQLAlchemy is used at the persistence boundary, API security headers/CSP are
  present. Non-blocking debt: no application rate-limit layer; `pip-audit`
  could not complete in this Windows environment because of resolver/encoding
  limitations.

## Commit strategy

Один merge commit на `main` с источником `origin/feature/interactive-map-data`;
последующие commits допустимы только для подтверждённых integration blockers.
