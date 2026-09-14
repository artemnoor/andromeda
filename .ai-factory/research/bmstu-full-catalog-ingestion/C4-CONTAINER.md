# C4 Container

```mermaid
flowchart TD
  C[Paginated catalog collector]
  D[Detail/profile parser]
  R[Study-plan resolver and PDF parser]
  N[Raw-to-canonical normalizer]
  P[Atomic ingestion repository]
  C --> D --> R --> N --> P
```

- Catalog collector owns pagination and catalog/detail request hashes.
- Detail parser owns source-shape traversal and admissions extraction.
- Resolver owns short links, Yandex metadata, download deduplication and source gaps.
- Normalizer owns canonical IDs, direction/program relationships and taxonomy.
- Repository owns ORM, transactionality, stale-row reconciliation and audit records.
