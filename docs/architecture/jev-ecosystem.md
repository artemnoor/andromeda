# Jev ecosystem integration

## Scope

Andromeda remains a modular monolith. Jev tools are integration capabilities
behind typed ports; they do not become domain dependencies or a second backend.

Execution starts from Stage 1 commit e353da4 on branch
feature/jev-ecosystem-stage-2. The earlier feature/university-admin-control
worktree was dirty during audit and is preserved separately.

## Strategy matrix

| Project | Strategy | Runtime role | Boundary |
|---|---|---|---|
| jevcal | DEV/EVAL_TOOL | calibration, ECE/coverage analysis and immutable decision locks | offline scripts and committed lock metadata |
| jev-align | DEV/EVAL_TOOL | uncertain-row acquisition, proposal generation and human review | review queue, manifests and approved semantic artifacts |
| System One Adapter | DEV/EVAL_TOOL | official TypeSafe benchmark/evaluation baseline | optional development dependency and evaluation scripts |
| jevQL | ISOLATED_OPTIONAL_RUNTIME, embedded-first | bounded semantic predicate for rare non-materialized analytics | Python SDK embedded engine, private subprocess, then shared service only if measured and approved |
| jev-tree | ISOLATED_OPTIONAL_RUNTIME | hierarchical choice for genuinely large unresolved candidate sets | Node bridge/service after deterministic narrowing |
| awesome-jev | PATTERN_ONLY | ecosystem reference list | documentation only |

Upstream references:

- https://github.com/abhixhek/jevcal
- https://github.com/sutro-sh/jev-align
- https://github.com/typesafe-ai/system-one-adapter-python
- https://github.com/kylemclaren/jevql
- https://github.com/reachjalil/jev-tree
- https://github.com/AnotiaWang/awesome-jev

The project classification is intentionally stricter than a package list:
evaluation tools do not enter production composition, and optional runtimes do
not become mandatory for canonical ingestion or deterministic analytics.

## Existing Andromeda boundary

The application-facing contracts are:

- DecisionModelPort and DecisionPolicyPort for bounded control decisions;
- SemanticClassifierPort for audited semantic enrichment;
- SemanticPredicatePort for optional jevQL predicates;
- HierarchicalSelectionPort for optional jev-tree candidate selection;
- MetricRegistry and QuerySpec for allow-listed factual analytics;
- AnalyticsResult, ResponsePlan and ResponseEnvelope for explainable,
  channel-neutral results.

Canonical facts, semantic values, program projections and admission facts remain
owned by existing modules. Jev output is untrusted and must be schema-validated
before it is mapped to one of these ports.

The dependency direction is:

    source and ingestion
      → canonical repositories
      → semantic enrichment
      → program projections and metrics
      → deterministic analytics
      → conversation and policies
      → response envelope
      → Web, OG, Telegram and future MAX

No subject module imports a Jev SDK, Node package or isolated service client.
AndromedaContainer is the only composition root.

## Shared Question Registry

The Question Registry is the single source of truth for the cross-tool
definition of a decision operation:

- definition id and kind;
- instructions and criteria;
- definition and schema version;
- typed input/output schema;
- allowed options or bounded score range;
- deterministic fallback;
- redaction and evidence policy;
- evaluation corpus identity;
- calibration lock identity.

The registry does not own technical settings of every tool. Separate validated
configuration remains tool-specific:

- jevcal owns dataset splits, calibration commands, optimizer/cache settings
  and lock generation;
- jev-align owns acquisition, review, proposal, rewind and artifact settings;
- jevQL owns engine mode, budgets, cache, subprocess and endpoint settings;
- jev-tree owns candidate threshold, fanout/depth/call limits and Node runtime.

This keeps the shared semantic contract stable without forcing unrelated
tooling into a false universal configuration.

## Runtime safety rules

1. Deterministic implementations remain enabled and usable when all providers
   are unavailable.
2. No model-generated SQL, repository handle, endpoint, template name or
   canonical entity may be executed without typed validation.
3. Production Jev uses the official TypeSafe SDK or a specifically approved
   TypeSafe-compatible endpoint behind the existing JevTransport and
   DecisionModelPort. System One Adapter is never the production client.
4. jevQL is selected only after MetricRegistry and materialized ProgramMetric
   lookup cannot answer an explicitly registered semantic predicate. Its
   deployment order is embedded Python SDK, private subprocess, then shared
   service only when capability and benchmark evidence require it.
5. jev-tree runs only after exact, alias and contextual deterministic narrowing,
   and only when the candidate set exceeds the measured threshold. A normal
   comparison of twenty programs must make zero jev-tree calls.
6. Missing, partial or unavailable data is never converted to false or zero.
7. External calls have bounded timeout, retry, concurrency, input size and cost.
8. Provider, model, definition, semantic and calibration identities are included
   in safe structured metadata; secrets, cookies and raw private profiles are
   never logged.

## State ownership

DecisionContext is explicit user decision/shortlist state. QuerySession is
conversation memory and separates explicit, inferred and model-candidate values.
decision_analytics is user-action/operational telemetry and is not catalog
analytics or source-of-truth domain state.

## Rollout states

| State | User-visible behavior |
|---|---|
| deterministic | existing deterministic policy and analytics only |
| shadow | deterministic response plus aggregate provider comparison telemetry |
| gated | provider may control only definitions with a valid calibration lock |
| degraded | deterministic fallback with typed unavailable/fallback evidence |

All Jev flags default to disabled. Live enablement requires provider ownership,
secrets/rotation, valid heldout calibration, health checks, benchmark evidence,
security review and a tested rollback.

