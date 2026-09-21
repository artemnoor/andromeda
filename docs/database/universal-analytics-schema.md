# Universal analytics schema

The additive Alembic chain is currently:

| Migration | Purpose |
|---|---|
| `0026_semantic_contracts` | versioned semantic features, defaults and item values |
| `0027_semantic_enrichment_lifecycle` | derived semantic runs and audit evidence |
| `0028_program_analytics_projections` | materialized program projections, metrics and evidence |
| `0029_query_sessions` | owner-bound conversation state |
| `0030_semantic_changed_items` | incremental rebuild change-set |

Canonical tables remain the source of truth. Derived tables are rebuildable:

- `semantic_features` is the versioned taxonomy;
- `discipline_semantic_features` stores reusable defaults;
- `curriculum_item_semantic_features` stores context-specific signals;
- `semantic_enrichment_runs` stores lifecycle, versions and changed IDs;
- `program_projections` stores the reusable projection;
- `program_metrics` stores registry-addressable metric rows;
- `program_metric_evidence` stores item-level contributions and provenance;
- `query_sessions` stores owner-bound conversation state and revision.

Indexes cover university/direction projection lookup, metric code/value and
quality/version filtering, evidence by program/metric and curriculum item,
semantic feature lookup and session owner/expiry. Downgrades are provided for
the new migrations; production changes must go through Alembic.
