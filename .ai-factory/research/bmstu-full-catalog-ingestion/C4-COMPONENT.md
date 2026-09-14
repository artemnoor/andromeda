# C4 Component

| Component | Input | Output | Boundary |
| --- | --- | --- | --- |
| `bmstu.tracer.source` | BMSTU URLs | hashed raw snapshots | HTTP/fetch only |
| `bmstu.tracer.parser` | snapshots | raw university/directions/programs/curricula/gaps | source shape only |
| `bmstu.tracer.normalizer` | raw bundle | canonical snapshot | identity/taxonomy only |
| `infrastructure.repositories.ingestion` | canonical snapshot | DB transaction/audit | ORM and persistence |

The existing public API, comparison, recommendation and proftest modules consume canonical contracts and are not part of the source traversal change.
