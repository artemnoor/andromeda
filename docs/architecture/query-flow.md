# Query flow

The typed path for an analytical question is:

```text
natural language
  → deterministic parser or future policy adapter
  → entity/metric resolution
  → QuerySession slot merge
  → DecisionPolicyPort
  → typed QuerySpec
  → QuerySpec validation + MetricRegistry
  → AnalyticsExecutor + repositories
  → AnalyticsResult + evidence
  → ResponsePolicyPort
  → ResponseEnvelope
```

`QuerySpec` contains entity, metrics, scope, canonical filters, aggregation,
sort and a bounded limit. It cannot carry SQL. Unsupported metrics,
aggregations and ambiguous entities are typed errors/states.

Admission questions use the same conversation state but compile to the existing
`BatchAdmissionFitRequest`; they do not create a second admission system.
Missing subject scores produce `ASK_FOR_EXAMS`; missing university scope
produces `ASK_FOR_UNIVERSITY_SCOPE`. Query sessions are owner-bound, persisted
with optimistic revisions and expire after the configured TTL.

Evidence can be followed from `AnalyticsResult` to projection metric, semantic
item feature, curriculum item, source link and captured source snapshot. The
channel receives the explainable envelope, not ORM objects or raw source bodies.
