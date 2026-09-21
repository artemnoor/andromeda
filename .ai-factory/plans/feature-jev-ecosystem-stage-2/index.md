<!-- aif:plan-mode:ultra -->

# Plan: Jev ecosystem integration — Stage 2

## Metadata

- Plan ID: feature-jev-ecosystem-stage-2
- Status: planned
- Mode: Ultra
- UI language: ru
- Technical terms: keep
- Testing: enabled
- Logging: verbose during implementation; production logs remain redacted
- Documentation: enabled
- Repository: Andromeda
- Audited branch: feature/university-admin-control
- Audited commit: 8e11ef6
- Audited worktree: dirty with pre-existing user changes; this is not an execution baseline
- Execution baseline: created by Phase 00 from a clean approved Stage 1 commit
- Target branch: feature/jev-ecosystem-stage-2, created only after Phase 00
- Created: 2026-09-21
- Scope: planning only; no implementation performed

## Original Request

Нужно спланировать ВТОРОЙ ЭТАП развития Andromeda после завершённой semantic/catalog analytics migration.

ВАЖНО: текущую архитектуру НЕ переписывать и не создавать параллельные аналоги уже существующих подсистем.

Текущая реализация уже содержит:

- Semantic Layer с versioning, confidence, review status, provenance;
- materialized `ProgramProjection` / `ProgramMetric`;
- typed `MetricRegistry`;
- typed `QuerySpec`;
- `AnalyticsResult`;
- universal deterministic Analytics Engine;
- Entity Resolver с alias/ambiguity handling;
- `QueryFrame` / `QuerySession`;
- adaptive clarification logic;
- `DecisionModelPort`;
- deterministic policy;
- optional Jev adapter + fallback;
- `ResponsePlan` / `ResponseEnvelope`;
- Web assistant;
- OG analytics rendering;
- Telegram integration;
- MAX-neutral transport contract;
- semantic rebuild pipeline;
- analytics benchmarks.

Перед планированием ОБЯЗАТЕЛЬНО исследуй фактический local working tree/repository state. Не полагайся только на это описание.

Цель этого этапа:

> Не изобретать собственные аналоги уже существующих Jev-инструментов, а аккуратно интегрировать лучшие готовые решения экосистемы Jev через существующие ports/adapters/tooling seams Andromeda.

Нужно глубоко исследовать и интегрировать следующие проекты:

1. jevcal  
https://github.com/abhixhek/jevcal

2. jev-align  
https://github.com/sutro-sh/jev-align

3. System One Adapter — официальный TypeSafe  
https://github.com/typesafe-ai/system-one-adapter-python

4. jevQL  
https://github.com/kylemclaren/jevql

5. jev-tree  
https://github.com/reachjalil/jev-tree

Также обязательно исследуй curated ecosystem:

https://github.com/AnotiaWang/awesome-jev

и официальный TypeSafe ecosystem/docs, если это необходимо для правильной интеграции.

НЕ ограничивайся README. Для каждого проекта изучи:

- source layout;
- public API;
- package/runtime dependencies;
- license;
- maintenance status;
- tests;
- current release/install mechanism;
- failure behaviour;
- caching;
- concurrency;
- security assumptions;
- supported providers;
- Python/Node/runtime compatibility;
- whether functionality can be embedded or requires process/service boundary.

Если upstream предоставляет готовую реализацию нужной функции — НЕ переписывай её локально без веской архитектурной причины.

---

# PRIMARY RULE

Для каждого upstream-проекта выбери ровно одну стратегию:

```text
DIRECT_DEPENDENCY
ADAPTER_AROUND_DEPENDENCY
DEV/EVAL_TOOL
ISOLATED_OPTIONAL_RUNTIME
PATTERN_ONLY
REJECT
```

Но `PATTERN_ONLY` или `REJECT` допустимы только после конкретного technical evidence.

Нельзя написать:

> "мы реализуем похожую логику сами"

только потому, что так проще агенту.

Если готовая библиотека может быть безопасно переиспользована — переиспользовать её.

И наоборот: нельзя ломать текущую архитектуру только ради формального подключения dependency.

Главный принцип:

> upstream capability plugs into Andromeda;
> Andromeda does not reshape itself around an upstream demo.

---

# 0. Mandatory repository + upstream audit

Сначала выполнить reconnaissance:

## Current Andromeda

Определить фактические symbols/paths для:

- Semantic Feature definitions;
- discipline feature persistence;
- ProgramProjection;
- ProgramMetric;
- MetricRegistry;
- QuerySpec;
- Analytics Engine;
- Entity Resolver;
- QueryFrame;
- QuerySession;
- adaptive clarification;
- DecisionModelPort;
- deterministic decision model;
- Jev adapter;
- response planning;
- analytics benchmark;
- rebuild scripts;
- configuration;
- observability;
- CI;
- Python dependency management;
- frontend/Node runtime.

Составить current module graph.

## Upstream tools

Для каждого из пяти проектов построить:

```text
capability
runtime
dependency type
API surface
state/cache
failure behaviour
license
security properties
what overlaps Andromeda
what Andromeda currently lacks
recommended seam
```

Перед implementation plan сделать explicit:

### REUSE MATRIX

| Upstream | Existing Andromeda equivalent | Missing capability | Integration strategy | Why |
|---|---|---|---|---|

Не начинать implementation phases до завершения этой матрицы.

---

# 1. jevcal — calibration and confidence governance

Repository:

https://github.com/abhixhek/jevcal

Назначение:

НЕ угадывать confidence thresholds вручную.

`jevcal` должен стать официальным calibration/evaluation инструментом для bounded Jev decisions Andromeda.

Исследуй реальный upstream CLI/API и спланируй использование существующих функций:

- `lint`;
- `measure`;
- `compile`;
- `run`;
- `optimize` where appropriate;
- `check`;
- generated decision lock;
- accepted accuracy;
- handled coverage;
- ECE;
- top_prob / margin / entropy;
- held-out validation;
- conservative confidence bounds;
- drift checks.

Не создавать собственный threshold optimizer, если upstream jevcal закрывает задачу.

## Decisions to calibrate

Минимум:

```text
intent resolution
next-action selection
metric resolution
presentation selection
semantic feature classification
```

Если какие-то decision class плохо соответствуют jevcal input/output — обосновать отдельно.

## Runtime integration

Исследуй возможность использовать `decisions.lock.json` как versioned runtime calibration artifact.

Цель:

```text
Jev raw probabilities
       ↓
jevcal-derived threshold
       ↓
accepted
or
fallback/unresolved
```

НЕ должно остаться:

```text
if confidence > 0.9:
```

без empirical calibration.

Low-confidence → deterministic fallback / LLM baseline / unresolved в зависимости от decision class.

## CI

Спланировать CI gate:

```text
jevcal check
```

но:

- не делать live paid API обязательным для каждого unit-test run;
- разделить offline/unit CI и explicit external/model drift gate;
- model-version drift должен быть видимым;
- secrets не попадать в CI output.

## Data

Создать evaluation corpus conventions:

```text
evals/jev/
```

или другое repository-consistent location.

Не коммитить sensitive raw user conversations.

Разрешить:

- curated synthetic examples;
- sanitized production examples;
- manually labelled examples.

Нужно versioning evaluation corpus.

---

# 2. jev-align — active learning for Semantic Layer

Repository:

https://github.com/sutro-sh/jev-align

Назначение:

не размечать вручную тысячи дисциплин и не бесконечно править semantic definitions руками.

Использовать upstream `jev-align` как operator/development tool для:

```text
current semantic definition
       ↓
dataset
       ↓
Jev predictions
       ↓
uncertain/audit samples
       ↓
human labels
       ↓
GEPA proposal
       ↓
human review
       ↓
accepted new definition version
```

КРИТИЧНО:

`jev-align` НЕ должен автоматически изменять production taxonomy/definitions.

Любой proposed definition:

```text
PROPOSED
↓
human review
↓
explicit acceptance
↓
new semantic definition version
↓
controlled rebuild
```

## Integration

Не дублировать active-learning algorithm.

Вместо этого сделать тонкие Andromeda tools:

```text
export_semantic_training_dataset
        ↓
jev-align
        ↓
import/inspect accepted definition artifact
        ↓
semantic definition registry
```

Исследуй формат CSV/Parquet/JSONL upstream и используй его напрямую.

Использовать existing Andromeda semantic provenance, versions, review status и rebuild mechanism.

## Capture

Исследуй upstream `AIFunction.load(..., capture=True)`.

Если подходит архитектурно, использовать capture только для sanitized/approved examples.

Не отправлять private profile/user data без explicit policy.

`.jev-align/` local runs, credentials и potentially sensitive datasets должны быть корректно gitignored.

---

# 3. Official System One Adapter — Jev vs LLM baseline

Repository:

https://github.com/typesafe-ai/system-one-adapter-python

Это официальный TypeSafe project.

Не писать собственную LLM compatibility wrapper, если официальный adapter закрывает задачу.

Назначение:

одни и те же System One questions прогонять через:

```text
Jev
vs
DeepSeek
vs
GPT
vs
Claude
vs other OpenAI-compatible models
```

с максимально одинаковым decision contract.

Использовать официальный API:

```text
SystemOneAdapterClient
AsyncSystemOneAdapterClient
Noul
Choice
Score
```

и upstream telemetry:

```text
input_tokens_total
output_tokens_total
n_retries
malformed_structure retries
latency
debug diagnostics
```

## Important

System One Adapter — преимущественно EVAL/BASELINE tooling.

НЕ заменять им production Jev adapter.

Он должен позволить нам ответить на реальных Andromeda задачах:

```text
accuracy
accepted accuracy
coverage
latency
token usage
cost
schema failure rate
retry rate
```

для Jev и LLM.

Сделать один shared decision dataset/questions definition, насколько это технически возможно.

Не поддерживать две несовместимые копии criteria/instructions.

## Benchmark

Нужен reproducible benchmark:

```text
backend/scripts/profile_decision_models.py
```

или repository-consistent equivalent.

Пример результата:

```text
decision class
provider/model
accuracy
coverage
p50/p95 latency
input/output tokens
estimated/actual cost
schema failures
retry count
```

Нельзя хардкодить маркетинговый вывод "Jev лучше".

Benchmark должен честно показывать случаи, где LLM выигрывает.

---

# 4. jevQL — semantic predicates inside typed analytics

Repository:

https://github.com/kylemclaren/jevql

Это самая архитектурно чувствительная интеграция.

Сначала глубоко изучи actual source.

jevQL предоставляет semantic SQL family:

```text
jev(...)
jev_prob(...)
jev_choice(...)
jev_score(...)
jev_score_norm(...)
jev_confidence(...)
jev_eval(...)
```

и модель:

```text
SQL pre-filter
→ collect rows
→ batch Jev judgement
→ cache
→ semantic filter/group/order/project
```

Нам нужна его сильная сторона:

> выполнять semantic predicates поверх уже детерминированно отфильтрованного набора данных.

Но НЕ разрешается:

- user-generated raw SQL;
- model-generated raw SQL;
- обход MetricRegistry;
- arbitrary table access;
- sending whole database rows externally;
- превращать jevQL в второй основной Analytics Engine.

## Desired role

jevQL должен быть исследован как backend для НОВОГО bounded seam, например:

```text
SemanticPredicatePort
```

Концептуально:

```text
typed QuerySpec
       ↓
deterministic SQL narrowing
       ↓
small bounded candidate set
       ↓
semantic predicate
       ↓
jevQL adapter
       ↓
typed semantic result
       ↓
existing AnalyticsResult
```

Примеры новых вопросов:

> «Какие программы более практико-ориентированные?»

> «Найди дисциплины, где реально много работы с данными, даже если это не видно из названия».

> «Найди программы, похожие по содержанию на эту».

Но сначала проверить:

1. нельзя ли ответить existing materialized Semantic Features;
2. только если metric/feature ещё не materialized — semantic runtime predicate допустим.

То есть приоритет:

```text
existing deterministic/materialized metric
        ↓ if impossible
registered semantic predicate
        ↓
jevQL
```

НЕ наоборот.

## Direct dependency

Исследуй официальный Python SDK:

```text
pip install jevql
```

и возможность использовать `Jevql` directly.

Проверь:

- actual platform support;
- Windows development compatibility;
- Linux production compatibility;
- bundled binary behaviour;
- CGO/native requirements;
- process lifecycle;
- connection handling;
- cache;
- concurrency;
- cancellation.

README указывает native/prebuilt caveats — проверить код/releases, не предполагать поддержку платформ.

Если Python package безопасно embedится → `ADAPTER_AROUND_DEPENDENCY`.

Если нет → исследовать `jevql serve` как optional isolated runtime.

НЕ создавать отдельный microservice автоматически.

Sidecar/service допустим только если:

- direct embed невозможен;
- deployment impact приемлем;
- benchmark доказывает пользу;
- failure mode не ломает core analytics.

## Security

Использовать:

- read-only PostgreSQL credentials;
- allow-listed relations;
- allow-listed columns;
- explicit column minimization;
- max rows;
- max chars;
- bounded concurrency;
- cost budget;
- timeout;
- explain/preflight;
- no raw credentials in logs.

Особенно использовать upstream идею:

```text
cheap indexed SQL predicates first
→ Jev only on surviving rows
```

## Cache

Не писать второй cache без необходимости.

Исследовать upstream cache key:

```text
model
kind
question
options
canonical row JSON
```

и определить, можно ли его использовать напрямую.

---

# 5. jev-tree — hierarchical selection

Repository:

https://github.com/reachjalil/jev-tree

Назначение:

Jev Choice имеет ограниченное пространство options; реальные каталоги Andromeda могут содержать сотни/тысячи:

- programs;
- disciplines;
- semantic metrics;
- universities;
- possible entities;
- aliases;
- future actions.

Использовать `jev-tree`, когда flat candidate choice становится слишком большим или начинает терять quality.

НЕ использовать tree для списка из 10 вариантов без причины.

## Desired seam

Исследуй введение:

```text
HierarchicalSelectorPort
```

или extension существующего entity/decision resolver.

Use cases:

```text
free text
→ entity candidate universe 2000+
→ deterministic lexical narrowing where possible
→ jev-tree when semantic hierarchical selection is still required
→ resolved entity
```

и:

```text
unknown semantic request
→ metric taxonomy
→ jev-tree
→ canonical MetricRegistry ID
```

## IMPORTANT runtime mismatch

Upstream `jev-tree` сейчас является Node/npm library.

Andromeda core backend — Python.

НЕ переписывать `jev-tree` на Python автоматически.

НЕ помещать domain logic во frontend/Telegram/MAX только потому, что там есть JS.

Исследовать варианты в таком порядке:

1. существует ли официальный/community Python-compatible interface/version;
2. можно ли использовать package через уже существующий Node server runtime без нарушения backend boundaries;
3. возможно ли использовать небольшой isolated bridge;
4. оправдан ли bridge фактическим candidate volume/benchmark.

Если direct runtime integration требует отдельного сервиса только ради редкого кейса — спланировать feature-flagged/optional integration и сохранить current deterministic resolver как fallback.

Но обязательно использовать upstream project для experiments/evaluation; не изобретать альтернативный tree algorithm до сравнения.

Использовать upstream protections:

```text
maxFanout
timeoutMs
maxDepth
maxCalls
shape validation
unavailable instead of invented leaf
injectable evaluator for tests
```

---

# 6. Shared Jev Question Registry

После изучения пяти проектов предложи способ избежать главной потенциальной проблемы:

> пять инструментов начинают хранить пять копий одних и тех же Jev instructions/criteria.

Нужен ONE SOURCE OF TRUTH для decision definitions, насколько это возможно.

Например:

```text
DecisionDefinition
  id
  version
  type: noul | choice | score
  instructions
  criteria/options
  target accuracy
  owner
```

или существующий repository-equivalent.

Из него должны максимально генерироваться/адаптироваться:

```text
production Jev adapter
jevcal questions
System One Adapter benchmark
jev-align tasks
jev-tree nodes where applicable
```

Не создавать duplication вручную.

Версионировать definitions.

Каждый runtime decision должен быть traceable до definition version.

---

# 7. Decision pipeline

Целевой pipeline должен выглядеть примерно так:

```text
User request
   ↓
QueryFrame
   ↓
deterministic resolution
   ↓
can deterministic path resolve?
   ├── yes → continue
   ↓ no
bounded Jev decision
   ↓
jevcal confidence gate
   ├── confident → accept
   └── uncertain → fallback/unresolved
   ↓
QuerySpec
   ↓
deterministic Analytics Engine
   ↓
missing semantic predicate?
   ├── no → result
   └── yes
        ↓
    bounded candidate rows
        ↓
    jevQL semantic predicate
        ↓
    typed result
   ↓
ResponsePlan
```

For large choice spaces:

```text
candidate universe
→ deterministic narrowing
→ if still too large
→ jev-tree
```

Evaluation/offline:

```text
same decision definitions
   ├→ Jev
   ├→ System One Adapter / LLM
   ├→ jevcal
   └→ jev-align feedback loop
```

---

# 8. Do not duplicate existing Andromeda functionality

Before adding code, explicitly identify overlaps.

Examples:

## Existing confidence/fallback

If current `JevDecisionModelAdapter` already has confidence policy:

DO NOT add another independent policy next to it.

Make jevcal artifacts configure/replace that policy.

## Existing semantic rebuild

jev-align must feed definition improvement into existing rebuild.

DO NOT create second semantic database.

## Existing AnalyticsEngine

jevQL is not a replacement.

It is a semantic operator/backend only where existing typed metric cannot answer.

## Existing EntityResolver

jev-tree extends it for large semantic spaces.

It does not replace deterministic alias/exact resolution.

## Existing benchmark

System One Adapter must extend current profiling/evaluation infrastructure.

Do not create disconnected benchmark scripts unless existing boundaries make reuse impossible.

---

# 9. Provider abstraction

Current Andromeda already has `DecisionModelPort`.

Preserve provider neutrality.

Support Jev providers according to actual upstream capabilities and current config:

```text
TypeSafe direct
Polza if current adapter supports it
OpenRouter if supported
Vercel/Cloudflare where required by upstream tool
```

Do NOT force the entire product onto Vercel solely because jev-tree uses Vercel Gateway.

Provider-specific requirements belong in infrastructure/tool adapters.

---

# 10. Feature flags

Every new integration must be separately controllable.

Conceptually:

```text
JEV_ENABLED
JEV_CALIBRATION_ENABLED
JEV_ALIGN_CAPTURE_ENABLED
JEVQL_ENABLED
JEV_TREE_ENABLED
LLM_BASELINE_ENABLED
```

Use repository's existing config conventions instead of inventing names blindly.

Core user flows must continue to function with ALL external Jev tooling disabled.

---

# 11. Failure/degraded behaviour

Required:

### jevcal artifact unavailable
→ fail closed to existing safe threshold/fallback policy; log configuration error.

### Jev unavailable
→ existing deterministic/fallback behaviour.

### jevQL unavailable
→ semantic predicate returns unavailable; never fabricate result.

### jev-tree unavailable
→ deterministic candidate list / clarification / unresolved.

### LLM baseline unavailable
→ benchmark/eval fails explicitly; production unaffected.

### jev-align unavailable
→ semantic rebuild still works with current accepted definitions.

No external tool is allowed to make canonical ingestion unavailable.

---

# 12. Observability

Reuse existing telemetry.

Add tool-specific fields without leaking content:

```text
decision_definition_id
decision_definition_version
decision_source
model/provider
calibration_lock_version
confidence
accepted_by_gate
fallback_reason

jevql_candidate_rows
jevql_cache_hits
jevql_batch_count
jevql_latency
jevql_estimated_cost

jev_tree_depth
jev_tree_calls
jev_tree_final_reason

system_one_baseline_provider
system_one_latency
system_one_input_tokens
system_one_output_tokens
system_one_retries

jev_align_definition_version
```

Do not log:

- API keys;
- DB passwords;
- raw private user text;
- full private profiles;
- raw rows sent to semantic providers unless explicit debug fixture.

---

# 13. Testing

Testing REQUIRED.

For each integration use upstream fakes/injection points where available instead of mocking internals blindly.

Need:

## jevcal

- fixture corpus;
- compile lock;
- threshold application;
- low-confidence fallback;
- drift detection;
- model-version mismatch.

## System One Adapter

- same questions produce same typed response contract;
- malformed structured output;
- corrective retries;
- token/latency accounting.

## jev-align

- export dataset;
- accepted definition import;
- rejected proposal changes nothing;
- semantic version bump;
- rebuild only affected projections.

## jevQL

- deterministic SQL narrowing occurs before semantic calls;
- only allow-listed columns leave process;
- row/cost limit;
- cache;
- timeout;
- unavailable semantics;
- no user SQL execution;
- PostgreSQL integration test.

## jev-tree

- >255 candidate fixture;
- deep hierarchy;
- max fanout;
- max depth;
- timeout;
- unavailable;
- fake evaluator;
- exact IDs preserved;
- deterministic resolver bypasses tree when exact match exists.

## Regression

Existing:

```text
backend suite
mypy
migration tests
alembic check
frontend tests/build/lint
telegram tests/mypy
OpenAPI drift
architecture checks
docs checks
deployment checks
```

must remain green.

PostgreSQL-only tests must be run with actual PostgreSQL before completion.

Playwright should also be included in final integration gate if current project supports it.

---

# 14. Benchmarks before enabling production paths

Do NOT enable an upstream tool merely because integration works.

For every runtime integration create A/B evidence.

## jevcal

Compare:

```text
handwritten/default threshold
vs
calibrated threshold
```

## jevQL

Compare:

```text
materialized semantic metric
vs
runtime semantic predicate
```

Measure:

```text
quality
latency
cost
candidate rows
cache effectiveness
```

## jev-tree

Compare:

```text
flat/batched current resolver
vs
hierarchical selector
```

on realistic candidate sets.

## System One Adapter

Jev vs selected LLM baseline.

Output machine-readable benchmark artifacts.

No invented performance claims.

---

# 15. Dependency policy

Do not vendor-copy upstream source unless unavoidable.

Prefer:

```text
pinned dependency
+
adapter
```

Pin versions/commit SHAs according to current project dependency conventions.

For git-only packages such as jevcal if still not on PyPI, evaluate:

- pinned git SHA;
- reproducibility;
- supply-chain risk.

For Node/npm packages pin lockfile normally.

Document upstream licenses.

Add dependency only to the scope that actually needs it:

```text
runtime
dev
eval
operator
```

Do not make `jev-align`, LLM SDKs, or benchmark dependencies part of minimal production runtime unnecessarily.

---

# 16. Security review

Particularly inspect jevQL.

Requirements:

- no arbitrary natural-language-to-SQL;
- no generated SQL execution;
- read-only DB access if separate connection is used;
- allow-listed tables/columns;
- prefilter locally/SQL before semantic provider;
- candidate hard limit;
- request character/token hard limit;
- timeout;
- concurrency cap;
- cost budget;
- rate limit;
- provider output validation.

Model output is untrusted data.

For jev-align:

- labels may contain sensitive source text;
- local run artifacts must not be accidentally committed/published;
- never automatically `push` to ai-functions.dev;
- publishing must be explicit manual operator action and disabled by default.

---

# 17. Documentation

Required docs:

```text
docs/jev-ecosystem.md
```

or repository-consistent equivalent.

Explain simply:

### jevcal
"How sure must Jev be before Andromeda trusts it?"

### jev-align
"Which semantic definitions need improvement, and what should a human label next?"

### System One Adapter
"Would a normal LLM do this task better/cheaper/slower?"

### jevQL
"Can we apply a new semantic condition to a bounded set of real database rows?"

### jev-tree
"How do we choose correctly when there are too many possible options for one Jev choice?"

Also document:

```text
production vs evaluation dependencies
feature flags
fallbacks
calibration workflow
active-learning workflow
benchmark workflow
security/data egress
```

---

# 18. Desired user-facing capabilities after integration

Integration is not complete merely because packages import successfully.

Demonstrate end-to-end scenarios.

## Scenario A — calibrated adaptive dialogue

User:

"Куда я прохожу с 270 баллами?"

Decision engine chooses missing EGE question.

jevcal-derived gate decides whether to trust the action.

If uncertain → deterministic fallback.

## Scenario B — novel semantic query

User:

"Покажи программы, где обучение более практическое, но без сильного уклона в программирование."

Existing materialized features used first.

If a supported semantic condition is not materialized:

typed query
→ bounded candidates
→ jevQL semantic predicate
→ typed AnalyticsResult.

## Scenario C — large entity resolution

User enters an ambiguous/free-form entity among a catalog larger than Jev flat-choice capacity.

exact aliases fail
→ deterministic narrowing
→ jev-tree
→ canonical entity ID.

## Scenario D — Jev vs LLM evaluation

Same Andromeda decision corpus:

```text
Jev
DeepSeek/OpenAI-compatible baseline
Claude where configured
```

via System One Adapter.

Produce accuracy/latency/cost/retry results.

## Scenario E — semantic improvement

Current feature definition has uncertain classifications.

Export examples
→ jev-align
→ label uncertain samples
→ proposed definition
→ human accepts
→ definition version bump
→ semantic rebuild
→ affected ProgramProjection refresh only.

---

# 19. Plan structure

Create an ULTRA implementation-ready plan.

Before task phases include:

1. Current local repository state.
2. Current Jev implementation.
3. Upstream source audit.
4. Reuse matrix.
5. Dependency/runtime compatibility matrix.
6. Proposed target architecture.
7. Proposed data/control flow.
8. Risks.
9. Explicit rejected integration approaches and why.

Suggested phases conceptually:

```text
Phase 1 — upstream audit + shared decision definition registry
Phase 2 — System One Adapter evaluation harness
Phase 3 — jevcal calibration + runtime gate + CI drift
Phase 4 — jev-align semantic active-learning workflow
Phase 5 — jevQL bounded semantic predicate adapter
Phase 6 — jev-tree hierarchical resolution adapter
Phase 7 — unified observability/config/fallbacks
Phase 8 — end-to-end scenarios + PostgreSQL/Playwright
Phase 9 — benchmark and production enablement decision
```

Do not blindly use these phases if repository evidence suggests a better dependency order.

For EVERY task include:

- exact existing files/symbols;
- upstream files/API being reused;
- dependency/version;
- why reuse is preferred over custom implementation;
- adapter boundary;
- config;
- data flow;
- error behaviour;
- tests;
- logging/telemetry;
- benchmark/acceptance criteria;
- migration concerns;
- rollback;
- feature flag;
- upstream link.

Commit checkpoints every 3–5 tasks.

---

# 20. Strict non-goals

DO NOT:

- rewrite current Semantic Layer;
- rewrite current AnalyticsEngine;
- remove MetricRegistry;
- replace QuerySpec with SQL strings;
- expose jevQL to user-generated SQL;
- move business logic into frontend/Telegram/MAX;
- create a new database for Jev tooling;
- turn jev-tree into the default resolver for tiny candidate sets;
- let jev-align autonomously alter production definitions;
- let jevcal make paid network calls in every unit CI run;
- introduce a generic agent framework;
- introduce microservices only to satisfy a dependency;
- duplicate current `DecisionModelPort`;
- create local clones of upstream libraries without strong evidence;
- delete deterministic fallback paths.

---

# Final architectural invariant

After this work the following must be true:

> Andromeda owns the domain, data model, typed analytics and deterministic business logic.

> Jev ecosystem tools enhance bounded semantic decisions through narrow adapters.

Specifically:

```text
jevcal
→ calibrates trust

jev-align
→ improves semantic definitions

System One Adapter
→ provides fair LLM baselines

jevQL
→ provides bounded runtime semantic predicates over pre-filtered data

jev-tree
→ resolves very large hierarchical choice spaces
```

None of them becomes "the architecture".

They plug into the architecture that already exists.

---

# Mandatory quality gate

Before recommending implementation of each upstream integration, answer:

1. What exact current Andromeda problem does it solve?
2. What existing code does it replace, configure, or extend?
3. Are we actually using upstream code, or accidentally reimplementing it?
4. Is direct dependency technically compatible?
5. What happens when it is unavailable?
6. What measurable improvement do we expect?
7. What benchmark will prove or disprove that improvement?
8. Can it be removed later without touching domain logic?

If those questions cannot be answered, do not hide the uncertainty.

Mark the integration as experimental/blocked and explain exactly what evidence is missing.

After planning STOP.

Do not implement yet.


## Revision notes

This plan was revised after review. The previous dirty branch is now explicitly research-only. Stage 2 cannot start until the completed Stage 1 migration is isolated in a clean baseline commit/branch and all Stage 1 verification passes.

JevQL is embedded-first: the preferred order is Python SDK embedded engine, then private subprocess, then shared service only when the first two modes are technically unsuitable. A shared service is not the default.

T19 now includes a real production TypeSafe Jev client/transport behind the existing DecisionModelPort. System One Adapter remains evaluation-only and cannot satisfy production runtime integration.

The Question Registry is the source of truth for operation instructions, criteria, version and output schema. Tool-specific settings remain tool-owned configs around it; jevcal, jev-align and jev-tree are not forced into one universal technical configuration.

## Executive summary

Цель второго этапа — не создавать собственные аналоги upstream Jev-инструментов и не строить второй backend, а подключить их за существующими typed ports/adapters Andromeda.

Фактическое состояние репозитория лучше, чем greenfield baseline: semantic layer, materialized ProgramProjection/ProgramMetric, MetricRegistry, QuerySpec, AnalyticsResult, Entity Resolver, QueryFrame/QuerySession, deterministic decision/response policy, assistant API, OG/Web/Telegram contracts и generic Jev adapter уже существуют. Однако Jev сейчас не является рабочей runtime dependency: adapter не wired в composition root, отсутствуют shared Question Registry, production feature flags, calibration lock, shadow mode, reviewed Jev-align loop, jevQL/jev-tree adapters и CI gates.

План сохраняет modular monolith, canonical source-backed data, PostgreSQL/SQLAlchemy/Alembic, существующие admission/recommendation/comparison/proftest-compatible consumers, MAX-neutral envelope и deterministic fallback. New upstream components are deliberately split into evaluation tooling versus isolated optional runtimes.

## Current Repository State

### Confirmed reusable components

- backend/src/andromeda/modules/semantic/: versioned feature values, confidence, review status, provenance, SemanticClassifierPort, deterministic RuleBasedSemanticClassifier, idempotent/changed-only enrichment.
- backend/src/andromeda/modules/program_analytics/: common ProgramProjection, fingerprint/projection builder, hours/credits, academic areas, semantic metrics, timeline, evidence and data quality.
- backend/src/andromeda/modules/analytics/: typed QuerySpec, allow-listed filters/sorts/aggregations, MetricRegistry, deterministic AnalyticsExecutor, repositories and explainable AnalyticsResult.
- backend/src/andromeda/modules/conversation/: QueryFrame, QuerySession, DecisionModelPort, DecisionPolicyPort, RuleBasedDecisionModel, deterministic policy, assistant orchestration, existing evaluation service.
- backend/src/andromeda/infrastructure/jev/adapter.py: generic JevTransport, JevDecisionModelAdapter, typed mapping/fallback/allowed presentation validation, but no official provider client.
- backend/src/andromeda/composition/container.py: deterministic policies and semantic classifier are wired; Jev adapter is not wired.
- backend/src/andromeda/infrastructure/config/settings.py: typed settings/redaction conventions exist; no Jev settings yet.
- Existing POST /assistant/query, POST /analytics/query, Web assistant, OG analytics routes, Telegram transport and MAX-neutral contracts.
- Existing migrations through 0033 for semantic/projection contracts; no Jev-specific migration.
- Existing evaluation script/service and architecture checks; no calibration/shadow/evaluation CI gate.
- .github/workflows/andromeda-ci.yml already covers backend, frontend, Telegram, architecture, migrations, PostgreSQL integration and documentation.

### Partial or absent capabilities

- Shared operation/question definitions are duplicated conceptually between policies and adapter; no registry artifact. Tool-specific technical settings are intentionally not unified yet.
- DecisionModelPort is present, but Jev runtime is generic and optional only by type; no real production TypeSafe/provider client with lock identity is wired.
- Deterministic evaluation exists, but no private/heldout task corpus, Jevcal calibration or empirical per-definition gate.
- Semantic classification has Jev method/type support, but no reviewed Jev-align proposal/import loop.
- Analytics supports materialized/deterministic metrics, but no bounded SemanticPredicatePort for rare unmaterializable predicates.
- Entity resolution is existing and deterministic; no bounded hierarchical candidate selection for very large ambiguity.
- ResponsePlan/ResponseEnvelope and rendering exist; Jev-aware degraded evidence and shadow metadata need additive extension.
- No Jev feature flags, optional dependency manifests, isolated service health checks or production rollback playbook.
- No new DB tables are required for the core of this stage; evaluation/lock/review artifacts are versioned files. A telemetry migration is explicitly out of scope unless separately approved.

### Incorrect assumptions found during audit

The attached request correctly describes the intended completed first stage, but it overstates Jev readiness. The repository does not currently contain working integrations of jevcal, jev-align, System One Adapter, jevQL or jev-tree; it contains only a generic Jev seam and deterministic fallback. It is therefore incorrect to treat “optional Jev adapter” as “provider-ready runtime.”

## Reuse matrix and upstream decisions

| Upstream | Audited role | Exact strategy | Integration boundary | Why |
|---|---|---|---|---|
| jevcal | calibration, ECE/coverage/threshold analysis, lock/check CLI | DEV/EVAL_TOOL | scripts + versioned lock artifacts | It calibrates offline; runtime must consume lock, not run calibration |
| jev-align | uncertain-row acquisition, human review, GEPA proposal workflow, artifact capture | DEV/EVAL_TOOL | scripts/eval manifests/reviewed semantic artifacts | Review must remain explicit; no auto-accept and no public private registry |
| System One Adapter | official TypeSafe evaluator/baseline with usage/retry/latency | DEV/EVAL_TOOL | optional Python extra + evaluation script | Useful for comparison; not a production decision dependency |
| jevQL | two-pass bounded semantic predicate over selected rows, cache and budget enforcement | ISOLATED_OPTIONAL_RUNTIME, embedded-first | Python SDK embedded engine → private subprocess → shared service only when required; adapter to SemanticPredicatePort | The Python SDK can manage a private engine; a shared service is a fallback for platform/throughput/ownership constraints |
| jev-tree | bounded recursive candidate selection for large ambiguity | ISOLATED_OPTIONAL_RUNTIME | Node service/bridge to HierarchicalSelectionPort after deterministic narrowing | Only genuinely large unresolved candidate sets qualify; ordinary 20-program comparisons stay deterministic; Node runtime, call/depth/fanout caps and no invented leaf require isolation |
| awesome-jev | curated ecosystem index | PATTERN_ONLY | documentation/reference only | Unofficial catalog, not runtime code or API contract |

Upstream audit was performed against real repository source, tests, package metadata and current revisions:
- jevcal: ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f;
- jev-align: 3d997fc76593036655c28d4964de43b55f81fe2c;
- system-one-adapter-python: adffc2eab300a4fa3c0e92252d4ffd6ceaa53700;
- jevql: 274532af852e8edfb7715ec6dca1113e589cb191;
- jev-tree: 95bff63bd653fee4dc71f33f9431dce0f81e2ca3;
- awesome-jev: 04e65b59a936b2fed0d40eaec71a0a11e33bb422.

The upstream classifications and compatibility constraints are also documented in phase-01-foundation.md and docs/architecture/jev-ecosystem.md to be added during implementation. The exact jevQL deployment mode decision is made in T13 using a capability/benchmark gate; it is not assumed from the start.

## Target dependency graph

### Existing graph to preserve

official source → raw → normalize → canonical entities → repositories/PostgreSQL → semantic enrichment → ProgramProjection/ProgramMetric → MetricRegistry/QuerySpec → AnalyticsExecutor → AnalyticsResult → Conversation/Decision/Response → Web/OG/Telegram/MAX adapters

### Target graph after this plan

clean Stage 1 baseline commit
→ canonical + persisted semantic/projection data
→ deterministic resolver and Question Registry
→ DecisionModelPort:
deterministic default, optional typed Jev provider, shadow comparator, calibrated gate
→ typed QuerySpec
→ deterministic repositories/AnalyticsExecutor
→ optional SemanticPredicatePort backed by isolated jevQL only for explicitly registered rare predicates
→ optional HierarchicalSelectionPort backed by isolated jev-tree only after deterministic candidate narrowing
→ existing AnalyticsResult / admission fit / recommendation contracts
→ ResponsePolicyPort / ResponsePlan / ResponseEnvelope
→ Web, OG, Telegram, future MAX.

### Dependency direction guardrails

- modules/domain, modules/contracts and modules/services never import jevcal, jev-align, TypeSafe SDK, jevQL or jev-tree.
- Infrastructure adapters depend inward on typed ports; composition root is the only wiring authority.
- No provider receives SQL, table names, repository handles or user-controlled endpoint URLs.
- No model output directly executes SQL, changes canonical facts, selects arbitrary templates or becomes an explicit user fact.
- decision_analytics remains operational/user-action telemetry; it is not reused for catalog metrics.
- DecisionContext remains explicit user choice; QuerySession stores dialogue state and origins.

## Storage and migration strategy

1. No Alembic migration is planned for Jev runtime in the initial rollout.
2. Existing canonical, semantic, projection, provenance and source-gap tables remain source-backed system of record.
3. New control/evaluation artifacts are versioned files:
   backend/config/jev/question-definitions.v1.yaml,
   backend/config/jev/locks/decisions.v1.lock.json,
   backend/evals/jev/,
   backend/evals/jev-align/.
4. Runtime loads definitions/locks through validated typed loaders and fails closed if an artifact is missing/stale.
5. No provider payload, raw prompt, cache or private label is committed. jevQL cache is external, bounded and treated as sensitive.
6. Backfill uses existing semantic rebuild and projection rebuild scripts; only changed semantic items and affected programs are rebuilt.
7. If later operational telemetry needs durable storage, it requires a separate migration plan; do not overload decision_analytics or create an unbounded event table.
8. Rollback is artifact/config based: disable capability, restore previous semantic artifact/lock, invalidate affected optional cache, and continue deterministic service. Canonical data is untouched.

## Shared contracts and ports

- Existing: DecisionModelPort, DecisionPolicyPort, SemanticClassifierPort, QuerySpec, AnalyticsResult, ResponsePlan, ResponseEnvelope, QueryFrame, QuerySession.
- Additive vendor-neutral contracts: DecisionDefinition, QuestionRegistryPort, JevRequestEnvelope, JevResponseEnvelope, JevFailure, SemanticPredicatePort, HierarchicalSelectionPort, shadow comparison result and calibration lock metadata.
- Question Registry is the source of truth for instructions, criteria, definition version, input/output schema and calibration identity. Tool-specific settings remain in tool-owned files under backend/evals/jev, backend/evals/jev-align and the jev-tree/jevQL deployment manifests.
- Runtime adapter inputs are bounded, typed and allow-listed.
- All response values include source/model/artifact identity, coverage/status and fallback reason where applicable.
- AI-derived semantic values preserve method, confidence, definition version, classifier version, review status and provenance.

## Feature flags and production gates

All flags default false:

JEV_ENABLED, JEV_SHADOW_ENABLED, JEV_CALIBRATION_ENABLED, JEV_ALIGN_CAPTURE_ENABLED, JEVQL_ENABLED, JEV_TREE_ENABLED, and evaluation-only SYSTEM_ONE_ENABLED.

Production decision enablement additionally requires:

- valid immutable decision definition;
- valid Jevcal lock for the exact definition/model/dataset hash;
- heldout quality thresholds met empirically;
- provider ownership, secret rotation and rate limits;
- isolated service health for jevQL/jev-tree when used;
- shadow agreement/quality evidence;
- benchmark and rollback evidence;
- security/license/package checks green.

Until these gates are satisfied, “architecture/evaluation ready” is the correct state and Jev remains disabled.

## Phase Index

0. [Phase 00: Stage 1 baseline](phase-00-baseline.md) — Task T00
1. [Phase 01: Foundation](phase-01-foundation.md) — Tasks T01–T03
2. [Phase 02: Evaluation baseline](phase-02-evaluation-baseline.md) — Tasks T04–T05
3. [Phase 03: Jevcal calibration](phase-03-jevcal-calibration.md) — Tasks T06–T08
4. [Phase 04: Jev-align semantic loop](phase-04-jev-align-semantic-loop.md) — Tasks T09–T11
5. [Phase 05: jevQL isolated runtime](phase-05-jevql-isolated-semantic-runtime.md) — Tasks T12–T14
6. [Phase 06: jev-tree resolution](phase-06-jev-tree-hierarchical-resolution.md) — Tasks T15–T17
7. [Phase 07: Runtime wiring](phase-07-runtime-wiring-observability.md) — Tasks T18–T21
8. [Phase 08: Vertical slices](phase-08-vertical-slices-and-performance.md) — Tasks T22–T24
9. [Phase 09: Rollout and handoff](phase-09-rollout-documentation-and-gates.md) — Tasks T25–T26

## Tasks

### Phase 00 — Stage 1 baseline

- [ ] T00 — Зафиксировать чистый Stage 1 baseline и подготовить branch для Stage 2

### Phase 01 — Foundation

- [x] T01 — Зафиксировать baseline и архитектурные инварианты
- [x] T02 — Ввести shared DecisionDefinition и Question Registry
- [x] T03 — Уточнить typed integration boundary и response envelope

### Phase 02 — Evaluation baseline

- [x] T04 — Изолировать official System One Adapter
- [x] T05 — Создать canonical decision corpus и replay protocol

### Phase 03 — Jevcal

- [x] T06 — Export typed decision data to Jevcal
- [x] T07 — Generate and validate calibration lock
- [x] T08 — Add CI calibration gates

### Phase 04 — Jev-align

- [x] T09 — Export uncertain semantic items
- [x] T10 — Integrate review/export/import workflow
- [x] T11 — Add reviewed artifact compatibility

### Phase 05 — jevQL

- [ ] T12 — Define SemanticPredicatePort
- [ ] T13 — Add isolated jevQL adapter
- [ ] T14 — Connect predicate evidence to analytics

### Phase 06 — jev-tree

- [ ] T15 — Define hierarchical selection port
- [ ] T16 — Add isolated jev-tree adapter
- [ ] T17 — Integrate hierarchical resolution into QueryFrame

### Phase 07 — Runtime wiring

- [ ] T18 — Add settings and capability flags
- [ ] T19 — Wire Jev and shadow policy
- [ ] T20 — Add safe observability
- [ ] T21 — Lock dependency packaging

### Phase 08 — Vertical slices

- [ ] T22 — Complete analytics/admission slices
- [ ] T23 — Verify ResponsePlan and adapters
- [ ] T24 — Benchmark PostgreSQL and budgets

### Phase 09 — Handoff

- [ ] T25 — Security review and architecture enforcement
- [ ] T26 — Documentation and final gates

## Commit checkpoints

- C0 after T00: clean Stage 1 baseline and Stage 2 branch.
- C1 after T01–T05: contracts, registry, baseline corpus.
- C2 after T06–T08: Jevcal export, lock schema, CI gate.
- C3 after T09–T11: reviewed semantic artifact workflow.
- C4 after T12–T14: embedded-first jevQL seam/evidence.
- C5 after T15–T17: bounded jev-tree seam/resolution.
- C6 after T18–T21: disabled-by-default runtime wiring, production client and packaging.
- C7 after T22–T24: vertical scenarios and benchmark evidence.
- C8 after T25–T26: final docs/security/release gate.

Each checkpoint must be a normal reviewable commit on the clean Stage 2 branch created by T00. Do not reset, force-push, rewrite published history or commit pre-existing unrelated changes. The original dirty feature/university-admin-control branch remains preserved.

## Major risks and mitigations

| Risk | Mitigation |
|---|---|
| Jev provider/SDK drift | Optional pinned adapter, contract fixtures, startup health/version checks |
| Missing labels make calibration meaningless | Heldout corpus is a hard gate; no invented thresholds |
| Model output becomes SQL/UI/business logic | Typed allow-listed ports and architecture tests |
| Semantic AI value is treated as source fact | Separate provenance/method/review status and explicit precedence |
| jevQL/jev-tree process leakage or SSRF | Allow-listed endpoints, bounded payloads, isolated runtime, redaction |
| External runtime unavailable | Deterministic result/fallback with explicit status and source |
| Performance regression | Materialized metrics first, bounded external calls, EXPLAIN/query-count benchmarks |
| Dirty worktree contaminates commits | Stage only plan/expected paths; inspect staged name list before each commit |
| CI secrets/network dependency | Offline deterministic fixtures; protected manual/scheduled provider evaluation |
| Windows/Linux/Node mismatch | Isolated service manifests and explicit capability-unavailable state |
| Mixed Stage 1/Stage 2 baseline | Mandatory T00 clean commit/branch gate before any Stage 2 task |
| Unnecessary jevQL service complexity | Embedded SDK/private subprocess first; service only after measured technical decision |
| No production Jev client | T19 requires official TypeSafe SDK or approved TypeSafe-compatible endpoint adapter |

## Blocking open questions

These do not block the staged plan files, but they block live production enablement and must be resolved before C8 rollout approval:

1. Which TypeSafe/Jev provider, model, endpoint owner and secret-management environment will serve production requests?
2. If embedded jevQL/private subprocess is rejected by the capability benchmark, where will the shared jevQL service run and who owns its health/SLO/patching? Node jev-tree still requires an isolated runtime when enabled.
3. Who owns labels/review decisions for semantic features and next-action/metric/presentation corpus?
4. Which empirical acceptance thresholds are approved for each decision definition? The plan intentionally does not invent a universal confidence threshold.
5. Are any analytics predicates required that cannot be materialized from current canonical/projection data? If not, keep jevQL disabled.

If answers are unavailable, implement and verify through C7 with deterministic/shadow tooling only, then hand off explicitly as production Jev disabled.

## Definition of done

The stage is complete only when:

- all existing flows and CI remain green with optional integrations disabled;
- Question Registry and typed envelopes are the single operation source;
- System One, jevcal and jev-align are reproducible evaluation/review tools only;
- jevQL is an embedded-first, bounded, disabled-by-default optional runtime with private subprocess/shared-service fallback only when justified; jev-tree is isolated, bounded and disabled by default;
- Jev decisions are calibrated, shadow-evaluated and fail closed;
- semantic features remain versioned and provenance-backed;
- analytics remains deterministic/source-backed and does not execute model-generated SQL;
- response rendering remains channel-neutral;
- docs, security checks, benchmarks and rollback evidence are complete;
- unresolved provider/runtime/labels/threshold questions are recorded and prevent false production-readiness claims.

## Plan artifacts

- index.md — manifest, original request, architecture baseline, task checklist and gates.
- phase-00-baseline.md
- phase-01-foundation.md
- phase-02-evaluation-baseline.md
- phase-03-jevcal-calibration.md
- phase-04-jev-align-semantic-loop.md
- phase-05-jevql-isolated-semantic-runtime.md
- phase-06-jev-tree-hierarchical-resolution.md
- phase-07-runtime-wiring-observability.md
- phase-08-vertical-slices-and-performance.md
- phase-09-rollout-documentation-and-gates.md

## Next step

STOP after planning. Run implementation only through the approved plan, one checkpoint at a time, preserving the deterministic path and the production-disabled Jev gate until the open questions and evidence requirements are satisfied.
