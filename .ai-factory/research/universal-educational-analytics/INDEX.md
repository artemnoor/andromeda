<!-- aif:research-mode:ultra -->
# Research Index: Universal Educational Analytics Interface

Topic: Универсальный educational analytics и decision interface для Andromeda
Slug: universal-educational-analytics
Updated: 2026-09-21 18:20
Status: historical baseline; current contracts are documented in docs/api.md and docs/architecture.md

## Purpose

Зафиксировать evidence-backed границы и зависимости перед additive refactor Andromeda в universal educational analytics/decision engine.

## Artifact Index

| Artifact | Purpose | Why included | Status |
|----------|---------|--------------|--------|
| [RESEARCH.md](RESEARCH.md) | Active summary and session history | Required; фиксирует scope, constraints, decisions, risks и open questions для `$aif-plan` | active |
| [DEPENDENCY-GRAPH.md](DEPENDENCY-GRAPH.md) | Historical and current dependency direction | Captures the pre-Public-API architecture and target module ownership; current clients use Public API v1 | historical baseline |
| [C4-CONTEXT.md](C4-CONTEXT.md) | External/user/trust boundary | Current backend stays channel-neutral; Web is active and MAX is a future external client | current boundary |
| [C4-CONTAINER.md](C4-CONTAINER.md) | Runtime/data containers and failure boundaries | Captures module/data ownership; physical deployment remains one backend and PostgreSQL | current architecture |

## Reading Order

1. [RESEARCH.md](RESEARCH.md)
2. [DEPENDENCY-GRAPH.md](DEPENDENCY-GRAPH.md)
3. [C4-CONTEXT.md](C4-CONTEXT.md)
4. [C4-CONTAINER.md](C4-CONTAINER.md)

## Traceability

| ID | Finding / requirement | Evidence | Decision or artifact |
|----|-----------------------|----------|---------------------|
| REQ-001 | Semantic feature vectors must be independent of 22-area distribution and non-exclusive | `backend/src/andromeda/modules/disciplines/domain/areas.py`, `modules/disciplines/services/classifier.py` | [RESEARCH.md](RESEARCH.md), [C4-CONTAINER.md](C4-CONTAINER.md) |
| REQ-002 | Program fingerprints are reusable analytics projections, not proftest-only state | `backend/src/andromeda/modules/proftest/services/fingerprint.py`, `services/catalog.py`, `infrastructure/repositories/recommendations.py` | [DEPENDENCY-GRAPH.md](DEPENDENCY-GRAPH.md), [RESEARCH.md](RESEARCH.md) |
| REQ-003 | Canonical ingestion must remain atomic while derived projection rebuild is observable | `backend/src/andromeda/infrastructure/repositories/ingestion.py`, `infrastructure/database/models/ingestion.py`, `scripts/run_andromeda_ingestion.py` | [DEPENDENCY-GRAPH.md](DEPENDENCY-GRAPH.md), [C4-CONTAINER.md](C4-CONTAINER.md) |
| REQ-004 | External clients must not own entity resolution, conversation, response selection or analytics | Public API v1 and existing frontend boundaries | [C4-CONTEXT.md](C4-CONTEXT.md), [RESEARCH.md](RESEARCH.md) |
| NFR-001 | Query path must be bounded and registry-validated; raw SQL from Jev/LLM is forbidden | User request; current FastAPI/SQLAlchemy boundaries in `backend/src/andromeda/api` and `infrastructure` | [RESEARCH.md](RESEARCH.md), [DEPENDENCY-GRAPH.md](DEPENDENCY-GRAPH.md) |
| NFR-002 | Evidence must retain provenance/source gaps through semantic and analytical layers | `backend/src/andromeda/shared/contracts/provenance.py`, `ingestion/contracts/raw.py`, `infrastructure/database/models/ingestion.py` | [RESEARCH.md](RESEARCH.md), [C4-CONTAINER.md](C4-CONTAINER.md) |
