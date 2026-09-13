# Phase 4: Verification and handoff

Plan: [index.md](index.md)
Tasks: 4
Depends on: Phase 1 / Task 1, Phase 2 / Task 2, Phase 3 / Task 3

## Objective

Доказать, что context layer и architecture guards не меняют product behavior и проходят локальные/remote gates; подготовить безопасный feature-branch handoff для последующей интеграции.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|------|-----------------|----------------|
| `.github/workflows/` | existing backend/frontend/fullstack jobs | Remote CI is the final source of green status. |
| `backend/pyproject.toml` | pytest/mypy configuration | Backend/type commands must use project configuration. |
| `frontend/` | generated OpenAPI client/build | Run only because public contract imports are touched; expect no OpenAPI drift. |
| `.ai-factory/plans/feature-agent-guidance-guardrails/index.md` | task ledger | Only index checkboxes record progress. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| `.ai-factory/plans/feature-agent-guidance-guardrails/index.md` | modify | Mark Task 1–4 complete only after their verification gates. |
| `.ai-factory/PLAN.md` | do not modify | Existing consolidation ledger is historical and outside this task. |
| Product source | limited modify | Seam-only fixes are allowed only for a confirmed blocker and must not change endpoint/schema/database/ingestion/scoring behavior. |

## Task 4: Verification, review и CI

### Intent

Закрыть strict verify/review gates и оставить evidence для следующего агента; не запускать Personal Route или новые features.

### Implementation Steps

1. Capture `git status --porcelain` and an explicit intended-file manifest; preserve and exclude pre-existing untracked files. Run focused architecture and affected module tests, then the full backend pytest suite.
2. Run strict backend typing (`python -m mypy src/andromeda` from `backend`), compileall and import smoke checks for `andromeda.api.main` and public contracts; inspect `git diff --check`.
3. Because public contract surfaces changed, run OpenAPI drift check and frontend unit/build commands; do not regenerate unrelated clients.
4. Audit docs/code consistency: all 11 modules, events/campus spatial data boundary, public contract/port terminology, compatibility exception and current CI commands agree.
5. Run `$aif-verify --strict` equivalent gates and append the standard machine-readable verify result in the agent response. If a real blocker appears, use `$aif-fix` on only that blocker, rerun strict verify, and preserve no product behavior.
6. Run independent `$aif-review` (optionally `+check` if findings need validation). A blocker requires fix → verify → review; suggestions are recorded without scope expansion.
7. Commit exact intended files and, when remote publication is in scope, push the feature branch and wait for remote CI green. Do not merge or delete branches as an implicit part of this context-layer task; integration into `main` is a separate explicit action after the green feature SHA is reviewed.

### Required Interfaces and Contracts

- No new environment variable, dependency, endpoint, migration, generated-client schema or user-visible behavior is expected.
- Verification must explicitly report if PostgreSQL/browser checks are unavailable; strict completion requires CI evidence or a documented existing CI equivalent.
- Preserve all pre-existing untracked user files; stage only this plan/research/context/docs/source seam/test files.

### Error Handling and Logging

Verification failures are blockers with command output and affected path. No secrets, cookies, database URLs or profile payloads go into commits or reports.

### Tests

- `python -m pytest -q tests/architecture`
- `python -m pytest -q tests`
- `python -m mypy src/andromeda`
- `python -m compileall -q src/andromeda`
- `git diff --check`
- Existing frontend OpenAPI drift/unit/build commands from `frontend/package.json`.
- GitHub Actions full workflow on pushed SHA.

### Acceptance Criteria

- Strict verification has no blocking failures.
- Independent review has no Critical Issues.
- Remote CI is green for the final feature SHA.
- Feature branch contains only the intended guidance/guardrail changes; main product logic/history is not rewritten.

### Verification

- `git diff --stat main...HEAD` and `git diff --name-only main...HEAD`
- `git status --short --branch`
- `gh run list --branch feature/agent-guidance-guardrails --limit 5` / `gh run view <id> --json status,conclusion,jobs`
- Expected result: exact intended files, preserved pre-existing files, clean worktree, successful jobs and a final handoff with feature SHA/evidence.

## Phase Risks and Mitigations

- Risk: frontend/OpenAPI check reveals unrelated pre-existing drift. Mitigation: compare baseline and do not regenerate unrelated files; report as blocker only if caused by this change.
- Risk: remote CI latency. Mitigation: poll at bounded intervals and report current run status; do not alter workflow to hide failures.
- Risk: user-owned untracked files are staged accidentally. Mitigation: use explicit `git add --` paths and inspect staged name-only diff before commit.

## Phase Completion Checklist

- Task 4 acceptance criteria and all required verification/review checks pass.
- `index.md` task checkbox updated last.
