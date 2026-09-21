# Phase 00 — Stage 1 baseline stabilization

Plan: [index.md](index.md)
Tasks: T00
Depends on: current repository audit only

## Objective

Отделить завершённую semantic/catalog analytics migration от текущих dirty changes и создать единственную чистую точку, от которой запускается Stage 2. Ни одна последующая задача Stage 2 не выполняется на текущем dirty worktree.

## Task T00 — Зафиксировать чистый Stage 1 baseline и подготовить branch для Stage 2

### Intent

Текущий аудит выполнен на ветке feature/university-admin-control с pre-existing dirty changes. Это исследовательское состояние, а не допустимая execution base. Сначала нужно доказуемо отделить изменения первой миграции от unrelated work и сохранить её отдельным commit/branch.

### Implementation steps

1. На текущем worktree выполнить read-only inventory: git status --short, git diff --stat, git diff --name-only, git ls-files --others --exclude-standard. Не использовать git reset, git checkout -- или массовое удаление.
2. Сопоставить изменённые файлы с уже завершённой Stage 1 migration: semantic layer, ProgramProjection/ProgramMetric, MetricRegistry, QuerySpec, AnalyticsResult, QueryFrame/QuerySession, deterministic policies, ResponsePlan/ResponseEnvelope, APIs, tests и docs.
3. Все unrelated user changes оставить нетронутыми и вынести из execution path через отдельный worktree или временную сохранённую ветку только после явного контроля содержимого.
4. В чистом worktree от последнего approved parent commit создать baseline branch с понятным именем, например feature/semantic-catalog-analytics-baseline.
5. На baseline branch добавить только предыдущую migration, одним обычным commit с сообщением уровня feat: complete semantic catalog analytics migration. Перед commit проверить git diff --cached --name-only и не добавлять unrelated files.
6. Выполнить полный Stage 1 verification: backend tests, architecture checks, mypy, migrations, frontend checks, Telegram checks, PostgreSQL integration, analytics benchmarks.
7. Только после зелёной проверки создать feature/jev-ecosystem-stage-2 от нового clean baseline commit. Зафиксировать baseline SHA в index.md и в execution log.
8. Если dirty files нельзя безопасно классифицировать, остановить Stage 2 на этом gate и запросить ручное решение; не угадывать принадлежность изменений.

### Required interfaces and invariants

- Stage 2 branch contains the approved Stage 1 commit plus no unrelated work.
- Current feature/university-admin-control remains preserved; it is not rewritten or force-pushed.
- Baseline SHA, parent SHA, staged file list and verification report are recorded.
- All later phase dependencies refer to the new clean Stage 2 branch, not the audit worktree.

### Error handling and logging

Log only repository paths, commit SHAs, test commands and classification decisions. Do not include secrets or database URLs. A classification conflict is a blocking error, not an automatic merge.

### Tests

- git diff --check;
- existing full CI-equivalent Stage 1 test matrix;
- migration head/history check;
- analytics benchmark smoke;
- clean checkout/import smoke from the new baseline commit.

### Acceptance criteria

- clean baseline commit exists and contains only the reviewed previous migration;
- Stage 2 branch is created from that commit;
- full Stage 1 verification is green;
- unrelated dirty changes remain preserved outside the Stage 2 execution worktree;
- no Stage 2 task is started before this acceptance criteria set is met.

### Verification

- git status --short is empty in the Stage 2 worktree;
- git log --oneline --decorate -3 shows baseline commit and Stage 2 branch;
- git diff baseline_sha..HEAD is empty immediately after branch creation;
- all Stage 1 verification commands pass.

### Rollback and risk

Rollback means stopping before branch creation or deleting only the newly created local branch after confirming it has no unique work. Never reset the original dirty branch. Main risk is accidentally mixing Stage 1 and Stage 2; the clean-worktree gate prevents it.

