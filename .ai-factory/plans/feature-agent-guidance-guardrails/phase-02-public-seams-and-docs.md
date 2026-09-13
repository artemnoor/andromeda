# Phase 2: Public seams and docs

Plan: [index.md](index.md)
Tasks: 2
Depends on: Phase 1 / Task 1

## Objective

Сделать public contract seams честными для текущих cross-module imports и обновить human architecture doc до фактического module/storage/API состава без изменения product behavior.

## Current-Code Evidence

| Path | Symbols / lines | Why it matters |
|------|-----------------|----------------|
| `backend/src/andromeda/modules/disciplines/contracts/public.py` | `__all__` | `comparison` должен получать `area_position` через public surface. |
| `backend/src/andromeda/modules/comparison/services/aggregation.py` | `area_position` import | Текущий internal-domain bypass. |
| `backend/src/andromeda/modules/events/contracts/public.py` | event exports | `campus` уже использует Event types; list envelope нужно публиковать явно. |
| `backend/src/andromeda/modules/campus/contracts/results.py` | `CampusPointEventsResult` | Текущие imports `events.contracts.results` и `events.domain.entities` нарушают module seam. |
| `backend/src/andromeda/modules/recommendations/contracts/public.py` | public contracts | Владелец public reader/service Protocol для runtime `proftest → recommendations`. |
| `backend/src/andromeda/modules/proftest/services/proftest.py` | `ProftestService.__init__` | Убрать concrete recommendation import; dependency приходит из composition. |
| `docs/architecture.md` | module tree and flows | Добавить `events` и `campus/spatial data`, описать public boundary и compatibility policy. |

## Files to Change

| Path | Action | Required change |
|------|--------|-----------------|
| `backend/src/andromeda/modules/disciplines/contracts/public.py` | modify | Re-export `area_position` in the public contract. |
| `backend/src/andromeda/modules/comparison/services/aggregation.py` | modify | Import `area_position` only from `disciplines.contracts.public`. |
| `backend/src/andromeda/modules/events/contracts/public.py` | modify | Re-export `EventListResult` from the events public surface. |
| `backend/src/andromeda/modules/campus/contracts/results.py` | modify | Import `Event` and `EventListResult` from `events.contracts.public`. |
| `backend/src/andromeda/modules/recommendations/contracts/public.py` | modify | Add public `ProgramFingerprintReader`/`RecommendationCatalogReader` Protocol and `RecommendationServicePort`; re-export `RankedFingerprint`. |
| `backend/src/andromeda/modules/recommendations/repository/ports.py` | modify | Re-export the canonical public reader Protocol aliases; preserve old import compatibility. |
| `backend/src/andromeda/modules/proftest/services/proftest.py` | modify | Depend only on `recommendations.contracts.public`; accept required `RecommendationServicePort`, preserve all result logic and composition wiring. |
| `docs/architecture.md` | modify | Reflect all modules, event/campus flow, spatial data payload boundary, current public contracts/ports and explicitly scoped facades. |

## Task 2: Public seams и актуальная архитектура

### Intent

Устранить конкретные module-internal imports, которые новый guard test должен отклонять, и при этом не переносить ownership бизнес-логики между модулями.

### Implementation Steps

1. Add `area_position` to `disciplines.contracts.public.__all__`; change only `comparison.services.aggregation` import path.
2. Add `EventListResult` to `events.contracts.public` exports; change `campus.contracts.results` to import both event symbols from that public file.
3. In `recommendations.contracts.public`, define storage-independent Protocols:
   - `ProgramFingerprintReader.list_fingerprints() -> tuple[ProgramFingerprint, ...]`;
   - alias `RecommendationCatalogReader = ProgramFingerprintReader`;
   - `RecommendationServicePort.rank_fingerprints(...) -> tuple[RankedFingerprint, ...]`;
   - `RecommendationServicePort.recommend_from_fingerprints(...) -> RecommendationResult`.
   Import `Iterable`/`Protocol` only for typing and expose names in `__all__`.
4. In `recommendations.repository.ports`, re-export the Protocols from `contracts.public` so infrastructure and existing tests keep their import path; do not remove or rename repository adapter classes.
5. In `proftest.services.proftest`, replace recommendation imports with public contracts, delete `_CatalogFingerprintReader` and default concrete construction, set `recommendations: RecommendationServicePort` as a required constructor dependency, and assign it directly. Keep `results`, ranking, adaptive validation, profile persistence and logs byte/behaviorally equivalent.
6. Update `docs/architecture.md` module tree to include `admissions`, `admission_fit`, `events`, `campus`; add event flow and campus spatial data statement: point identity/type/address/optional coordinates/relations/events/card data are API payloads, while map visualization/routing remain out of scope. Document public contract/Protocol rule and exact compatibility facades.

### Required Interfaces and Contracts

- No endpoint path, JSON field, database table, migration, fixture, OpenAPI schema, scoring formula or recommendation ordering changes.
- `RecommendationServicePort` is structural and accepts the existing concrete `RecommendationService` and test spy; the test spy must satisfy it without `type: ignore`.
- `RecommendationCatalogReader` remains importable from `recommendations.repository.ports` for infrastructure compatibility.
- `EventListResult` and `area_position` remain the same objects; only their public import surface changes.
- A direct `ProftestService` construction without a recommendation service becomes invalid by type/constructor contract and raises Python's normal missing-argument `TypeError`; current application composition already injects it. This is a boundary-only API used by composition/tests, not an HTTP behavior change.

### Error Handling and Logging

No new HTTP/runtime flow or logs. Missing recommendation dependency is intentionally rejected by Python constructor contract before use; existing validation/log messages and exception behavior inside `results` remain unchanged. Never log the recommendation profile, cookie, token or full payload.

### Tests

- Existing recommendation/proftest/campus/comparison tests must pass unchanged or with import-only test updates if needed.
- Add a focused test that a concrete `RecommendationService` and a typed spy satisfy/work through `RecommendationServicePort`, and that the existing spy still delegates `preview`/`results`.
- Commands: `python -m pytest -q tests/modules/proftest tests/modules/recommendations tests/modules/campus tests/modules/comparison` from `backend`.

### Acceptance Criteria

- Production subject-module imports no longer target cross-module `domain` or `services` for runtime behavior.
- Current HTTP/application flows produce the same contracts and values.
- `docs/architecture.md` no longer omits `events`/`campus` and states map data boundary without implementing a map.

### Verification

- `rg -n "from andromeda\\.modules" backend/src/andromeda/modules -g '*.py'`
- `python -m pytest -q tests/modules/proftest tests/modules/recommendations tests/modules/campus tests/modules/comparison`
- Expected result: cross-module runtime imports use public contracts/approved ports, tests pass.

## Phase Risks and Mitigations

- Risk: changing `ProftestService` constructor breaks an unobserved direct caller. Mitigation: inspect all repository call sites before edit; application/API injection is mandatory and existing direct unit test already passes a spy; record this as an explicit contract decision.
- Risk: circular import while adding Protocols. Mitigation: public contract imports only proftest public types, `RankedFingerprint` from own domain and result/request contracts; service implementation continues importing own repository port.

## Phase Completion Checklist

- Task 2 acceptance criteria and focused tests pass.
- `index.md` task checkbox updated after verification.
