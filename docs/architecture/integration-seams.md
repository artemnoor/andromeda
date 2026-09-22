# Integration seams

## Stage 2 execution baseline

Stage 2 remediation runs from the clean baseline commit 105dacb on
feature/jev-ecosystem-stage-2. The earlier feature/university-admin-control
worktree was dirty during research and is preserved as a separate audit source;
it is not a runtime or implementation baseline.

## Jev

Jev integration is optional infrastructure behind typed ports. The default
runtime is deterministic and must remain usable when every external provider
is unavailable. The production decision client is a TypeSafe-compatible
adapter; System One Adapter is evaluation-only and must not be used as the
production client.

Implemented now:

- `TypeSafeJevTransport` → `JevDecisionModelAdapter` → `DecisionModelPort`;
- `ModelBackedDecisionPolicy` and `ShadowDecisionPolicy` → `DecisionPolicyPort`;
- `JevQLAdapter` → `SemanticPredicatePort`;
- `JevTreeAdapter` → `HierarchicalSelectionPort`.

`SemanticClassifierPort` and `ResponsePolicyPort` remain deterministic in the
default composition; future provider adapters must use the same typed seam.

These adapters belong at the composition/integration boundary. Domain,
analytics, admissions and presentation contracts must not import a Jev SDK.
The deterministic implementations remain the testable default.

The shared Question Registry owns operation instructions, criteria, version,
input/output schema and calibration identity. Tool-specific settings stay in
their own validated configuration:

- jevcal: dataset splits, upstream calibration and lock generation;
- jev-align: upstream acquisition/GEPA, review, proposal and rewind settings;
- jevQL: engine mode, budgets, cache and SDK endpoint settings;
- jev-tree: candidate threshold, tree limits and Node runtime settings.

No model output may provide SQL, a repository handle, an endpoint, a template
name or a user fact. The only application-facing boundary is a typed
DecisionModelPort/semantic/resolution port. External responses are
schema-validated and failures fall back to deterministic behavior with a
typed reason.

### Upstream strategy

| Project | Strategy | Boundary |
|---|---|---|
| jevcal | DEV/EVAL_TOOL | Offline calibration and immutable lock artifacts |
| jev-align | DEV/EVAL_TOOL | Human-reviewed semantic proposals and versioned imports |
| System One Adapter | DEV/EVAL_TOOL | Baseline/evaluation reports only |
| jevQL | ISOLATED_OPTIONAL_RUNTIME, embedded-first | `Jevql()` private embedded engine, or `Jevql(url=..., token=...)` shared service |
| jev-tree | ISOLATED_OPTIONAL_RUNTIME | Node adapter only after deterministic narrowing and large-candidate threshold |
| awesome-jev | PATTERN_ONLY | Curated reference list, no runtime dependency |

The common analytics path is materialized metrics and deterministic SQL
aggregation. jevQL may run only for an explicitly registered,
non-materialized semantic predicate with bounded rows and evidence. jev-tree
must not be called for ordinary small candidate sets, including a comparison of
twenty programs.

Production flags are disabled by default. Enabling a provider requires a
validated definition, an immutable calibration lock, health/version checks,
bounded timeout/retry/rate budgets and a tested rollback path.

## State ownership

DecisionContext stores explicit user choices for shortlist/decision flows.
QuerySession stores conversation state, including explicit, inferred and
model-candidate origins. decision_analytics is operational/user-action
telemetry and is not catalog analytics or a source of domain truth.

## MAX

MAX should send an update to `POST /assistant/query`, preserve the returned
`session_id`/`revision`, and map `ResponseEnvelope` to text, image, PDF,
buttons or a Mini App. It should not implement NLP, entity resolution,
analytics, admission fit or response selection.

## Telegram

Telegram is the reference transport. Free-form messages now use the same
assistant endpoint. Existing commands and signed OG routes remain compatibility
adapters until parity is proven. Its local store contains only an encrypted
opaque cookie and query-session metadata; it does not become a business-state
source of truth.

## Web and OG

The Web `queryAssistant` client and `AssistantPage` use the same endpoint.
Existing OG routes retain HMAC/timestamp validation and server-side cookie
forwarding. New generic renderers must consume envelope data and evidence; they
must not query canonical repositories or recalculate metrics.
