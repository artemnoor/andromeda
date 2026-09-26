# Phase 05: Temporal applicability, precedence и conflicts

Plan: [index.md](index.md)
Tasks: 12-14
Depends on: Phase 04

## Цель

Implement deterministic Effective Rule Resolver: select only exact-revision explicitly approved rules by lifecycle, valid/system time, admission cycle and explicit scope. Every call returns a typed `ResolutionTrace`; ambiguous maximal rules return conflict, never accidental row order.

## Текущие точки интеграции и переиспользуемый код

- Admission Fit uses typed admission_year selection.
- Stage 2 admission_benefits owns its expanded BenefitScope, coverage states, applicant-category confirmation and sole evaluator/calculators; policy selection never substitutes for domain validation/calculation.
- entity_resolution has explicit ambiguity results.
- Phase 02 temporal contracts and Phase 04 bounded selector AST/approval ledger.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-12"></a>

## Task 12: Определить temporal и cohort applicability

### Контракт выполнения

- Файлы: modules/policy/contracts/applicability.py; domain/applicability.py; services/applicability_resolver.py; admissions cycle read port; unit tests.
- Input: target admission_year, resolved AdmissionCycle, academic/application/enrollment dates when known, program/university/direction, route, subject/olympiad/profile, applicant attributes, valid-time as-of and optional system-time as-known-at. Mark user-provided versus source-derived values.
- Logic: require source-backed cycle mapping, valid interval, supported policy lifecycle and a matching explicit approval event for the exact revision hash. A future rule can be reported without being applied to an earlier cohort. Calendar year never substitutes for admission year. The domain owner may still return review-required/insufficient-data under its own guardrails after policy selection.
- Trace: record each considered revision and typed filter outcome/reason for temporal status, valid/system interval and admission-cycle mapping, with canonical evidence references. The trace is required even for zero matches, conflict, or blocked-by-missing-data.
- Ошибки и логирование: missing/conflicting cycle, date or scope yields BLOCKED_BY_MISSING_DATA or UNCERTAIN; no guessed year. Logs contain IDs and rule version, not applicant profile.
- Будущие тесты: identical rule with 2027/2028 applicants; future-effective adopted rule; campaign vs academic year; date boundaries; historical as-known query.
- Критерии приёмки: rule effective in 2028 does not change a 2027 result; typed inputs yield deterministic applicability plus complete ResolutionTrace/evidence, and no unapproved revision is considered eligible.
- Будущая проверка: python -m pytest backend/tests/unit/test_policy_applicability.py backend/tests/unit/test_policy_temporal.py
- Зависимости: Tasks 6, 10 and 11.
- Откат: keep current module-specific read paths until parity gate.
- Риски: admission-cycle mapping can differ by source; require reviewed explicit mapping.
- Вне scope: applying an unapproved proposal as canonical policy.

### Выполнение Task 12

- Added `PolicyResolutionRequest` and versioned, content-addressed `ResolutionTrace` contracts with ordered revision decisions, source evidence, cycle evidence, explicit `valid_as_of`, resolved `as_known_at`, and a fingerprint of typed context without embedding profile payloads.
- Added approved-only repository scans at system time. A revision enters that scan only if its exact hash has an `APPROVED` event by `as_known_at`; pending/rejected/not-yet-known revisions are excluded. Scan is bounded at 500 revisions and deterministic by canonical rule ID/revision.
- `EffectiveRuleCandidateResolver` requires a source-backed `AdmissionCycle` for the exact university/admission year, validates cycle state and bitemporal intervals, keeps policy valid time separate from source effective time, and reports not-yet-effective rules as `FUTURE`. It imports the admissions public cycle contract through a consumer-owned port; composition is deferred until a query/API phase.
- Cycle-owned selector context values (university, admission year, academic year, cycle ID and available application/enrollment date bounds) are marked `SOURCE_BACKED_CYCLE`. User-provided context remains separately marked. Cycle fields cannot be supplied by the caller. New date-valued selector fields use canonical `YYYY-MM-DD` values.
- Missing `valid_as_of`, cycle mapping/state, owner reference or time interval fails closed. An empty approved-rule scan is `INDETERMINATE`, never “no rule.” Each result contains a trace, including blocked/empty results. The trace produces temporal/selector candidates only; Tasks 13–14 must resolve scope/precedence/conflicts before an effective set exists.
- Files: `modules/policy/contracts/resolution.py`, updated `contracts/applicability.py` / `rule_ast.py`, `services/applicability_resolver.py`, policy cycle/clock ports, approved revision repository as-known reads, `tests/unit/test_policy_applicability.py`, and repository approval-time assertions.
- No migration was required for Task 12. At that point, 0044 was the Alembic head; Task 13 adds 0045 for the additive v2 authority/relation schema.

<a id="task-13"></a>

## Task 13: Реализовать authority, specificity и явное разрешение overrides

### Контракт выполнения

- Файлы: modules/policy/domain/precedence.py; services/effective_rule_resolver.py; RuleScope contract/repository; resolver tests.
- Extensible scope targets: federal, regulator, university, campus, faculty, department, education level, direction, program, route, competition, applicant category, olympiad/profile and subject. Store common dimensions relationally; extensions must be registered and typed.
- Precedence: first require exact-revision approval and requested valid/system time; then apply explicit source-backed supersedes/amends/authorized exception edges; compare jurisdictional legal authority and registered scope specificity; keep incomparable survivors as conflict. Source reliability is not precedence. Never use SQL row order or latest timestamp alone.
- Mandatory `ResolutionTrace` contract/version: include request/context IDs and as-of times; deterministic ordered considered-rule entries (revision ID/hash, source evidence refs, approval gate and each stage result); rejection reason codes (unapproved/stale approval, lifecycle, valid-time, knowledge-time, cycle, scope, superseded, exception/override, conflict, unsupported target); relation IDs/evidence for precedence; unresolved conflict refs; final selected domain-rule refs. The resolver accepts AST/payload only from the approved-revision repository; the repository may attach bounded exclusion diagnostics (candidate ID/hash/reason only) for unapproved revisions, never their rule payload, so the trace can explain the approval gate without evaluating them. Do not include raw applicant/profile text.
- Every resolver response returns this structured trace, including empty/no-match or failure states. Impact, review/semantic diff, operations debugging, `ResponseEnvelope.explanation` and regression tests consume the same typed result; no LLM-generated trace prose.
- Ошибки и логирование: tied incomparable rules return CONFLICT and competing evidence; invalid override target rejected; narrower conflict cannot silently fall back to broad rule.
- Будущие тесты: federal-to-university exception, direction/program exception, same-scope conflict, supersession history, stable repeated result.
- Критерии приёмки: documented partial order ends deterministically in one domain-rule set or conflict; repeated identical input returns equivalent ordered rules and trace.
- Будущая проверка: python -m pytest backend/tests/unit/test_policy_precedence.py backend/tests/integration/test_policy_resolver.py
- Зависимости: Task 12.
- Откат: feature flag preserves old reads.
- Риски: jurisdiction ranks require approved configuration; social trust is not legal authority.
- Вне scope: general legal expert system.

### Выполнение Task 13

- Added `policy-rule.v2` with reviewer-assigned `family_id`, legal `authority`, and typed `PolicyRuleRelation`. `policy-rule.v1` remains readable for existing approved rows, but a v1 row has no family/authority and therefore cannot be promoted to a final effective selection until it is explicitly revised and approved as v2.
- Added migration `0045_policy_authority_relations`: nullable v2 metadata constrained by schema version, exact target `(rule_id, revision, content_hash)` FK, and relation provenance FKs to the source revision's exact claim/evidence ordinals. The repository accepts only exact targets already approved as known at source revision time, within the same family; authorized exceptions require resolved authority and strictly narrower registered scope. Override/amend/supersede edges require sufficient authority and equal or narrower scope.
- Added typed scope assessment for every registered scope dimension. Federal scope is the broad default; every other dimension requires a present source/user context value. Unknown or unavailable scope is indeterminate, and a mismatch is filtered before selector candidate creation. Regulator identifiers use the canonical `issuer:` namespace.
- Added a registered partial order: authority ranks only compare rules at the same scope; scope specificity only orders known hierarchy pairs (federal to local, university to local, faculty to department, direction to program, Olympiad to profile) at equal authority. Orthogonal scopes and authority/scope crossings remain conflicts. A lower-authority narrow rule may prevail over a broader rule only through an exact `AUTHORIZED_EXCEPTION_TO` relation; ordinary `EXCEPTION_TO` is not an activation edge. Exact override/supersession/amendment relations take precedence only when authority and scope constraints pass. Rule-family relation cycles fail closed.
- Added `EffectivePolicyResolver` over the approved temporal candidate scan. It re-loads exact approved hashes at the trace system time, computes a deterministic maximal selection per reviewer-assigned family, and returns no effective set when a family conflicts or authority is unresolved. Independent families may coexist. The candidate-only `EffectiveRuleCandidateResolver` remains available as an intermediate service.
- Upgraded `ResolutionTrace` to `policy-resolution-trace.v2`. It retains ordered candidate/filter and explicit scope results, then adds exact precedence pair decisions, relation kinds/evidence, effective exact domain-rule references, or exact conflict participants. The trace remains content-addressed; no source text, profile text, SQL ordering or LLM prose enters precedence.
- Files: `modules/policy/contracts/{applicability,precedence,public,resolution,rule,rule_ast}.py`, `domain/{applicability,precedence}.py`, `services/{applicability_resolver,effective_rule_resolver,__init__}.py`, `infrastructure/database/models/{policy,__init__}.py`, `infrastructure/repositories/policy.py`, Alembic `0045_policy_authority_relations.py`, `tests/unit/test_policy_applicability.py`, `tests/infrastructure/test_knowledge_candidate_repository.py`, and migration tests.
- Verified: combined policy selector/precedence, repository round-trip, migration and architecture-boundary suite: 47 passed in 36.21s; policy source Mypy (26 files) and Ruff passed. Re-run the combined suite after Tasks 14–15 change the trace contract.
- The existing `admission_benefits` evaluator remains the only owner of BVI, 100-point, confirmation and achievement calculations; policy emits only exact approved `DomainRuleRef` selections for the owning evaluator.

<a id="task-14"></a>

## Task 14: Смоделировать conflict groups и безопасный unresolved ответ

### Контракт выполнения

- Файлы: knowledge conflict contract/repository; policy result contract; tests. User API serialization comes in later phase.
- Conflict groups cover contradictory authoritative claims, stale web page versus current signed PDF, federal baseline versus university-specific rule, same issuer amendment, and overlapping scope/time contradiction. Store participants, reason, scope/time, evidence, review state and resolution link.
- Шаги: detect only typed contradictions with overlapping scope/validity; group without auto-resolution; resolve only by explicit supersession or human review; preserve old group and resolution audit.
- Ошибки и логирование: unresolved effective conflict blocks eligibility/impact and says that no unambiguous confirmed answer is available; absence of evidence is unknown, not conflict/no.
- Будущие тесты: authoritative disagreement; explicit repeal; stale page/PDF; resolve and reopen conflict.
- Критерии приёмки: answer exposes source/effective period and unresolved state with trace references; no deterministic benefit/admission action is emitted when effective policy is conflicted.
- Будущая проверка: python -m pytest backend/tests/integration/test_policy_conflicts.py
- Зависимости: Tasks 7, 12 and 13.
- Откат: conflict cases can remain explicitly unresolved; never hide the conflict to recover old behavior.
- Риски: over-grouping could suppress a valid answer; require same typed field plus overlapping scope/time.
- Вне scope: automatic legal adjudication.

### Выполнение Task 14

- Добавлены typed conflict group revisions для exact claim/change-event/policy revision участников, с content-addressed identity, проверкой известного пересечения valid-time, источниковой evidence на каждом участнике и проверкой scope/namespace.
- Добавлен append-only event ledger на каждую immutable group revision. Open/reopen/resolve/dismiss события валидируют последовательность, knowledge time, точный group hash и допустимый participant; supersession resolution требует exact approved policy revision и сохранённой typed precedence relation. Новая revision группы открывает отдельное состояние и сохраняет аудит старой.
- Добавлены PostgreSQL модели и additive migration `0046_knowledge_conflict_groups` с typed participant FK slots, evidence locators, event uniqueness, bounded audit order, checks и индексами. Репозиторий fail-closed проверяет existence/hash/evidence, recorded time и пересечение valid intervals.
- Resolver уже возвращает `CONFLICT` в `ResolutionTrace.v2` с точными competing selections и evidence, без effective rules; общая policy result contract подтверждает, что conflicted/indeterminate/blocking state не может нести effective rule set. Пользовательская сериализация остаётся Task 28.
- Файлы: `modules/knowledge/contracts/conflicts.py`, public exports, `repository/ports.py`, `infrastructure/database/models/knowledge_conflicts.py`, repository implementation, Alembic `0046_knowledge_conflict_groups.py`, миграционные и repository regression tests.
- Проверено: `pytest tests/infrastructure/test_knowledge_candidate_repository.py::test_conflict_group_round_trips_sources_and_preserves_resolution_audit_per_revision tests/infrastructure/test_alembic_migrations.py::test_empty_sqlite_database_reaches_head_and_preserves_constraints -q` — 2 passed.
- Остаточный boundary: human event contract требует account actor, однако полный authorization capability и operator workflow остаются Task 18–20. До них repository не является публичным review API.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
