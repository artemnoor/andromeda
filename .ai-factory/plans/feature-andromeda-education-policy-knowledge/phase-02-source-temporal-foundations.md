# Phase 02: Источники, provenance и temporal foundation

Plan: [index.md](index.md)
Tasks: 5-6
Depends on: Phase 01

## Цель

Добавить идентичность источника и capture observations поверх immutable snapshots, а также разделить valid-time и system/knowledge-time. Сохранить текущие snapshot hashes и provenance предметных модулей.

## Текущие точки интеграции и переиспользуемый код

- infrastructure/database/models/ingestion.py: SourceSnapshotModel keyed by content_sha256, RawSourceRecordModel, IngestRunModel.
- modules/ingestion: RawSourceSnapshot, fetch policy, PDF policy, source adapters.
- SourceAttribution / BenefitProvenance and source citations in analytics/benefits.
- Clean Stage 2 Alembic head is `0038_admission_offering_scope_and_exam_choices`; revisions 0036-0038 already model benefit source coverage, applicant confirmation category, campus scope and exam choice groups.
- Stage 2 `backend/alembic/env.py` already sizes Alembic version storage for the longest revision ID; do not recreate this safeguard.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-5"></a>

## Task 5: Сохранить source identity и повторные observations

### Контракт выполнения

- Файлы: contracts in `modules/knowledge/contracts/sources.py` and `evidence.py`; domain source/provenance; registry/observation repository ports; `infrastructure/database/models/knowledge.py`; additive Alembic successor to 0038; `infrastructure/repositories/knowledge_source_repository.py`; composition/container.py.
- Data flow: stable publisher/source identity → one or more source observations → existing content-addressed SourceSnapshotModel and IngestRunModel. Observation represents a capture, so same bytes at different URLs/times do not change current benefit FKs.
- Registry: versioned source key/issuer/jurisdiction/source kind/trust tier, approved HTTPS host/path/feed/API allowlist, adapter ID/version, enabled state, polling cadence/freshness budget and expected coverage. Registry URL comes only from reviewed config/database values; no user-supplied arbitrary URL.
- Constraints: stable source_id; unique normalized source identity within jurisdiction; observation FK to snapshot hash and ingest run; immutable captured time/requested/final URL/response metadata. Keep body in current snapshot/blob store. Provenance can identify source, snapshot, locator, field/record key, run and inferred flag.
- Шаги: inventory snapshot-hash FK users; design additive identity/observation relations; preserve existing PK and attribution serialization; implement repository/migration; wire only after contract tests.
- Ошибки и логирование: unknown publisher becomes source reliability unknown and requires review; same hash is idempotent for blob but captures remain distinct; logs use IDs/hash prefix, not body, secrets or URL query values.
- Будущие тесты: PostgreSQL FK/unique/index tests, duplicate bytes with distinct observations, retry idempotency, legacy benefits provenance reads.
- Критерии приёмки: existing ingestion/benefits load unchanged; snapshots remain immutable; many observations can reference one snapshot; evidence chain is reconstructable; registry revisions preserve source history and cannot expand the allowlist implicitly.
- Будущая проверка: python -m pytest backend/tests/integration/test_ingestion_pipeline.py backend/tests/integration/test_admission_benefits.py backend/tests/integration/test_database_postgres.py
- Зависимости: Phase 01 ownership; exact implementation migration parent is Stage 2 head `0038` after clean-worktree/deployment-head verification.
- Откат: disable new observation writes; retain additive schema and existing reads.
- Риски: content hash is not source identity; never replace current primary key.
- Вне scope: open crawler, arbitrary URL intake, snapshot body redesign.

<a id="task-6"></a>

## Task 6: Ввести bitemporal revisions и владельца admission cycle

### Контракт выполнения

- Файлы: temporal contracts in modules/knowledge and modules/policy; modules/admissions/contracts/admission_cycles.py and matching domain/repository port; SQLAlchemy model and additive migration. Claim/review revisions stay with knowledge, policy revisions with policy.
- Temporal semantics: valid time records when a rule/assertion applies; system time records when Andromeda stored this revision. Store published_at, announced_at, adopted_at, effective_from/to, valid_from/to, captured_at and recorded_at only when known. Immutable revisions or closed system-time intervals enable as-known-at queries.
- AdmissionCycle: owned by admissions with admission_year, academic year, application/enrollment periods, source/evidence and state. No implicit effective calendar year equals admission year; mapping needs source-backed cycle or reviewed applicability mapping.
- Шаги: write 2027/2028 and as-known-on examples; decide interval boundaries/date-time/UTC conventions; add typed cycle/revision contracts; migrate additively; document unknown history.
- Ошибки и логирование: reject invalid intervals; missing cycle mapping returns BLOCKED_BY_MISSING_DATA; never fabricate recorded_at for historical imports.
- Будущие тесты: interval boundary, bitemporal point-in-time, 2027 vs 2028 applicability, empty/populated database migrations.
- Критерии приёмки: Dec 1 publication, Dec 15 capture, Sep 1 2028 effect is representable; historical-as-known distinguishes publication/capture/effect; unknown cycle is explicit.
- Будущая проверка: python -m pytest backend/tests/unit/test_policy_temporal.py backend/tests/integration/test_database_postgres.py
- Зависимости: Task 5 and admissions-owner review.
- Откат: turn off temporal read path, retain additive audit; do not invent legal dates for legacy records.
- Риски: prior history may be unreconstructable; expose historical_state_unavailable.
- Вне scope: infer cycles from calendar dates; persist per-user impact.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
