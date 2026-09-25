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


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
