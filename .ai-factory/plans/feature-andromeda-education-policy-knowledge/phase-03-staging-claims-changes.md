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

- Файлы: `modules/knowledge/domain/{claim,evidence,change_event}.py`, contracts and repository ports; SQLAlchemy knowledge models and additive migration after Task 6 head `0040_admission_cycle_revisions` (it descends from clean Stage 2 head 0038).
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

- Файлы: existing `backend/src/andromeda/ingestion/contracts/raw.py`, `ingestion/ports.py`, `ingestion/universities/bmstu/fetch.py`, and `infrastructure/repositories/ingestion.py`; fixed adapters in `ingestion/knowledge_source_adapters.py`; bounded poller in `ingestion/knowledge_source_discovery.py`; `modules/knowledge/services/candidate_normalizer.py`; source repository/model additions in `infrastructure/repositories/knowledge_source_repository.py` and `infrastructure/database/models/knowledge.py`; additive migration after 0041; operator/scheduler seam `backend/scripts/discover_knowledge_sources.py`; ingestion/knowledge integration tests.
- Data flow: versioned allowlisted source registry → scheduled or operator-triggered bounded poller → existing capture/fetch policy and content-addressed snapshot → deterministic parser → normalized typed claims/change candidates → schema validation and deterministic entity narrowing → staged records. Keep snapshot, locator, extracted span/hash, parser/adapter version and proposed typed fields. Persist parser version on each immutable poll attempt; unchanged content is re-parsed when the parser version changes, without replacing old candidate history.
- Discovery state: append one `knowledge_source_poll_attempts` row per attempted poll with outcome (new/changed/unchanged/unavailable/removed), last successful/source snapshot hash, retry count, typed failure code, next retry and candidate count. Compare enabled registry entries and due/deferred attempts to report bounded discovery coverage. Reuse IngestRun/SourceSnapshotModel; do not copy raw bodies into knowledge tables.
- Scheduling seam: `backend/scripts/discover_knowledge_sources.py` polls at most 100 due approved registry entries in one invocation; an operator or the already selected operations scheduler can invoke it. It does not run migrations. The CI `source-health` workflow is not that poller, and the host-level systemd timer is a later rollout task. No always-on service, open web crawl or user-provided arbitrary URL. A not-found/disappeared source is an availability observation, never repeal.
- Safety: redirects and DNS are revalidated by current fetch policy; allowlisted hosts/path adapters, download/MIME/PDF limits and request budgets remain enforced. Every redirect is also checked against the exact registry path allowlist before a request. Feed discovery is accepted only for explicitly registered official feeds/APIs.
- Errors: unsupported MIME, oversize and parse timeout use current typed ingestion failures; ambiguity becomes needs_review; absence never creates a relation; failed capture cannot delete old snapshot/canonical data.
- Проверки реализации: `python -m pytest tests/unit/test_knowledge_candidate_normalizer.py tests/unit/test_knowledge_source_poll_attempts.py tests/ingestion/test_knowledge_source_discovery.py tests/infrastructure/test_knowledge_source_repository.py tests/infrastructure/test_alembic_migrations.py tests/ingestion/test_fetch_security.py -q`; targeted Mypy for `modules/knowledge`, source adapters, poller and repository; Ruff for new/changed knowledge files. Existing Stage 2 fetch/repository files may have their pre-existing lint rules ignored only for those exact paths. Also check `python scripts/discover_knowledge_sources.py --help`, Alembic head and `git diff --check`.
- Критерии приёмки: empty-database cold start supports independent candidates with no forced relations; source polling is idempotent/bounded and reports health/gaps; discovery can create observations/snapshots/candidates only and cannot create effective rules. Immutable poll attempts retain outcome, previous/current snapshot hash, parser version, candidate count and bounded retry state; unchanged bytes are re-parsed after an extractor-version change.
- Результат Task 8: focused verification passed: 33 tests across normalizer, poll lifecycle/discovery, source repository, migration and fetch-security suites; targeted Mypy passed 20 source files; new-path Ruff passed after sorting the changed fetch-security test imports; legacy Stage 2 fetch/repository Ruff checks passed with only their known unrelated rules ignored. The database migration assertions include the poll-attempt constraints/indexes, including `parser_version`; `discover_knowledge_sources.py --help` and Alembic history/head also passed. `git diff --check` reported only expected Windows LF-to-CRLF conversion notices.
- Зависимости: Task 5 registry/snapshot contract, Task 7 claim lifecycle and ingestion security policy; production cadence/runner owner approved in Phase 00.
- Откат: disable new source poller/registry revisions only; existing adapters are unaffected. Poll attempt history and immutable snapshots remain audit records.
- Риски: legal PDF layout ambiguity; preserve evidence and require review rather than trust parser confidence.
- Вне scope: OCR expansion, broad crawl/news aggregation, autonomous canonicalization, production Jev classification. Broad multi-university news monitoring is post-pilot and must add registry adapters without changing Knowledge/Policy ownership.

<a id="task-9"></a>

## Task 9: Определять source/claim diffs и безопасно объединять дубликаты

### Контракт выполнения

- Файлы: `modules/knowledge/contracts/diffs.py`, `modules/knowledge/domain/claim_fingerprint.py`, `modules/knowledge/services/candidate_diff.py`; exact-cluster repository port in `modules/knowledge/repository/ports.py`; append-only SQLAlchemy cluster/member models in `infrastructure/database/models/knowledge_candidates.py`; `infrastructure/repositories/knowledge_candidates.py`; migration `0043_knowledge_exact_claim_clusters.py`; `tests/unit/test_knowledge_diff.py`, `tests/infrastructure/test_knowledge_candidate_repository.py`, and migration assertions.
- Diff levels: source byte hash/status from immutable `SourcePollAttempt`; structured claim fields when typed; versioned claim fingerprint; proposed typed candidate. Canonical/effective policy and impact diffs remain later tasks. Keep source observation, snapshot and claim revision links; source disappearance is not repeal.
- Deduplication: cluster only exact normalized assertion fingerprints (`exact_assertion:v1`): Unicode NFKC, casefold and whitespace folding; punctuation, typed subject/scope, stage, valid time and effective time remain significant. Persist cluster membership as a derived review grouping; retain each source-specific claim, locator and evidence unchanged. Claim revisions from later sources join the same cluster only on exact fingerprint equality. Near duplicates stay separate and require review; do not fuzzy match.
- Candidate diff: compare exact fingerprints first. Pair a changed typed proposition only when predicate, subject identity and unit map one-to-one; emit typed field changes for assertion, value, stage and temporal bounds. Multiple matches are `ambiguous`; untyped wording changes stay `added` plus `removed`. A source-unavailable/removed attempt has no claim-set diff and cannot imply a rule/claim repeal.
- Ошибки и логирование: conflicts stay separate and linked; no newest timestamp shortcut; structured logs use IDs only.
- Проверки реализации: `python -m pytest tests/unit/test_knowledge_diff.py tests/infrastructure/test_knowledge_candidate_repository.py tests/infrastructure/test_alembic_migrations.py -q`; targeted Mypy/Ruff for the knowledge contracts/domain/service and candidate repository; Alembic head/history plus `git diff --check`.
- Критерии приёмки: duplicated news yields one reviewable exact claim cluster while every publication keeps a separate candidate and evidence link; same assertion with different typed scope, lifecycle stage or validity/effective window remains separate; missing/disappeared source leaves prior snapshot/candidates and any canonical rule untouched; typed field and temporal diffs exist pre-approval; ambiguous and untyped near matches fail closed.
- Результат Task 9: migration `0043_knowledge_exact_claim_clusters` adds deterministic review-only cluster and member tables; claims/evidence remain source-specific and append-only. Source/candidate diff is derived from poll attempts and exact claim revisions, including typed field and temporal changes only for unambiguous owner/subject matches. Focused verification passed: 22 tests; targeted Mypy passed 21 source files; Ruff passed the knowledge modules, candidate repository, migration assertions, and unit/infrastructure tests. Alembic head is `0043_knowledge_exact_claim_clusters`; `git diff --check` reports only expected Windows line-ending notices.
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
