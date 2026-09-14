<!-- aif:plan-mode:ultra -->

# План: full BMSTU catalog ingestion

## Original Request

Превратить текущий BMSTU tracer ingestion из 2 программ в автоматический ingestion всего доступного официального каталога МГТУ им. Баумана, загрузить результат в существующую canonical DB, убрать live-зависимость от старых `TARGET_DIRECTION_CODE`/`TARGET_PROGRAM_CODES`, сохранить contracts/modular boundaries, обойти pagination/details/study plans/admissions, фиксировать provenance/source hashes/source gaps, детерминированно классифицировать все дисциплины по существующей 22-area taxonomy, проверить SQLite/PostgreSQL/migrations/idempotence/full pytest+mypy/CI и передать отдельную feature branch без merge.

## Research Context

- Research bundle: [bmstu-full-catalog-ingestion](../../research/bmstu-full-catalog-ingestion/INDEX.md).
- Official API crawl baseline: 53 catalog cards, 53 details, 152 profiles, 133 unique plan URLs.
- Official linked plan metadata includes direct Yandex files, Yandex directories and `clck` short links; unavailable resources are source gaps.
- Existing fixture/demo keeps two profiles and fixture event/campus contracts; full live path must discover profiles without a hardcoded list.

## Scope

- In scope: BMSTU source capture/parser/normalizer, ingestion contracts, repository multi-direction projection, taxonomy mappings/rules, runner/retry, migrations if required, focused/full tests and ingestion documentation.
- Out of scope: API/recommendation/comparison/proftest redesign, new event/campus live fixture truth, unrelated frontend work in the dirty worktree.

## Defaults

- Testing: yes; logs: verbose and configurable through `LOG_LEVEL`; documentation: update; branch: current `feature/full-bmstu-ingestion`.
- The singular aggregate fields remain compatibility aliases; plural directions/gaps are canonical for full snapshots.
- Existing valid numeric program codes retain their IDs. Other source profiles receive deterministic numeric suffixes with the raw source code retained in raw provenance.

## Acceptance Criteria

- [x] Live capture discovers all pages until `meta.count`, all returned details and all linked plans without a manual program list.
- [x] Every discovered profile has a unique canonical program ID and either a non-empty curriculum or an explicit source gap.
- [x] Raw snapshots include requested/final URLs, hashes and source metadata; canonical IDs are unique and repository writes are atomic/repeatable.
- [x] All projected disciplines have valid 22-area `area_weights` with positive values and exact sum `1.0000`; no unexplained mass fallback remains after the vocabulary audit.
- [x] Fixture API/recommendation/comparison/proftest behavior remains green; live events/campus are not fabricated.
- [x] Full pytest, mypy, SQLite migration/ingestion/idempotence and available PostgreSQL checks are run; diff check, strict verify and review are green or blockers are documented.

## Tasks

- [x] [Phase 1: source discovery and contracts](phase-1-source-discovery.md)
- [x] [Phase 2: identity and raw/canonical aggregates](phase-2-identity-contracts.md)
- [x] [Phase 3: full catalog parser and study-plan resolver](phase-3-parser-plans.md)
- [x] [Phase 4: admissions and live-source safety](phase-4-admissions-safety.md)
- [x] [Phase 5: taxonomy coverage](phase-5-taxonomy.md)
- [x] [Phase 6: repository and runners](phase-6-persistence-runners.md)
- [x] [Phase 7: tests and documentation](phase-7-tests-docs.md)
- [ ] [Phase 8: verification, commit and CI](phase-8-verification.md)

## Plan Integrity

- Each task is assigned to exactly one phase file.
- Phase order is dependency order; each phase names files, symbols, tests and executable acceptance commands.
- No unresolved architectural choice remains; source gaps and identity rules follow ADR-0001.

## Improve +check result

The plan was manually re-checked because the repository does not expose the `aif-*` executable. Phase links, scope boundaries, acceptance criteria and the research/ADR references resolve; the plan introduces no hardcoded program list and keeps API, comparison, recommendations, proftest and event/campus production truth out of scope. The only explicit two-program values remain committed fixture/demo compatibility inputs.

## Implementation evidence

- Official live run: 53 catalog cards, 53 details, 152 profiles, 133 unique public plan URLs, 134 curricula, 14,910 canonical items, 1,492 admission offerings, 18 source gaps, 319 captured snapshots, 0 live events and 0 live campus points.
- SQLite repeat run: canonical IDs unique, 0 invalid area-weight sums, second repeat had 0 inserts and 0 removals; migrations at `0009_auth_profile_binding`.
- Quality: full backend `296 passed, 6 skipped, 3 warnings`; `python -m mypy` passes for 313 source files; focused ingestion/contracts `43 passed`; PostgreSQL-only local smoke is explicitly skipped because no DSN is configured.
