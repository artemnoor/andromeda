# Phase 03: Staging claims и changes

Plan: [index.md](index.md)
Tasks: 7-9
Depends on: Phase 02

## Цель

Создать lifecycle от source capture до reviewed candidate. Разделить надежность Source, содержание Claim, Change Event и юридическое состояние Rule. Ingestion производит кандидаты, но не пишет canonical truth.

## Текущие точки интеграции и переиспользуемый код

- Existing IngestionService/runner/adapters, RawSourceSnapshot, SourceSnapshotModel, IngestRunModel, content hashes, retry/idempotency/heartbeat and typed source gaps.
- Stage 2 BMSTU `BmstuAdmissionDocumentCatalog` and admission-benefit source catalog are university-specific adapter examples with official-host checks; reuse their bounded adapter pattern, not the BMSTU parser as a generic registry.
- `.github/workflows/source-health.yml` is a scheduled read-only probe only; `deploy/yc/compose.yaml` has no ingestion worker or production polling schedule.
- ingestion/fetch_policy.py: HTTPS/allowlist/public DNS/redirect validation/limits; pdf_policy.py: bounded MIME/PDF processing.
- modules/semantic review/classification/version/rebuild patterns only.
- admission_benefits provenance and ACTIVE/STALE/REVIEW_REQUIRED/CONFLICT/UNRESOLVED as consumer patterns.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-7"></a>

## Task 7: Смоделировать claims, evidence links, milestones и независимые оси статуса

### Контракт выполнения

- Файлы: `modules/knowledge/domain/{claim,evidence,change_event}.py`, contracts and repository ports; SQLAlchemy knowledge models and additive migration after Stage 2 head 0038.
- Claim is one source assertion with text/span, typed proposition, source observation, evidence locator and extraction method. Evidence is citation linkage, not a copy of canonical fact. ChangeEvent records proposal/publication/adoption/effect/amendment/repeal/withdrawal milestones.
- Independent axes: source reliability (primary normative, official regulator/university, trusted secondary, unverified/community/user/unknown); policy lifecycle (rumor/hypothesis, announced/proposal/draft, adopted/published, effective/future-effective, superseded/repealed/withdrawn/rejected/unknown); candidate/review state. Source reliability never implies adoption or approval.
- This task defines claim/change lifecycle and references the policy-owned approval vocabulary only. It creates no `PolicyRuleRevision`/`RuleCandidate`; those writes begin in Phase 04 only with the immutable exact-revision approval ledger. No unreviewed item is an input to the effective resolver.
- Шаги: define typed state machine and transition table; add constraints/indexes; repository; preserve existing attribution without mass conversion.
- Ошибки и логирование: reject unsupported transition; contradictory evidence creates/joins conflict group; never choose newest row; retain source locator and parser version.
- Будущие тесты: trust-vs-policy state matrix, contradiction, lifecycle transitions, locator serialization.
- Критерии приёмки: official proposal is not effective; secondary evidence can support a claim without changing its trust tier; milestones have source/time.
- Будущая проверка: python -m pytest backend/tests/unit/test_knowledge_claims.py backend/tests/contracts/test_knowledge_contracts.py
- Зависимости: Phase 02.
- Откат: disable candidate writes/reads; keep immutable captures.
- Риски: enum explosion; keep internal axes separate and derive display labels in response policy.
- Вне scope: news feed, universal facts table, automatic canonical updates.

<a id="task-8"></a>

## Task 8: Добавить deterministic parsing и bounded validation кандидатов

### Контракт выполнения

- Файлы: adapter contracts in `modules/ingestion/contracts`; bounded discovery runner/poller in the existing ingestion adapter/use-case layer; `modules/knowledge/services/candidate_normalizer.py`; source/adapter composition in container or current ingestion command; candidate repository; ingestion/knowledge integration tests.
- Data flow: versioned allowlisted source registry → scheduled or operator-triggered bounded poller → existing capture/fetch policy and content-addressed snapshot → deterministic parser → normalized typed claims/change candidates → schema validation and deterministic entity narrowing → staged records. Keep snapshot, locator, extracted span/hash, parser/adapter version and proposed typed fields.
- Discovery state: persist per-source observation outcome (new/changed/unchanged/unavailable/removed), last attempted and last successful observation, source hash, adapter/registry version, failure class/count and bounded next-retry/backoff. Compare expected registry coverage with observations to expose discovery gaps. Reuse IngestRun idempotency/retry metadata and SourceSnapshotModel; do not copy raw bodies into knowledge tables.
- Scheduling seam: poll only registry entries due for observation through one bounded ingestion command/use case invoked by the selected existing deployment/operations scheduler. The CI `source-health` workflow is not that poller. No always-on service, open web crawl or user-provided arbitrary URL. A not-found/disappeared source is an availability observation, never repeal.
- Safety: redirects and DNS are revalidated by current fetch policy; allowlisted hosts/path/feed adapters, download/MIME/PDF limits and request budgets remain enforced. Feed discovery is accepted only for explicitly registered official feeds/APIs.
- Errors: unsupported MIME, oversize and parse timeout use current typed ingestion failures; ambiguity becomes needs_review; absence never creates a relation; failed capture cannot delete old snapshot/canonical data.
- Будущие тесты: deterministic fixtures, retries, malicious PDF/redirect/cross-host blocked by existing policy, malformed date fail closed, no arbitrary URL.
- Критерии приёмки: empty-database cold start supports independent candidates with no forced relations; source polling is idempotent/bounded and reports health/gaps; discovery can create observations/snapshots/candidates only and cannot create effective rules.
- Будущая проверка: python -m pytest backend/tests/ingestion backend/tests/integration/test_ingestion_pipeline.py
- Зависимости: Task 5 registry/snapshot contract, Task 7 claim lifecycle and ingestion security policy; production cadence/runner owner approved in Phase 00.
- Откат: disable new source parser only; existing adapters are unaffected.
- Риски: legal PDF layout ambiguity; preserve evidence and require review rather than trust parser confidence.
- Вне scope: OCR expansion, broad crawl/news aggregation, autonomous canonicalization, production Jev classification. Broad multi-university news monitoring is post-pilot and must add registry adapters without changing Knowledge/Policy ownership.

<a id="task-9"></a>

## Task 9: Определять source/claim diffs и безопасно объединять дубликаты

### Контракт выполнения

- Файлы: knowledge change/diff contracts and service; source-observation queries; later policy diff port; unit and staging integration tests.
- Diff levels: byte hash; structured extraction fields; claim fingerprints; proposed typed candidate; later canonical/effective policy and impact. Keep explicit version/supersedes links. Source disappearance is not repeal.
- Deduplication: exact document identity/hash and stable claim fingerprint can cluster deterministically. Near duplicates retain separate evidence and need review; multiple publications may evidence one logical change.
- Ошибки и логирование: conflicts stay separate and linked; no newest timestamp shortcut; structured logs use IDs only.
- Будущие тесты: unchanged/changed/removed/new, duplicate news, same claim at different time/scope, source disappearance with retained snapshot.
- Критерии приёмки: duplicated news yields one reviewable claim/change cluster with multiple evidence sources; missing/disappeared source leaves prior canonical rule intact; per-source health and gaps remain visible; semantic diff exists pre-approval.
- Будущая проверка: python -m pytest backend/tests/unit/test_knowledge_diff.py backend/tests/integration/test_knowledge_staging.py
- Зависимости: Tasks 7-8.
- Откат: disable clustering/refresh; retain candidates and no canonical rollback is needed.
- Риски: fingerprints can overmerge paraphrases; only exact duplicates auto-cluster.
- Вне scope: general news search/ranking or autonomous truth scoring.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
