# C4 Context

```mermaid
flowchart LR
  BMSTU[Official BMSTU catalog and detail API]
  PLAN[BMSTU-published study-plan links]
  YANDEX[Yandex public-resource metadata/download]
  ING[Andromeda BMSTU ingestion adapter]
  DB[(Existing canonical DB)]
  API[Existing API, comparison and recommendations]
  BMSTU --> ING
  PLAN --> ING
  ING --> YANDEX
  ING --> DB
  DB --> API
```

The only authoritative catalog/detail source is BMSTU. Yandex is a linked document transport, not a catalog of its own. Events and campus remain outside the live full-catalog scope because no complete official live source was established in this research.
