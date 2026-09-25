# Phase 07: Human review, manual data и operator workflow

Plan: [index.md](index.md)
Tasks: 18-20
Depends on: Phase 03 and Phase 06

## Цель

Build the full operator review UX on the early immutable approval ledger and reuse semantic-review/university-admin seams. The approval gate is already mandatory before this phase: this phase adds queue/actions/manual-data UX and does not introduce the first approval record or a second ledger. Show evidence, diff, conflict, scope/time, impact and ResolutionTrace before approval.

## Текущие точки интеграции и переиспользуемый код

- Stage 2 `SemanticReviewWorkflow` review lifecycle, proposal/source hashes, stale-source protection, reviewer/time, accepted/rejected/rewound states and publish-after-review; reuse as patterns only, not curriculum-specific records or storage.
- university_admin membership/access; admin_ops access where relevant.
- Existing auth dependencies require_university_admin/editor/owner and require_ops_access.
- API schemas/OpenAPI generation and frontend-next app/client.

## Файлы для изменения

Точные пути и действия для каждого задания указаны в его контракте ниже; вместе эти списки задают весь scope фазы.

<a id="task-18"></a>

## Task 18: Реализовать review transitions и audit

### Контракт выполнения

- Файлы: `modules/knowledge/contracts/review.py`; `services/review_workflow.py`; repository port; add ReviewItem/queue persistence if required; call the policy-owned approval command port introduced in Phase 04; composition and tests.
- Review item uses a discriminated target ref for ClaimCandidate, ChangeCandidate or PolicyRuleCandidate; stores evidence, extraction rationale, proposed target/relations, advisory confidence, current canonical snapshot, diff, impact preview, mandatory ResolutionTrace, conflict, effective date and scope.
- Commands: approve/reject/edit/merge/resolve identity/mark unresolved/mark duplicate. Each Knowledge review action is appended immutably with actor/capability/time/reason/exact revision hash. A PolicyRule approval delegates to the policy-owned append-only event command; claim/fact canonicalization calls its subject owner port. No write endpoint can bypass the Phase 04 exact-revision gate or write policy approval rows directly.
- Permissions: separate proposer/annotator from approver/publisher. Platform steward versus university editor authority for federal/local rules is an explicit decision gate; least privilege default.
- Ошибки и логирование: stale revision requires refresh; idempotency key prevents duplicate approval; auth/validation errors audited without secrets/payload.
- Будущие тесты: transition matrix, actor/scope checks, concurrent revision, duplicate command, owner write failure.
- Критерии приёмки: parser/Jev/LLM cannot approve; resolver rejects absent/stale/non-approve ledger event before this UI ships; canonical write and review command are atomic within one app command/UoW or safely idempotent; no distributed transaction.
- Будущая проверка: python -m pytest backend/tests/unit/test_knowledge_review.py backend/tests/integration/test_knowledge_review.py
- Зависимости: Tasks 7, 9, 13 and 16-17.
- Откат: disable new queue/approval; approved records retain owner and audit.
- Риски: cross-module transaction; use single application command and repositories, not distributed transactions.
- Вне scope: automated reviewer.

<a id="task-19"></a>

## Task 19: Добавить авторизованный source/manual-data workflow

### Контракт выполнения

- Файлы: modules/knowledge/services/manual_source_commands.py; api/routes/knowledge_ops.py and schemas; auth dependencies; API/integration tests.
- Use cases: register source, attach operator document/snapshot, submit manual claim/rule candidate, correct candidate metadata. Require actor/source, reason, times, revision, scope, provenance and optional expiration.
- Authorization: university_admin roles may propose within their university; central policy stewards approve federal rules. Verify resource scope, do not infer authority from role name. No direct database writes from UI.
- Security: reuse URL allowlist, SSRF/redirect/DNS policy, download/PDF caps, MIME validation, upload bound and rendered-text sanitization. Audit access; no secrets or profile data in logs.
- Ошибки и логирование: invalid/expired source stays candidate/review; unauthorized changes rejected and audited; manual data never becomes anonymous truth.
- Будущие тесты: role/scope matrix, immutable audit, expiry, upload/SSRF, redacted logs.
- Критерии приёмки: manual/imported data uses the same staging/review path and cannot bypass to effective rules.
- Будущая проверка: python -m pytest backend/tests/api/test_knowledge_ops.py backend/tests/integration/test_knowledge_manual_data.py
- Зависимости: Task 18 and Phase 00 access decision.
- Откат: disable write routes, preserve audit/snapshots.
- Риски: university editor roles were not designed for federal law; introduce explicit capability check.
- Вне scope: arbitrary SQL/admin direct canonical editing.

<a id="task-20"></a>

## Task 20: Создать review queue с diff и impact preview

### Контракт выполнения

- Файлы: likely frontend-next/src/app/ops/knowledge-review/page.tsx and feature components; verify route layout/auth before implementation; generated API contracts in frontend-next/openapi.json and src/lib/generated.ts.
- Screens: queue; source/evidence detail; structured diff; existing canonical state; trust and policy status separately; scope/effective cycle; conflicts; current/candidate ResolutionTrace; impact preview; approve/reject/edit/merge/unresolved/duplicate; immutable audit timeline.
- Шаги: inspect auth/layout conventions; use typed API only; add accessible loading/error states; approval confirmation names exact revision/scope/effective date.
- Failure: stale revision requires reload; unknown is never shown as “no”; unavailable impact explicit; disable approval when source/scope unresolved.
- Будущие тесты: component/API contracts and browser review/conflict E2E.
- Критерии приёмки: reviewer sees evidence and current-vs-candidate impact before mutation; applicant UI remains unchanged.
- Будущая проверка: frontend lint/build after confirming package scripts; Playwright smoke only if test infra is configured.
- Зависимости: Tasks 18-19 and OpenAPI generation.
- Откат: disable route/flag; preserve audit.
- Риски: current frontend may lack ops shell; confirm exact path before implementation.
- Вне scope: CMS/news reader and applicant exposure of internal enums.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
