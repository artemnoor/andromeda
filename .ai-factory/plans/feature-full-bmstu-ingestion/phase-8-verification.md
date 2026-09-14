# Phase 8: verification, commit and CI

## Goal

Run the requested gates, fix only blocking findings, and hand off a clean feature branch without merge.

## Commands

1. `python -m pytest backend/tests -q`.
2. `mypy backend/src backend/scripts` (or the configured pyproject command).
3. `alembic upgrade head` against fresh SQLite and configured PostgreSQL; run repeat-ingestion checks.
4. `git diff --check` and `git status --short` with explicit review of pre-existing dirty paths.
5. Strict architecture/rules verification and code review of only the BMSTU/full-ingestion diff.
6. If a blocking test/review finding occurs, apply a narrow fix, rerun strict verification/review and repeat until green or a genuine external blocker remains.
7. Stage only changed BMSTU/contract/repository/migration/test/doc/plan/research paths, verify `git diff --cached --name-only`, commit on `feature/full-bmstu-ingestion`, push, then inspect GitHub Actions status if remote/credentials permit.

## Acceptance

Final handoff lists counts from the actual full ingestion run, source gaps, taxonomy coverage, removed tracer hardcodes, exact test/CI results and merge readiness. No merge is performed.

## Local verification evidence

- [x] Full backend pytest: `296 passed, 6 skipped, 3 warnings`; `python -m mypy`: no issues in 313 source files; `python -m compileall -q src scripts`: passed.
- [x] Final live SQLite run `ingest:78c2b34552824712af75ba8198b9bea7`: 54 directions, 152 programs, 134 study plans, 14,910 curriculum items, 1,492 admissions, 18 source gaps, 319 captured snapshots, 0 events and 0 campus points.
- [x] Repeat/idempotence and DB invariants: unique canonical IDs, valid discipline weights, no orphan curriculum rows, latest run `0 inserts / 0 removals / 17,699 unchanged`; Alembic at `0009_auth_profile_binding (head)`.
- [x] PostgreSQL integration tests: `4 skipped` because no local DSN is configured; the CI workflow provisions PostgreSQL.
- [x] Staged review: `git diff --cached --check` passed, staged paths are limited to the BMSTU ingestion/contracts/repository/tests/docs/AIF scope, and live target hardcode scan is clean. The requested `aif-*` executables are unavailable in this environment; their rules/verify/review gates were run manually and documented.
- [x] Push and GitHub Actions status check: run `34872246737` is green for all jobs; no merge was performed.
