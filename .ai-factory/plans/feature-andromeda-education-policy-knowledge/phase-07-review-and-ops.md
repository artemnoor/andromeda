# Phase 07: Human review, manual data и operator workflow

Plan: [index.md](index.md)
Tasks: 18-20
Depends on: Phase 03, Phase 06 and the exact domain-owner impact adapters from Task 24

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

### Факт выполнения

- Добавлены exact-revision review contracts для claim/change-event/policy targets и capability-gated approve/reject/edit/merge/identity/unresolved/duplicate actions. Review item требует evidence, extraction rationale и confidence; policy item также требует semantic diff, impact reference и current/candidate `ResolutionTrace` IDs. Queue read model пока не сохраняется: Task 20 может собирать его из candidate/evidence/diff/impact owners без второй очереди.
- Добавлены owner-side candidate review writes: raw staging API по-прежнему принимает только pending candidates, а review workflow может append-ить только явные human outcomes. Exact source assertion/provenance сохраняется; identity resolution может менять только canonical subject ID после проверки существующим resolver port.
- Добавлен append-only `knowledge_review_actions` с actor, capability, reason, timestamp, exact target/result hashes, related target и actor-scoped idempotency. `KnowledgeReviewWorkflow` требует injected authorization, candidate, audit и UoW ports; exact revision, owner write и audit action атомарны в текущем session/UoW. Authorization/validation logs не включают reason или payload.
- Policy approve/reject делегируются через `PolicyApprovalReviewAdapter` существующему `PolicyApprovalCommandService` и `policy_approval_events`; policy decisions не попадают во второй knowledge ledger. Adapter создаётся composition только при наличии policy capability authorizer; без него команда fail-closed. Повтор exact terminal policy command возвращает исходное owner event; другой terminal command конфликтует.
- Migration `0049_knowledge_review_workflow` добавляет action ledger и разрешает duplicate review state, сохраняя Jev extraction confidence constraint. Downgrade блокируется после review decisions, duplicate states или human-reviewed Jev claims.
- Проверки: targeted unit/infrastructure/Alembic/architecture suites — 44 passed; focused Ruff и Mypy — passed; Task 1 full-run network limitation remains unchanged. Review UI, write API, concrete production authorizer and source/manual-data commands remain Tasks 19-20.
- Rollback: `0049` безопасно откатывается только до появления зависимых review outcomes; после этого downgrade намеренно отказывается терять журнал. Runtime policy approval remains on its existing owner service.

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

### Факт выполнения

- Добавлены authenticated endpoints для source registration, bounded operator document capture, source-backed manual claim submission, exact-hash metadata correction и university-scoped policy candidate submission. Source registration всегда записывает `enabled=false`; upload валидирует PDF signature/UTF-8 plain text, ограничивает чтение до 10 MiB и сверяет URL только с source allowlist без сетевого fetch.
- `knowledge_manual_submissions` хранит actor, university scope, reason, exact target/revision/hash, source observation, idempotency/fingerprint, optional expiry и timestamp. Metadata correction append-ит только pending claim revision и сохраняет assertion/evidence. Policy candidate уходит в существующий `PolicyApprovalCommandService`; новый approval ledger/evaluator не добавлялся, а university-scoped authorizer разрешает только `SUBMIT_REVISION` и запрещает `APPROVE_REVISION`.
- Проверки: `tests/api/test_knowledge_ops.py`, `tests/unit/test_knowledge_manual_commands.py`, `tests/integration/test_knowledge_manual_data.py` — 7 passed; расширенные Task 19/18 boundary, policy, migration и architecture suites — 39 passed; focused Ruff, Mypy и compileall прошли. Alembic head `0050_knowledge_manual_submissions` linear от `0049`; OpenAPI экспортирован в `frontend-next/openapi.json`, `src/lib/generated.ts` regenerated, `check-api-drift` passed. Полный product suite ещё не выполнен.
- Изменены knowledge manual contracts/ports/service/repository/model; policy manual submission wrapper; university-policy scoped infrastructure authorizer; composition/API/schema/settings; migration `0050_knowledge_manual_submissions`; OpenAPI/client; `docs/api.md` и `docs/architecture/knowledge-policy.md`.
- Rollback: выключить три write route families; source snapshots, manual submission audit и pending policy approval events сохраняются. Migration downgrade остаётся guarded против потери audit rows.

<a id="task-20"></a>

## Task 20: Создать review queue с diff и impact preview

### Контракт выполнения

- Файлы: `backend/src/andromeda/api/routes/knowledge_review.py`, schemas/dependencies and repository query ports; actual frontend is the SPA at `frontend-next/src/app/page.tsx` with query routing in `frontend-next/src/lib/router.tsx` and a feature under `frontend-next/src/features/knowledge-review/`; generated contracts in `frontend-next/openapi.json` and `src/lib/generated.ts`.
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

### Факт выполнения и незакрытые acceptance gates

- Добавлены `GET /ops/knowledge/review-queue` и `POST /ops/knowledge/review-actions`, authenticated hidden SPA view, exact-revision list/detail, source reliability separate from policy lifecycle, evidence locators, current policy revision diff, canonical-state explanation, conflict participants/evidence and immutable review/approval history. Pending queries return latest unresolved revisions from owner repositories; the queue itself is a bounded read model, not a new persisted owner.
- Reviewer and policy-steward allowlists are distinct and empty-by-default. Claim/change-event actions are exact-revision, reason-required, idempotent and audited. Open/truncated conflicts block approval. Source-claim approval means only that the source made the assertion; it does not establish a canonical domain fact or activate a policy.
- Added `POST /ops/knowledge/review-preview` backed by `PolicyHypotheticalSandbox`. It loads one approved snapshot and one exact pending policy revision, evaluates both through the shared deterministic resolver/precedence kernel, and returns typed current/candidate `ResolutionTrace`s, approved-snapshot hash, effective-policy diff, domain-owner impact, evidence, and uncertainty. The path is read-only and tagged hypothetical; it never calls the production `EffectivePolicyResolver` with a pending revision.
- Policy approve/reject actions require the exact reviewer preview context and fingerprint. The action route recomputes the preview and checks the fingerprint, exact target hash, candidate resolution, complete owner impact and open/truncated conflicts before approve; the existing `PolicyApprovalCommandService` rejects approve commands without a preview fingerprint, and the existing `policy_approval_events` ledger stores that fingerprint. Migration `0052_policy_approval_preview_fingerprint` adds the nullable audit field while preserving historical events; a guarded downgrade refuses to discard linked approvals. Resolver eligibility remains determined by the approved-only ledger.
- The existing query-view SPA now collects explicit university/admission-year/valid-as-of context and optional scope inputs, renders typed current/candidate traces, effective diff and domain-owner impact/evidence, and offers approve/reject only after a preview. Unknown scope inputs stay unknown. The UI exposes bounded claim proposition edit as a new pending revision and a distinct identity-resolution action; generic edit cannot change subject kind or canonical ID. Identity resolution checks exact existing University/Direction/Program IDs through an infrastructure adapter over the catalog models, and unsupported subject kinds fail closed.
- The owner impact adapter delegates final admission-benefit interpretation to the existing `admission_benefits` reader/evaluator; policy supplies lifecycle, applicability, scope and impact traversal only. The review queue remains a read model over the knowledge and policy owners, with no second queue or approval ledger. The SPA route is still omitted from applicant navigation.
- Verification: targeted backend review/approval/identity/API/migration suites — 34 passed; the earlier sandbox/resolver/impact/domain-owner regression batch — 41 passed; architecture boundary suite — 7 passed; focused Ruff passed; focused Mypy passed with only unresolved Jev import/unused-ignore codes suppressed because local Jev packages are unavailable (same Task 1 environment limitation); frontend review component — 3 passed; TypeScript, ESLint, Next production build and OpenAPI client drift passed. `git diff --check` passed. Alembic migration head is `0052_policy_approval_preview_fingerprint`.
- Acceptance gates are met for operator review preview and claim edit/identity controls. Applicant-facing behavior remains unchanged. Rollback can disable the internal review route/SPA entry; approval fingerprints remain immutable audit data and the migration downgrade is guarded.


## Риски фазы и меры снижения

- Risk: the execution branch, migrations or current symbols may differ after the Phase 00 baseline decision. Mitigation: re-read named paths and confirm the actual Alembic/API branch before edits; update this plan through an explicit review if a contract moved.
- Risk: source trust, legal lifecycle, temporal mapping or scope are treated as implicit defaults. Mitigation: keep unknown values explicit, require evidence/review, and fail closed.
- Risk: a task crosses a current module owner or turns a proposal into canonical truth. Mitigation: route writes through the owner port and preserve feature-off behavior until parity is demonstrated.

## Проверка завершения фазы

- Every task in this phase meets its acceptance criteria on the selected clean implementation baseline.
- Listed future tests, typing/build checks and architecture checks pass for the changed boundary.
- Audit, provenance, rollback and documentation requirements for this phase are recorded.
- Update progress only in index.md after implementation verification; this phase file contains no progress checkboxes.
