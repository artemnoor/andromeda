<!-- aif:plan-mode:ultra -->
# План реализации Ultra: source-backed knowledge об образовательных правилах Andromeda

Mode: ultra
Plan branch: feature/andromeda-education-policy-knowledge (planning checkout remains based on feature/semantic-catalog-analytics-baseline; carry only the allowlisted planning artifacts to implementation; do not execute implementation here)
Implementation baseline: feature/jev-ecosystem-stage-2 @ 1f5777c892c2daf2f6f11a405bc19268b7dc0c88 (reconciled 2026-09-25)
Created: 2026-09-25

## Original Request

Используй максимально глубокий режим планирования. Перед составлением плана обязательно используй доступные тебе skills для best practices, architecture, backend/data modeling, PostgreSQL, testing/evaluation и AI/Jev integration, если такие skills доступны. Не ограничивайся поверхностным просмотром README.

КРИТИЧЕСКОЕ ОГРАНИЧЕНИЕ

СЕЙЧАС НЕЛЬЗЯ РЕАЛИЗОВЫВАТЬ ЗАДАЧУ.

На этом этапе ты должен:

1. максимально глубоко исследовать текущий репозиторий и текущую ветку;
2. восстановить фактическую архитектуру;
3. определить, какие существующие части нужно переиспользовать;
4. выявить архитектурные пробелы;
5. спроектировать целевую архитектуру;
6. составить максимально подробный phased implementation plan;
7. остановиться.

НЕ ПИШИ production-код.
НЕ СОЗДАВАЙ migrations реализации.
НЕ МЕНЯЙ runtime behavior.
НЕ РЕФАКТОРИ существующий код.
НЕ НАЧИНАЙ реализацию отдельных фаз.

Разрешены только research/plan artifacts, которые предусмотрены $aif-plan ultra.

Если AI Factory автоматически создаёт planning branch, она должна происходить от текущего состояния рабочей ветки. Не rebase, не reset, не переписывай историю.

⸻

1. BASELINE

Текущая система — Andromeda V2.

В качестве фактического baseline изучи текущую checkout-ветку. На remote основной актуальной веткой на момент постановки задачи является:

feature/jev-ecosystem-stage-2

Но сначала самостоятельно проверь:

* текущую branch;
* HEAD;
* status;
* историю последних commits;
* отличие от main;
* незакоммиченные изменения;
* актуальность remote.

Локальное текущее состояние репозитория имеет приоритет над предположениями из этого задания.

Обязательно изучи как минимум:

* AGENTS.md
* .ai-factory/config.yaml
* .ai-factory/DESCRIPTION.md
* .ai-factory/RULES.md
* существующие планы AI Factory;
* README.md
* ROADMAP.md
* docs/architecture.md
* docs/product-principles.md
* docs/architecture/query-flow.md
* docs/architecture/integration-seams.md
* docs/architecture/universal-analytics.md
* docs/semantic-analytics.md
* admissions/admission-benefits docs;
* ingestion architecture;
* database models и migrations;
* composition root;
* API;
* current OpenAPI;
* relevant architecture/integration/e2e tests.

Особенно внимательно исследуй существующие модули:

* conversation
* semantic
* entity_resolution
* analytics
* admissions
* admission_fit
* admission_benefits
* decision
* comparison
* recommendations
* programs
* curricula
* ingestion;
* infrastructure repositories;
* Jev/jevcal/jev-align/jevQL/jev-tree integration.

Не проектируй новую систему до того, как поймёшь уже существующую.

В плане обязательно должно быть явно указано:

что уже существует и переиспользуется;
что расширяется;
что действительно требует нового module/contract/table;
что вообще создавать не нужно.

⸻

2. ГЛАВНЫЙ АРХИТЕКТУРНЫЙ ПРИНЦИП

Andromeda должна ОСТАТЬСЯ modular monolith.

Не предлагай сейчас:

* отдельный Knowledge Core service;
* отдельный Data Staging service;
* отдельный Ingestion Platform deployment;
* Kafka;
* отдельные БД для каждого bounded context;
* distributed transactions;
* service discovery;
* CQRS ради CQRS;
* набор микросервисов.

Целевая схема сейчас:

ONE REPOSITORY
ONE BACKEND
ONE POSTGRESQL
+ строгие module boundaries
+ typed contracts
+ ports
+ repositories
+ composition
+ возможность вынести отдельный module в сервис позже

Мы хотим получить преимущества будущего Knowledge Core / Data Staging, но пока физически внутри текущей Andromeda.

Принцип:

logical boundaries first
physical boundaries later

Любой новый модуль должен следовать существующему Andromeda pattern:

```
modules/<module>/
    domain/
    contracts/
    services/
    repository/
```

Subject modules не должны знать про FastAPI, ORM, конкретный Jev SDK или university-specific parser.

⸻

3. ЦЕЛЬ

Нужно превратить текущую Andromeda из системы, которая в основном знает каталог, admissions, curricula, comparisons и отдельные admission-benefit rules, в полноценную source-backed систему знаний об образовании и поступлении.

Она должна понимать не только:

«Какие ЕГЭ нужны?»

или:

«Дает ли эта олимпиада БВИ?»

но и, например:

«Правда ли, что со следующего года вводят четвёртый ЕГЭ?»

«Это уже принято или пока только обсуждают?»

«Я видел новость, что за четвёртый ЕГЭ будут давать дополнительные баллы. Это правда?»

«С какого года это начинает действовать?»

«Я поступаю в 2027 году. Это меня касается?»

«Я поступаю в 2028 году. Что изменится для меня?»

«Это федеральное правило или только правило конкретного вуза?»

«Есть ли у Бауманки исключение?»

«Применяется ли это ко всем направлениям или только к части?»

«Меняет ли это мои шансы на поступление?»

«Влияет ли это на БВИ?»

«Что будет с олимпиадами?»

«Это касается 100 баллов за олимпиаду?»

«Изменились ли индивидуальные достижения?»

«Новость уже вступила в силу или пока нет?»

«Это слух, проект, официальный документ или действующая норма?»

«Что конкретно изменилось по сравнению с прошлой версией правил?»

«Мне вообще нужно что-то делать сейчас?»

Ответ должен строиться не как свободная генерация LLM, а на структурированной knowledge/rule модели.

⸻

4. PALANTIR-LIKE МОДЕЛЬ

Нужно спроектировать для Andromeda модель, концептуально похожую на Palantir Ontology:

real-world objects
+ facts
+ relations
+ policies/rules
+ provenance
+ temporal state
+ events/changes
+ dependency graph
+ impact analysis

Но НЕ надо слепо копировать Palantir и НЕ надо вводить graph database только потому, что здесь есть граф.

Сначала исследуй, можно ли естественно реализовать всё необходимое поверх PostgreSQL и существующих repositories.

Ожидаемые концепты, которые необходимо исследовать и при необходимости спроектировать:

Object / Entity
Fact
Relation
Claim
Rule / Policy
RuleCandidate
Change / Event
Source
Evidence
Scope
Exception
Override
Validity
Version
Dependency
Impact

Названия могут быть другими, если существующая терминология Andromeda лучше.

Главное — семантика и границы.

⸻

5. ФАКТ ≠ УТВЕРЖДЕНИЕ ≠ ПРАВИЛО ≠ НОВОСТЬ

Это критически важно.

Не создавай одну универсальную таблицу facts, куда будет складываться абсолютно всё.

Нужно явно разделить хотя бы концептуально:

Source

Откуда получена информация.

Например:

* нормативный документ;
* официальный приказ;
* официальный сайт министерства;
* официальный сайт университета;
* правила приёма;
* приложение к правилам;
* официальный пресс-релиз;
* новость вуза;
* официальный Telegram/VK;
* СМИ;
* сторонний сайт;
* социальные сети;
* пользовательский материал.

Claim

Что конкретно утверждает источник.

Один источник может содержать несколько claims.

Несколько источников могут подтверждать один claim.

Claims могут:

* подтверждать друг друга;
* противоречить друг другу;
* уточнять;
* относиться к разным периодам;
* относиться к разным вузам.

Rule / Policy

Нормализованное правило, которое реально можно применить deterministic engine.

News / Change Event

Событие во времени:

* опубликован проект;
* опубликован приказ;
* закон принят;
* правило вступило в силу;
* вуз изменил правила;
* вышло разъяснение;
* появилась новая редакция;
* старое правило отменено.

Hypothesis / Rumor

Информация, которая пока не является достаточным основанием для canonical rule.

Нужно спроектировать lifecycle от появления сигнала до подтверждённого правила.

⸻

6. НЕ СМЕШИВАТЬ TRUST И POLICY STATUS

Это один из основных архитектурных invariants.

Нельзя использовать одно поле status, которое одновременно означает и доверие к источнику, и юридическое/регуляторное состояние правила.

Например:

официальная новость Минобрнауки

может совершенно официально сообщать:

«предлагается ввести...»

Источник официальный, но правило ещё НЕ действует.

И наоборот, сторонняя статья может корректно пересказывать уже действующий приказ.

Поэтому необходимо отдельно смоделировать:

Source / evidence reliability

например:

primary_official
official_secondary
trusted_secondary
unverified_secondary
community
unknown

Не обязательно именно такими enum — сначала спроектируй.

И отдельно:

Policy lifecycle

Нужно продумать состояния уровня:

rumor
hypothesis
announced
proposal
draft
under_review
adopted
published
effective
superseded
repealed
withdrawn
rejected
unknown

Не копируй этот список буквально, если можно сделать лучше.

Главное — возможность корректно различать:

об этом говорят

это официально предложили

опубликован проект

решение принято

документ опубликован

правило уже действует

правило начнёт действовать позже

правило отменено

правило заменено новым

⸻

7. TEMPORAL MODEL

Andromeda должна понимать время не как одно поле date.

Нужно спроектировать полноценную temporal model.

Минимально рассмотреть:

observed_at
captured_at
published_at
announced_at
adopted_at
effective_from
effective_to
valid_from
valid_to

И обязательно решить, где нужны две временные оси:

valid time

Когда факт/правило действительно в реальном мире.

system/knowledge time

Когда Andromeda узнала об этом и когда эта версия была сохранена.

Нужно рассмотреть bi-temporal approach.

Пример:

15 декабря 2027 года мы обнаружили документ, опубликованный 1 декабря, который вводит правило с 1 сентября 2028 года.

Andromeda должна понимать одновременно:

published_at = 2027-12-01
observed_at = 2027-12-15
effective_from = 2028-09-01

И не должна применять правило к поступающему в кампанию 2027 года.

⸻

8. ADMISSION CYCLE / COHORT AWARENESS

Особенно важно не путать календарный год с приёмной кампанией.

Нужно определить, как система хранит и вычисляет:

admission_year
academic_year
effective_date
application_period
enrollment_period

Если правило вступает в силу в 2028 году, необходимо определить, относится ли оно к:

* поступлению летом 2028;
* учебному году 2028/29;
* результатам олимпиад определённого года;
* ЕГЭ определённого года;
* уже полученным достижениям.

Необходимо спроектировать deterministic applicability resolver.

⸻

9. SCOPE

Любой rule должен иметь явный scope.

Нужно поддержать правила разных уровней:

federal
ministry
university
campus
faculty
department
education_level
direction
program
admission_route
competition_type
applicant_category
olympiad
olympiad_profile
subject

Не обязательно хранить scope ровно таким набором колонок.

Нужно выбрать extensible модель.

Критически важно избежать создания отдельной схемы под каждый новый тип правила.

⸻

10. GENERAL RULE → EXCEPTION → OVERRIDE

Одна из главных целей новой модели — нормальная работа исключений.

Пример:

Федеральное правило:
для поступления требуется X.
↓ exception
МГТУ:
для определённой категории применяется Y.
↓ narrower override
конкретная программа:
применяется Z.

Нужно спроектировать понятную precedence model.

Рассмотреть:

* authority;
* specificity;
* explicit exception;
* override;
* supersedes;
* valid period;
* admission year;
* conflict.

Нельзя решать precedence через случайный порядок SQL rows.

Должен существовать deterministic Effective Rule Resolver.

⸻

11. RULES AS DATA

Мы хотим добавлять новые правила преимущественно как данные, а не как новый Python if.

Например концептуально:

```
IF
    fourth_exam.score >= 90
THEN
    admission.competitive_score += 30
SCOPE
    ...
EFFECTIVE
    admission_year >= 2028
STATUS
    effective
SOURCE
    ...
```

Конкретный DSL спроектируй сам.

Он должен быть:

* versioned;
* typed;
* bounded;
* auditable;
* testable;
* safe;
* machine-evaluable;
* human-readable;
* extensible;
* без arbitrary code execution.

Нужно определить:

* conditions;
* effects;
* predicates;
* scopes;
* exceptions;
* priorities;
* validity;
* dependencies;
* evidence;
* conflict handling.

Не проектируй огромный универсальный programming language.

⸻

12. СВЯЗЬ С ТЕКУЩИМ admission_benefits

Очень внимательно исследуй существующий:

modules/admission_benefits

Там уже существуют важные идеи:

* source-backed AdmissionBenefitRule;
* validity;
* scope;
* BVI;
* 100 points;
* Olympiad identity/profile;
* individual achievements;
* confirmation;
* provenance;
* ACTIVE/STALE/REVIEW_REQUIRED/CONFLICT/UNRESOLVED;
* deterministic evaluator.

НЕ СОЗДАВАЙ параллельную вторую admission-benefit систему.

Нужно определить, как общая Rule/Knowledge architecture:

* переиспользует эти сущности;
* обобщает общие механизмы;
* не ломает существующие contracts;
* не создаёт два competing rule engines.

В плане отдельно покажи migration/evolution path.

⸻

13. ОЛИМПИАДЫ И ЛЬГОТЫ

Knowledge model должна быть связана с:

* БВИ;
* 100 баллов;
* ВсОШ;
* перечневыми олимпиадами;
* профилями олимпиад;
* уровнями;
* подтверждением ЕГЭ;
* сроком действия результата;
* программами/направлениями;
* индивидуальными достижениями;
* специальными правами;
* квотами;
* альтернативными admission routes.

Пример:

Если появляется новый приказ, изменяющий соответствие олимпиады направлениям подготовки, система должна уметь определить:

Change
↓
affected OlympiadProfile
↓
affected AdmissionBenefitRule
↓
affected Direction/Program
↓
affected ApplicantDecision

И объяснить это пользователю.

⸻

14. INDIVIDUAL ACHIEVEMENTS

Текущая модель уже знает individual achievements.

Нужно включить их в общий policy/change system.

Например:

«С 2028 года вуз перестаёт давать 5 баллов за X.»

Система должна:

1. найти прежнее rule;
2. найти новое source-backed правило;
3. понять validity;
4. определить supersedes;
5. пересчитать applicability;
6. показать affected users/programs;
7. при необходимости показать change history.

⸻

15. DEPENDENCY GRAPH

Нужно добавить логический dependency graph.

Не обязательно graph DB.

Нужны typed relations, позволяющие отвечать:

что от чего зависит?

и:

что изменится, если изменился этот факт/rule?

Примеры relations:

APPLIES_TO
EXCEPTION_TO
OVERRIDES
SUPERSEDES
AMENDS
IMPLEMENTS
CLARIFIES
CONFLICTS_WITH
DERIVED_FROM
SUPPORTED_BY
AFFECTS
REQUIRES
RESOLVES_TO

Не принимай этот список как готовую схему — нормализуй его.

Нужно определить:

* typed edge contracts;
* допустимые node/edge combinations;
* cardinality;
* provenance;
* validity;
* review state;
* cycle detection;
* traversal limits.

⸻

16. IMPACT ANALYSIS

Это одна из ключевых возможностей.

После появления изменения система должна уметь построить:

source/change
↓
claim
↓
rule
↓
affected objects
↓
affected derived metrics/decisions
↓
affected applicant contexts

Например:

новый приказ
→ изменяет подтверждение БВИ
→ касается олимпиады X
→ направления A/B/C
→ университет BMSTU
→ поступление 2028

И на вопрос пользователя:

«Мне нужно из-за этого что-то менять?»

дать не эмоциональную оценку, а actionability.

Например:

Для поступления в 2027:
не влияет.
Для поступления в 2028:
может влиять на ваш маршрут БВИ.
Что изменилось:
...
Что пока неизвестно:
...
Что нужно отслеживать:
...

Продумай отдельную модель Impact, Applicability и/или DecisionImpact.

⸻

17. DIFF

Нужен first-class semantic diff.

Не просто:

document A != document B

а:

старое правило:
minimum = 75
новое правило:
minimum = 80

или:

раньше:
scope = all programs
теперь:
scope = programs A/B/C

или:

benefit:
BVI → 100 points

Нужно спроектировать:

* source diff;
* structured candidate diff;
* canonical rule diff;
* effective-policy diff;
* impact diff.

Diff должен быть доступен до подтверждения изменения в review UI.

⸻

18. STAGING ВНУТРИ ANDROMEDA

Ранее концептуально рассматривался отдельный Data Staging service.

Теперь НЕ создавай отдельный сервис.

Но сами механизмы нужны внутри modular monolith.

Целевой поток:

```
source
→ capture
→ raw snapshot
→ deterministic parse
→ normalized data
→ candidate objects/facts/claims/relations/rules
→ deterministic validation
→ bounded Jev semantic resolution where needed
→ review
→ diff
→ impact preview
→ approved canonical/effective data
```

Cold start должен поддерживаться.

Пустая БД не является ошибкой.

Можно создавать:

* independent objects;
* facts без relations;
* candidates со needs_review.

Нельзя заставлять AI придумывать relation только потому, что relation отсутствует.

⸻

19. HUMAN REVIEW

AI не должен самостоятельно превращать неоднозначную информацию в canonical truth.

Нужна review workflow.

Исследуй существующий semantic review lifecycle и переиспользуй его где возможно.

Review item должен показывать как минимум:

candidate
source/evidence
why extracted
proposed canonical target
proposed relations
confidence
current canonical value
diff
impact preview
conflicts
effective date
affected scopes

Reviewer должен иметь возможность:

approve
reject
edit
merge
resolve identity
mark unresolved
mark duplicate

Все действия должны быть auditable.

⸻

20. MANUAL / ADMIN DATA

Университет или администратор должен иметь возможность исправить или добавить информацию.

Но manual data не должна становиться безымянной истиной.

Нужны:

* actor/source;
* reason;
* timestamps;
* provenance;
* revision;
* audit;
* optional expiration;
* scope.

Рассмотри связь с существующим university_admin.

⸻

21. РОЛЬ JEV

Очень важно сохранить правильную границу.

Концептуально:

Jev understands / classifies / resolves / links
Rule Engine decides
Database stores canonical truth
LLM verbalizes

Jev НЕ должен:

* придумывать source facts;
* писать canonical data напрямую;
* выполнять SQL;
* вычислять юридическое действие правила;
* принимать eligibility decision вместо deterministic evaluator;
* генерировать unrestricted IDs;
* выбирать relation за пределами ontology/allowed candidates;
* обходить calibration gates.

Используй Jev только там, где deterministic logic недостаточна, например:

* intent resolution;
* entity resolution;
* bounded candidate selection;
* semantic classification;
* relation candidate classification;
* claim classification;
* ambiguous source wording;
* source → ontology alignment.

Предпочтительный pattern:

deterministic narrowing
→ bounded candidate set
→ Jev
→ typed candidate
→ validation
→ review if needed

Учитывай существующие:

* Question Registry;
* TypeSafe transport;
* calibration locks;
* deterministic fallback;
* shadow mode;
* jevcal;
* jev-align;
* jevQL;
* jev-tree.

Не создавай второй Jev abstraction без серьёзного основания.

⸻

22. EVALUATION JEV

Если план предполагает новые Jev operations для:

* claim classification;
* relation resolution;
* rule-type recognition;
* source-status interpretation;
* ontology mapping;

то для каждой такой операции план должен включать отдельный evaluation lifecycle.

Нельзя использовать Jev prediction как ground truth.

Нужно предусмотреть:

* deterministic synthetic/golden corpus;
* ground truth до model run;
* independently authored labels;
* bounded candidate sets;
* adversarial cases;
* ambiguity;
* typo/paraphrase strata;
* false-positive measurement;
* hallucinated relation measurement;
* false MATCH measurement;
* unresolved recall;
* regression corpus.

Для relationship/entity matching предусмотреть не менее 500 deterministic golden synthetic cases, если этот operation будет использоваться для production canonical/staging decisions.

Обязательно отдельно измерять:

hallucinated relations
false MATCH
false NO_MATCH
incorrect override
incorrect scope resolution
incorrect temporal applicability

Fail closed.

⸻

23. RULE ENGINE НЕ РАВЕН JEV

Rule engine должен быть deterministic.

Например:

Applicant
+ Program
+ AdmissionCycle
+ EffectivePolicySet
→ deterministic result

Jev может помочь определить, какое правило/объект имелся в виду, но финальная applicability должна определяться typed deterministic logic.

⸻

24. CONFLICT MODEL

Нужно спроектировать работу с конфликтами.

Возможные случаи:

* два официальных источника противоречат;
* новый документ отменяет старый;
* федеральное правило и вузовское правило различаются;
* вуз опубликовал новость до официальных правил;
* одна страница обновилась, PDF — нет;
* source publication date отличается от effective date;
* одна и та же норма описана разными словами.

Нельзя просто брать «самую новую строку».

Нужно определить:

conflict detection
authority
specificity
supersession
temporal applicability
manual review
safe user-facing state

При unresolved conflict система должна честно сказать, что однозначного ответа пока нет.

⸻

25. SOURCE HIERARCHY

Спроектируй hierarchy/trust model источников.

Но источник и policy status, как уже сказано, НЕ смешивать.

Рассмотреть как минимум:

primary normative/legal document
official ministry/regulator publication
official university admission rules
official university order
official appendix
official university announcement/news
official university social channel
trusted secondary media
secondary aggregator
community/social source
user supplied source
unknown

Определи:

* какие источники могут автоматически создавать candidate;
* какие требуют mandatory review;
* какие могут только создавать hypothesis/signal;
* какие никогда не могут напрямую создавать effective rule.

⸻

26. PROVENANCE

Существующий provenance — сильная часть Andromeda.

Новая архитектура не должна его обойти.

Для любого значимого ответа должна существовать цепочка:

answer
→ effective rule / fact
→ claim
→ evidence
→ source snapshot
→ source URL/document locator

Где возможно — page/table/row/section.

Нужно определить field-level provenance там, где один объект собран из нескольких источников.

⸻

27. ANSWER ENGINE

Нужно расширить текущий conversation / /assistant/query, но не создавать параллельного второго assistant backend.

Исследуй существующий:

natural language
→ QuerySession
→ parser / resolution
→ DecisionPolicy
→ typed request
→ execution
→ result/evidence
→ ResponsePolicy
→ ResponseEnvelope

И предложи, как добавить knowledge/policy/change questions в тот же flow.

Возможно, потребуются новые intent types — но не плодить десятки intents без необходимости.

Система должна уметь вести multi-turn диалог.

Пример:

USER:
Говорят, что в 2028 введут четвёртый ЕГЭ.
SYSTEM:
Найдено изменение ...
Статус ...
Дата ...
USER:
А меня это касается?
SYSTEM:
На какой год вы поступаете?
USER:
На 2027.
SYSTEM:
Нет, для кампании 2027 это правило не применяется...

QuerySession должен сохранять typed context, а не только строковую историю.

⸻

28. THREE RESPONSE MODES

Учти ранее выбранную концепцию трёх режимов ответа.

Конкретную реализацию уточни по существующей архитектуре, но смысл должен сохраниться:

Mode 1 — trusted deterministic/Jev path

Когда Andromeda может построить ответ целиком из structured source-backed данных и deterministic logic.

LLM не нужен.

Mode 2 — source-backed result + LLM verbalization

Andromeda сначала получает полностью structured result:

facts
rules
status
effective dates
impact
exceptions
evidence
uncertainties

и только потом LLM, например DeepSeek Flash через provider-neutral adapter, превращает его в естественный человеческий ответ.

LLM не имеет права добавлять новые факты.

Mode 3 — general LLM fallback

Если вопрос выходит за coverage Andromeda.

Ответ должен быть явно отделён от verified knowledge path и иметь состояние вроде:

unverified / outside Andromeda knowledge coverage

Такой ответ:

* не записывается как canonical fact;
* не становится rule;
* не влияет на deterministic decisions;
* не выдаётся как проверенная информация Andromeda.

Спроектируй routing между режимами.

Не делай LLM обязательным dependency для core.

⸻

29. USER-FACING STATUS

Пользователь не должен видеть внутреннюю кашу enum.

Нужно спроектировать понятное представление примерно такого уровня:

Статус:
пока обсуждается
Что известно:
...
Источник:
...
Опубликовано:
...
Вступает в силу:
...
Кого касается:
...
Вас касается:
...
Что изменится:
...
Исключения:
...
Что ещё неизвестно:
...
Последняя проверка:
...

Не обязательно именно такой UI, но ResponseEnvelope должен позволять его построить.

⸻

30. «СТОИТ ЛИ ВОЛНОВАТЬСЯ»

Не делай эмоциональный classifier worry=true/false.

Нужно формализовать это как relevance/actionability.

Например:

NOT_APPLICABLE
FUTURE_ONLY
INFORMATIONAL
ACTION_RECOMMENDED
ACTION_REQUIRED
UNCERTAIN
BLOCKED_BY_MISSING_DATA

Подбери лучшую модель.

Она должна учитывать:

* admission year;
* target university;
* programs/directions;
* exams;
* applicant achievements;
* olympiads;
* admission route;
* effective dates;
* exceptions.

⸻

31. WHAT-IF

Knowledge/Rules architecture должна позволять безопасный what-if.

Например:

«А если это правило всё-таки примут?»

или оператору:

«Что изменится, если candidate rule активировать с 2028?»

What-if не должен менять canonical state.

Нужен deterministic sandbox evaluation:

current effective policy
vs
current + candidate rule

с:

diff
impact
affected entities
affected applicants/decision contexts where safe

В плане опиши архитектуру такого preview.

⸻

32. CURRENT / FUTURE / HISTORICAL QUESTIONS

Система должна одинаково корректно отвечать:

Что действует сейчас?
Что будет действовать в 2028?
Что действовало в 2025?
Когда это правило появилось?
Чем правила 2027 отличаются от 2028?
Почему система вчера отвечала иначе?
Какой источник был известен Andromeda на дату X?

Последние вопросы особенно важны для bi-temporal/audit model.

⸻

33. NEWS / SIGNAL INGESTION

Не превращай Andromeda в обычный news aggregator.

Новости интересны только если они могут:

* создать Claim;
* сообщить Change;
* подтвердить/опровергнуть Hypothesis;
* привести к RuleCandidate;
* изменить status;
* повлиять на existing knowledge;
* быть релевантными applicant decision.

Нужно определить pipeline:

source discovery
→ snapshot
→ candidate claims
→ entity linking
→ change classification
→ evidence linking
→ review
→ knowledge update
→ impact

Спроектируй deduplication одинаковой новости в нескольких источниках.

⸻

34. CHANGE DETECTION

При повторном ingestion одного источника система должна понимать:

unchanged
changed
removed
new

Для structured documents — желательно field/semantic changes.

Нужно учитывать:

* source hash;
* document version;
* canonical identity;
* semantic diff;
* supersession;
* stale facts/rules.

⸻

35. EXISTING SEMANTIC LAYER

Не смешивай curriculum semantic features:

mathematics
programming
AI
physics
...

с новой policy ontology.

Исследуй, какие primitives можно переиспользовать:

* versioning;
* classifier status;
* review workflow;
* confidence;
* source hash;
* rebuild;
* derived data.

Но оставь разные bounded contexts, если они семантически разные.

⸻

36. CANONICAL DATA VS DERIVED DATA

Определи строго:

canonical/source-backed

Что является фактом/правилом источника.

derived

Например:

* applicability;
* impact;
* user relevance;
* conflict interpretation;
* current effective policy;
* recommendation;
* summary.

Derived result должен быть rebuildable.

Не сохраняй generated LLM prose как источник истины.

⸻

37. INCREMENTAL RECOMPUTATION

Изменение одного rule не должно требовать полностью перестраивать всю Andromeda.

Используй dependency information для определения affected projections.

Нужно спроектировать:

changed fact/rule
→ dirty dependencies
→ targeted recomputation

Но не вводи сложную distributed event architecture без необходимости.

⸻

38. API

Нужно определить, какие API действительно нужны.

Предпочтительно расширять существующие public seams.

Рассмотреть typed APIs уровня:

knowledge lookup
policy/effective rules
change history
impact preview
review queue
assistant query
sources/evidence

Но НЕ создавай endpoint на каждую database table.

API должен соответствовать use cases.

OpenAPI должен оставаться source of generated frontend types.

⸻

39. MAX / TELEGRAM / WEB

Business logic должна оставаться channel-neutral.

MAX, Telegram и Web:

→ /assistant/query
→ ResponseEnvelope

и НЕ должны:

* самостоятельно понимать правила;
* выполнять Jev logic;
* пересчитывать impact;
* читать DB;
* определять status новости.

MAX остаётся transport + notification/quick-action layer.

Mini App может использовать более глубокие сценарии просмотра:

* comparison;
* shortlist;
* sources;
* changes;
* impact;
* history.

Но core knowledge logic одна.

⸻

40. DATA EDITING / REVIEW UX

В плане продумай operator/admin workflow.

Пример:

```
New source detected
        ↓
3 claims extracted
        ↓
1 existing fact unchanged
1 candidate relation
1 candidate rule change
        ↓
review screen
        ↓
semantic diff
impact preview
sources
confidence
        ↓
approve/reject/edit
```

Нужна возможность легко исправлять систему без изменения Python-кода там, где это data change.

⸻

41. NO FABRICATION

Hard invariant:

no evidence
≠ false
≠ zero
≠ no

Использовать состояния:

unknown
unavailable
insufficient_data
unresolved
review_required
conflict

где необходимо.

Особенно это касается:

* олимпиад;
* исключений;
* дат;
* квот;
* scope;
* applicability.

⸻

42. MIGRATION STRATEGY

Нельзя переписывать Andromeda с нуля.

Составь evolutionary migration.

Нужно сохранить существующие working vertical slices:

* catalog;
* curricula;
* semantic analytics;
* comparison;
* admissions;
* admission fit;
* admission benefits;
* proftest;
* recommendations;
* DecisionContext;
* assistant;
* Web;
* Telegram;
* future MAX.

Определи порядок внедрения новой модели таким образом, чтобы после каждой крупной фазы существующий продукт оставался runnable.

⸻

43. DATABASE

Изучи текущие SQLAlchemy models/Alembic migrations и предложи нормальную PostgreSQL model.

Избегай двух крайностей:

1. таблица на каждый imaginable rule;
2. один giant JSON blob без constraints.

Нужно найти баланс typed relational model + controlled extensibility.

Отдельно рассмотреть:

* canonical IDs;
* uniqueness;
* indexes;
* temporal indexes;
* versioning;
* provenance;
* JSONB только там, где оправдан;
* immutable source snapshot;
* audit;
* idempotency;
* conflict groups;
* review state.

⸻

44. PERFORMANCE

План должен учитывать потенциальный рост:

* десятки вузов;
* тысячи программ;
* десятки тысяч документов;
* сотни тысяч facts/relations;
* history за несколько лет.

Но не оптимизировать под миллиарды объектов заранее.

Определи, какие индексы/materialized projections понадобятся и что можно отложить.

⸻

45. SECURITY

Особенно для source ingestion и admin:

* никаких arbitrary URLs без policy;
* SSRF protections;
* bounded downloads;
* content size limits;
* MIME validation;
* PDF safety;
* no secrets in logs;
* no arbitrary code execution из Rule DSL;
* authorization для review/admin;
* immutable audit trail.

⸻

46. TEST STRATEGY

План должен включать несколько уровней тестов.

Unit

Rule evaluation, precedence, temporal applicability, status transitions.

Contract

Pydantic/public contracts, serialization.

Repository

PostgreSQL persistence и constraints.

Architecture

Module dependency boundaries.

Integration

Source → staging → canonical.

Vertical

official document
→ parsed claim
→ approved rule
→ assistant question
→ deterministic result
→ provenance

Temporal regression

Например:

2027 applicant
2028 applicant
same rule
different applicability

Conflict regression

Два источника → unresolved conflict.

Exception regression

Federal rule → university exception.

Jev evaluation

Отдельные bounded corpora и calibration gates.

E2E

FastAPI/OpenAPI → channel-neutral ResponseEnvelope.

⸻

47. ОБЯЗАТЕЛЬНЫЕ GOLDEN SCENARIOS

План должен включить минимум следующие будущие acceptance scenarios.

Scenario A — rumor

Источник сообщает:

«Возможно, с 2028 года введут новое правило.»

Ожидание:

* не становится effective rule;
* status/uncertainty отражены;
* пользователь видит, что это пока не принято.

Scenario B — official proposal

Официальный источник публикует проект.

Ожидание:

* source официальный;
* policy status = proposal/draft;
* система не применяет его как действующее правило.

Scenario C — adopted future rule

Правило принято сейчас, действует с кампании 2028.

Пользователь поступает в 2027.

Ожидание:

verified
future rule
not applicable to your admission cycle

Scenario D — future applicant

То же правило.

Пользователь поступает в 2028.

Ожидание:

applicable
impact shown
affected exams/score/routes shown

Scenario E — university exception

Общее правило действует, но у BMSTU есть source-backed exception.

Ожидание:

effective resolver выбирает правильное правило для BMSTU.

Scenario F — direction exception

Исключение только для части направлений.

Scenario G — Olympiad change

Новый документ меняет БВИ или 100-point applicability.

Ожидание:

affected Olympiad/Profile/Program graph + deterministic evaluation.

Scenario H — individual achievement change

Баллы за достижение изменяются с нового admission year.

Scenario I — supersession

Новый документ полностью заменяет старый.

Scenario J — conflict

Два authoritative sources расходятся.

Ожидание:

никакого выдуманного разрешения;
conflict/review_required.

Scenario K — source disappears

Ранее опубликованный источник недоступен, но имеется immutable snapshot.

Scenario L — same news duplicated

Одна новость опубликована несколькими источниками.

Ожидание:

один logical change/claim cluster, несколько evidence sources.

Scenario M — no evidence

Пользователь спрашивает об исключении, которого система не знает.

Ожидание:

insufficient_data, а не «исключений нет».

Scenario N — what-if

Candidate rule ещё не действует.

Оператор спрашивает impact preview.

Canonical state не меняется.

⸻

48. ПЛАН ДОЛЖЕН БЫТЬ ПРИЗЕМЛЁН К ТЕКУЩЕМУ CODEBASE

Не пиши абстрактный architecture essay.

Для каждой phase укажи:

* objective;
* existing code reused;
* exact modules;
* exact likely files/directories;
* contracts to add/change;
* repository ports;
* infrastructure models;
* migrations;
* composition wiring;
* API changes;
* tests;
* docs;
* dependencies;
* rollback;
* acceptance criteria;
* risks;
* what explicitly remains out of scope.

Если точный файл ещё нельзя определить без реализации, укажи наиболее вероятное место и почему.

⸻

49. ПРЕДВАРИТЕЛЬНАЯ ЖЕЛАЕМАЯ ДЕКОМПОЗИЦИЯ

Не считай это обязательной финальной схемой.

Исследуй, достаточно ли текущих modules или имеет смысл добавить логические bounded contexts вроде:

modules/knowledge
modules/policy
modules/change_intelligence
modules/review

или меньший набор.

Не создавай четыре модуля только потому, что они перечислены здесь.

Предпочитай минимальное количество bounded contexts с ясной ownership model.

Особенно проверь возможность переиспользования:

semantic review
admission_benefits
conversation
entity_resolution
shared provenance
ingestion
admin_ops
university_admin

⸻

50. OWNERSHIP MATRIX

В план обязательно включи ownership matrix:

concept
→ owning module
→ canonical/derived
→ writer
→ readers
→ persistence owner

Минимум для:

* Source;
* SourceSnapshot;
* Claim;
* Fact;
* Relation;
* Rule;
* RuleCandidate;
* ChangeEvent;
* EffectivePolicy;
* ReviewItem;
* Impact;
* User relevance;
* QuerySession;
* ResponseEnvelope.

Не допускай ситуации, когда два модуля являются владельцами одной canonical сущности.

⸻

51. WRITE PATH / READ PATH

Нарисуй целевой write path:

source
→ ingestion
→ candidate
→ validation/Jev
→ review
→ canonical
→ derived refresh

и read path:

user question
→ conversation
→ entity/context resolution
→ knowledge/policy lookup
→ effective-rule resolution
→ impact/applicability
→ ResponseEnvelope
→ optional LLM verbalization

И отдельно what-if path.

⸻

52. НЕ ПОТЕРЯТЬ ТЕКУЩУЮ ФИЛОСОФИЮ ANDROMEDA

Сохраняются текущие hard principles:

* source-backed;
* user makes final decision;
* no fabricated missing data;
* canonical IDs;
* provenance;
* explicit vs derived state;
* channel-neutral backend;
* deterministic fallback;
* bounded AI;
* university adapter model;
* modular monolith;
* typed APIs;
* testability;
* fail closed.

Новая система не должна разрушить эти принципы.

⸻

53. ОСОБЕННО ПРОВЕРЬ СУЩЕСТВУЮЩИЕ ПРОБЛЕМЫ

Во время research проверь и зафиксируй:

1. насколько текущий conversation parser способен поддерживать новые knowledge/change questions;
2. нужно ли расширять ConversationIntent;
3. не становится ли QuerySession перегруженным;
4. можно ли использовать текущий DecisionModelPort;
5. подходит ли semantic review lifecycle;
6. достаточно ли существующего provenance;
7. какие admission-benefit abstractions можно обобщить;
8. не возникнет ли второй rule engine;
9. где сейчас жёстко зашита логика, которая должна стать rule-as-data;
10. как избежать универсального god-module knowledge;
11. какие current migrations/contracts будут сложнее всего эволюционировать;
12. как сохранить backwards compatibility API.

⸻

54. НЕ ПЕРЕСТРАИВАТЬ ТО, ЧТО УЖЕ РАБОТАЕТ

Если текущий компонент уже решает задачу хорошо, переиспользуй его.

Например, не создавай:

KnowledgeEntityResolver

если existing entity_resolution можно корректно расширить.

Не создавай новый:

KnowledgeJevClient

если есть DecisionModelPort/Jev adapters.

Не создавай новый provenance stack.

Не создавай вторую conversation system.

Не создавай второй admission-benefit evaluator.

⸻

55. РЕЗУЛЬТАТ ПЛАНИРОВАНИЯ

После исследования создай $aif-plan ultra bundle.

В index.md должны быть:

1. Executive summary.
2. Current-state architecture assessment.
3. Concrete gaps between current Andromeda and target model.
4. Architectural decision summary.
5. Target module map.
6. Ownership matrix.
7. Canonical vs derived model.
8. Source/Claim/Rule model.
9. Temporal model.
10. Rule DSL / Effective Rule Resolver.
11. Exceptions/override/precedence model.
12. Dependency/impact model.
13. Staging/review model.
14. Jev boundaries.
15. Three response modes.
16. Assistant/query integration.
17. Database evolution strategy.
18. API evolution strategy.
19. Testing/evaluation strategy.
20. Migration/backwards compatibility strategy.
21. Rollout/feature flags.
22. Risks.
23. Explicitly rejected alternatives.
24. Detailed phases and dependency graph.

Каждая отдельная phase должна находиться в отдельном phase-файле согласно $aif-plan ultra.

⸻

56. PHASE DESIGN

Не навязываю количество фаз, но план примерно должен покрывать:

Phase 0
Deep architecture audit + invariants
Phase 1
Canonical knowledge vocabulary and ownership
Phase 2
Temporal + provenance foundations
Phase 3
Claim/change/staging lifecycle
Phase 4
Rule model + Rule DSL
Phase 5
Effective Rule Resolver + exceptions/overrides
Phase 6
Dependency graph + semantic diff + impact
Phase 7
Review/admin workflow
Phase 8
Jev bounded semantic linking/classification
Phase 9
Admission Benefits / Olympiad / Individual Achievement integration
Phase 10
Conversation/assistant knowledge queries
Phase 11
Three response modes + optional verbalization
Phase 12
What-if / historical / future policy queries
Phase 13
Evaluation, regression, performance, security
Phase 14
Migration/backfill/rollout/docs

Но после исследования измени разбиение, если существует более правильный порядок.

⸻

57. ACCEPTANCE DEFINITION

Финальный implementation plan должен привести к системе, в которой реальный end-to-end flow выглядит так:

```
официальный документ / новость / другой источник
              ↓
        SourceSnapshot
              ↓
      structured extraction
              ↓
      Claim / ChangeCandidate
              ↓
 deterministic normalization
              ↓
 bounded Jev resolution where needed
              ↓
 deterministic validation
              ↓
             review
              ↓
        semantic diff
              ↓
        impact preview
              ↓
          canonical data
              ↓
    effective policy resolution
              ↓
       dependency refresh
              ↓
      пользовательский вопрос
              ↓
        QuerySession/context
              ↓
 applicability + impact + exceptions
              ↓
       source-backed result
              ↓
 ResponseEnvelope + evidence
              ↓
 optional constrained LLM verbalization
```

И при этом:

Jev understands and links.
Rule Engine decides.
Database stores canonical truth.
LLM only verbalizes verified results when used.

⸻

58. ФИНАЛЬНЫЕ ЗАПРЕТЫ

На этой итерации:

DO NOT IMPLEMENT.

DO NOT CREATE RUNTIME CODE.

DO NOT CREATE DATABASE MIGRATIONS IMPLEMENTATION.

DO NOT MODIFY PRODUCTION API.

DO NOT ENABLE NEW JEV OPERATIONS.

DO NOT CHANGE CURRENT CALIBRATION LOCKS.

DO NOT REMOVE EXISTING MODULES.

DO NOT TURN ANDROMEDA INTO MICROSERVICES.

DO NOT USE AN LLM AS A SOURCE OF TRUTH.

DO NOT ALLOW AI TO WRITE CANONICAL RELATIONS/RULES WITHOUT VALIDATION/REVIEW.

DO NOT LABEL A PROPOSAL AS AN EFFECTIVE RULE.

DO NOT TREAT ABSENCE OF DATA AS A NEGATIVE FACT.

Сейчас нужен только максимально качественный, codebase-grounded $aif-plan ultra.

После завершения остановись и выдай:

1. путь к созданному plan bundle;
2. краткое описание целевой архитектуры;
3. список предлагаемых modules;
4. список существующих modules, которые переиспользуются;
5. основные database/model изменения;
6. phases в порядке реализации;
7. главные риски;
8. вопросы/решения, которые действительно требуют человеческого architectural decision перед implementation.

Никакую фазу реализации после этого не начинай.

## Stage 2 Reconciliation (2026-09-25)

This bundle was originally researched from `feature/semantic-catalog-analytics-baseline` at `efc1699772400f71c8cef0004b1ef8ca4f6cb1b8`. Reconciliation verified that `origin/feature/jev-ecosystem-stage-2` and its local remote-tracking ref both point to `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`; this is the clean implementation baseline for every future phase. It contains the old baseline plus 29 Stage 2 commits. The Stage 2 tree contains neither this plan bundle nor its linked research bundle; `$aif-implement` can accept the copied bundle through an explicit `@.ai-factory/plans/feature-andromeda-education-policy-knowledge/index.md` path. The current planning checkout remains on the old commit and has a dirty worktree (122 status entries, including 63 tracked paths at reconciliation start); preserve it and never use it for implementation. Task 1 creates one plan-only commit from an exact artifact allowlist, then cherry-picks only that commit onto a separate clean worktree based directly on the exact Stage 2 SHA. Do not merge the old planning branch or rebase, reset, stash, clean or switch this planning checkout.

Stage 2 is now baseline code, not a proposed merge. It adds the production Jev integration seams and gates, enriches admission benefits and assistant contracts, and advances the Alembic head to `0038_admission_offering_scope_and_exam_choices`. New migrations must continue additively from `0038` after checking deployed database heads; do not recreate existing source snapshots, benefit coverage, benefit scope, campus or exam-choice data. The `alembic_version` sizing safeguard is already in `backend/alembic/env.py`.

Reconciliation guardrails:

- Preserve both new subject modules (`knowledge`, `policy`) and the existing single owners. `policy` selects approved domain revisions and explains applicability; it never calculates BVI, 100-point Olympiad benefits, confirmation, benefit validity, or individual-achievement eligibility/points. Those remain delegated to `admission_benefits` and its current deterministic evaluator/calculator. Other domain calculations likewise stay with their existing owner.
- Define `policy` ownership of the minimal append-only `PolicyApprovalEvent` contract. The same transaction that first persists a `PolicyRuleRevision`/`RuleCandidate` must append initial `PENDING_SUBMITTED`, bound to that immutable revision hash. Later authorized human approve/reject/withdraw actions append events through a typed policy port; current state is derived from history. The effective resolver v1 reads only an exact approved revision. `knowledge` owns ReviewItem/workflow, and its full operator UI remains later.
- Add bounded source discovery over the existing ingestion adapter/capture and immutable snapshot path. The versioned source registry is allow-listed; poll observations, health, last-success, hash, retry/backoff and discovery gaps are explicit. Discovery creates snapshots/candidates only. Stage 2's `source-health` workflow is scheduled read-only health probing, not source discovery or production ingestion scheduling; no broad crawl/news aggregator is introduced.
- Make typed `ResolutionTrace` mandatory in every effective-rule resolution. It records considered/rejected revisions and reasons, time/cycle/scope, supersession, exceptions/overrides, conflicts, selected rules and provenance references; impact, review, debugging, ResponseEnvelope and regression tests consume this structure.
- Reuse Stage 2 Jev runtime/composition, Question Registry, TypeSafe transport, existing domain ports, calibration/capability gates and evaluation tooling. New Jev operations require separate versioned definitions, independently authored evaluation evidence and their own calibration artifacts; do not modify existing locks or enable any Jev flag as part of this plan.
- Before implementation, carry only the ultra plan directory plus the five exact linked files in `.ai-factory/research/universal-educational-analytics/` (`INDEX.md`, `RESEARCH.md`, `C4-CONTAINER.md`, `C4-CONTEXT.md`, `DEPENDENCY-GRAPH.md`) in the plan-only commit. Cherry-pick that commit onto Stage 2, verify its parent and complete changed-path allowlist, and invoke `$aif-implement @.ai-factory/plans/feature-andromeda-education-policy-knowledge/index.md`; do not merge the old runtime branch.
- Task 1 is a release gate before all runtime work: run `python scripts/andromeda.py full`, explicit Alembic heads/history, `git diff --check`, and verify required CI checks for the exact Stage 2 code SHA. Record code SHA, plan-only commit SHA and commit-bound green CI evidence; any red/missing required check blocks implementation.

The existing plan remains a modular-monolith evolution: no separate Knowledge Core/Staging deployment, graph database, Kafka, second assistant, provenance stack, entity resolver, Jev client or benefit evaluator.

## Settings

- Language: Russian artifacts; keep established technical terms
- Testing: yes for future implementation; no test/build is run in this planning turn
- Logging: standard
- Docs: yes, alongside each shipped phase

## Правила логирования для всех заданий

- Писать структурированные логи из application service/repository adapter владельца: operation ID, canonical/candidate ID, revision, outcome и duration.
- INFO: успешные переходы capture/staging/review/approval/refresh. WARN: неизвестные source/scope/cycle, conflict, stale projection, traversal truncation, deterministic fallback или unresolved Jev. ERROR: ошибка parser/persistence/refresh, из-за которой операция не выполнена.
- Решения review создают immutable audit events с actor, target, revision и reason; обычные логи не заменяют audit.
- Не логировать credentials, cookies, raw source bodies, полные user query/profile или LLM/Jev payload. Редактировать query string у source URL; при необходимости использовать prefix hash.

## Roadmap Linkage

Milestone: "none"
Rationale: В корневом ROADMAP.md нет milestone для source-backed policy/knowledge, а настроенный путь .ai-factory/ROADMAP.md отсутствует. После принятия плана linkage можно предложить через aif-roadmap; этот план не меняет roadmap.

## Research Context

Source: `.ai-factory/research/universal-educational-analytics/RESEARCH.md` (Active Summary, Updated: 2026-09-21 18:20, SHA256: 93a7e7dbdc8ba9cf5501fff671ae139a53857d85dd7696a1a74914bec75587af)

Active Summary
Topic: Универсальный educational analytics и decision interface для Andromeda
Goal: Подготовить существующий modular monolith к typed аналитическим запросам, произвольному channel-neutral диалогу и будущим Jev/MAX adapters без зависимости домена от транспорта, LLM или Jev.
Scope: Архитектурная эволюция поверх текущих ingestion, canonical University/Direction/Program/Curriculum/Discipline, admissions, Admission Fit, recommendations, comparison и decision modules. Включает отдельные semantic, analytics, entity-resolution, conversation и presentation boundaries, persistent analytical projections, QuerySpec, policy ports, ResponseEnvelope, typed API и тонкую миграцию Telegram/Web seams.
Stakeholders: Пользователь Andromeda; backend/API; ingestion operators; Telegram и будущий MAX/Web transports; будущие Jev policy/classifier adapters; PostgreSQL/SQLAlchemy/Alembic operations.
Constraints: Сохранить PostgreSQL, SQLAlchemy, Alembic, canonical IDs/contracts, current admissions/admission-fit/provenance/source-gap semantics и backwards compatibility. Оставить существующую 22-area taxonomy отдельно от non-exclusive semantic features. Не подключать Jev/LLM как runtime dependency; не принимать raw SQL от внешней модели; не превращать missing в zero; не создавать microservices, Kafka, Redis или AssistantService-монолит без отдельного решения. Все schema changes только Alembic. Subject modules не импортируют ORM/FastAPI/ingestion; university-specific behavior остаётся в ingestion adapters.
Requirements: П persist semantic defaults и curriculum-item overrides с confidence, classification method, classifier/taxonomy versions, source hash/run ID и provenance. Вынести ProgramFingerprint/FingerprintBuilder в общий analytics domain с compatibility imports. Строить и хранить rebuildable program projections после ingestion. Ввести versioned extensible metric registry, explicit workload basis и statuses AVAILABLE/PARTIAL/INSUFFICIENT_DATA/UNAVAILABLE. Реализовать bounded typed QuerySpec и AnalyticsResult/evidence без raw SQL. Добавить backend entity resolvers с explicit ambiguity. Хранить generic QuerySession с slot filling для analytics и admission flows. Создать DecisionPolicyPort и ResponsePolicyPort с deterministic implementations; подготовить Jev seams. Возвращать channel-neutral ResponseEnvelope, добавить /analytics/query и /assistant/query, оставить Telegram/Web thin adapters и PDF report path из готового result.
Decisions: Canonical data остаётся source of truth; semantic data и projections являются versioned derived data и могут быть полностью rebuilt. Первичная semantic классификация — RuleBasedSemanticClassifier через SemanticClassifierPort. Поля semantic values не суммируются до единицы и не заменяют DisciplineAreaWeight. Canonical Discipline с глобальным normalized identity не переписывается сразу: curriculum-item semantic override является обязательным уточнением для одинаковых имён в разных планах; identity split остаётся отдельным compatibility decision. Persistent projections обновляются post-ingestion для affected programs и отдельно отмечают projection failure, не откатывая canonical transaction. Admission Fit остаётся отдельным существующим engine; conversation собирает applicant slots и передаёт typed batch request, а analytics filter использует allow-listed adapter. Существующие comparison/recommendation/decision contracts сохраняются, а ProgramFingerprint становится compatibility alias на analytics projection. Telegram сначала получает общий assistant HTTP contract; resolver/session/response selection постепенно выносятся из Telegram, без второго domain engine.
Risks: Нынешний ProftestCatalogService пересчитывает fingerprints из всего каталога в runtime, а recommendations и decision напрямую используют proftest contract; перенос ownership может сломать compatibility и architecture allowlist. Comparison независимо повторяет hours→credits и area aggregation. Текущая дисциплина глобально уникальна по normalized_name и curriculum item не имеет собственной provenance/semantic таблицы. Post-ingestion projection failure может дать canonical/analytics version skew. QuerySpec может стать обходом безопасности, если validation не будет registry-driven и bounded. Telegram сейчас кэширует полный catalog, хранит только cookie session и сам выбирает text/PNG; миграция должна сохранить callback/session security и OG HMAC boundary. 5,000 программ и 100,000 curriculum items требуют batch repositories/indexes и запрета N+1.
Open questions: Нужен ли в следующем этапе отдельный identity model для одинаковых дисциплин по university/program context, или curriculum-item override достаточно для первой projection version; должен ли QuerySession храниться по anonymous ProfileScope или отдельным owner key; какой production scheduler/runner будет вызывать rebuild после ingestion; будет ли PDF HTML renderer размещён в backend presentation adapter или в Next report route; какие дополнительные semantic features и aliases должны пройти manual review до production rollout.
Success signals: Existing regression/architecture/OpenAPI tests remain green; a fixture ingestion creates semantic rows and persistent projections; one bounded SQL query answers metric comparison without rebuilding fingerprints; missing basis produces explicit insufficient status; evidence can traverse metric → item → semantic classification → canonical/source snapshot; unsupported metrics and ambiguous entities fail typed; deterministic scenarios A–H work without Jev; Telegram remains HTTP-only and can consume ResponseEnvelope; MAX can later reuse the same API without importing backend modules.
Next step: Зафиксировать evidence-backed execution plan по фазам с отдельными migration/projection rollout checkpoints и approval gate перед implementation.

## Резюме

Andromeda уже modular monolith с каталогом, admissions, curricula, deterministic admission fit, comparison, analytics, conversation и API. Добавить эволюционный путь source assertion → reviewed policy → deterministic applicability/impact → evidence-backed answer, сохранив существующие vertical slices.

Добавить только modules/knowledge и modules/policy. Knowledge владеет source identity/observations, claims/evidence, change candidates и review. Policy владеет typed rules, temporal applicability, precedence/resolution, dependencies и impact. Domain facts остаются у текущих owners; admission_benefits сохраняет единственный evaluator.

Один repository/backend/PostgreSQL/composition root. Relational typed data для ownership/evidence/time/scope/edges, bounded versioned JSONB только для AST/extraction payload. Без микросервисов, Kafka, graph DB или arbitrary code.

## Оценка текущей архитектуры

### Проверенный baseline

- Plan artifact branch remains `feature/andromeda-education-policy-knowledge` at the old source commit `efc1699772400f71c8cef0004b1ef8ca4f6cb1b8`; it is not an implementation target.
- Current verified implementation baseline is `origin/feature/jev-ecosystem-stage-2` at `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`, 29 commits / 294 changed paths beyond the old source. The remote and local tracking ref matched at reconciliation. Stage 2 does not contain this plan or the linked research bundle, so Task 1 transfers only those planning artifacts and `$aif-implement` is started with the explicit plan path.
- The planning checkout was dirty (122 status entries, 63 tracked paths) and is preserved. Future implementation starts in a new clean worktree directly from the Stage 2 SHA (or a separately reviewed descendant), never from this worktree.
- Clean Stage 2 Alembic head is `0038_admission_offering_scope_and_exam_choices`. Revisions 0036-0038 add benefit coverage, confirmation applicant category, campus scope and exam choice cardinality. `backend/alembic/env.py` already sizes Alembic version storage dynamically.
- Current `origin/main` is an ancestor of the reviewed Stage 2 baseline; there is no outstanding Stage 2 merge decision for this plan. Recheck remote advancement when implementation begins.

### Существующие модули для повторного использования

| Модуль | Текущая ответственность | Повторное использование и граница |
|---|---|---|
| ingestion | Existing adapters, RawSourceSnapshot/SourceSnapshotModel, IngestRun, content hash, idempotency/retry/heartbeat, source coverage/gaps | Reuse capture/parser/snapshot and runner seams; add bounded allowlist-driven poller, not another ingestion or snapshot service |
| admissions | Stage 2 AdmissionOffering, campus, exams/choice groups, quotas, passing scores, tuition, admission_year | Canonical owner; AdmissionCycle still not present and needs a typed admissions-owned contract |
| admission_fit | Deterministic applicant/program fit | Keep evaluator; provide typed effective inputs |
| admission_benefits | Stage 2 benefit rules/coverage, BVI/100, Olympiad/Profile, applicant confirmation category, validity, individual achievements, source provenance, eligibility and effective competitive-score evaluators | Sole calculator for all listed benefits/achievement semantics; policy selects exact approved domain revision and delegates calculation |
| semantic | Curriculum features, versioning, confidence, review, provenance/rebuild; Stage 2 hashed semantic proposal/review/publish lifecycle | Reuse freshness/hash/audit workflow invariants only; never reuse curriculum ontology, artifact storage or classifier as policy model |
| entity_resolution | Canonical IDs, alias/ambiguous outcomes, Stage 2 hierarchical resolution and optional bounded candidate selector | Extend existing services/ports; reuse `JevAdmissionCandidateSelector`; no KnowledgeEntityResolver |
| analytics | Allowlisted registry, typed query/result/evidence/gaps | Reuse contract patterns, not rule DSL |
| conversation | Stage 2 typed QuerySession/QueryFrame, explicit/inferred admission slots, resolution cache/evidence, assistant/parser/compiler, DecisionModelPort/DecisionPolicyPort | Add one nested policy context and broad knowledge intent; preserve Stage 2 session/API; no second assistant |
| presentation | Stage 2 ResponseEnvelope and current evidence/metadata, ResponsePolicyPort/Plan, templates | Add typed policy/relevance/ResolutionTrace explanation; maintain API/OpenAPI compatibility |
| decision/comparison/recommendations/programs/curricula | Existing owner vertical slices | Preserve contracts and consume through ports |
| university_admin/admin_ops | Membership, roles and access | Reuse authentication; add policy-specific capability |
| composition/API | AndromedaContainer, FastAPI, schemas, OpenAPI/generated frontend types | One composition root; API remains transport |
| Jev | Stage 2 wired optional runtime/composition, Question Registry, TypeSafe transport, calibration locks, `resolve_olympiad_profile`, jevcal/eval harness, jev-align, jevQL and jev-tree seams | Reuse existing typed ports and capability gates; add only separately versioned/evaluated knowledge operations; no second client/registry/calibration system |

### Текущий flow и разрывы

Current assistant: natural language → parser/entity resolution/session → DecisionPolicy → QuerySpec/admission request → execution → result/evidence → ResponsePolicy → ResponseEnvelope through /assistant/query. A second assistant backend is unnecessary.

Stage 2 now wires optional Jev behind typed policy/model ports and expands admission benefits, admission fit, entity resolution, QuerySession and generated OpenAPI. `JevAdmissionCandidateSelector` already handles bounded Olympiad-profile selection; Stage 2 benefits cover source coverage/category/campus/exam choice and effective competitive score. Missing: cross-university educational source registry/discovery observations; Claim/Change lifecycle; durable generic exact-revision approval ledger; policy selector/resolver/ResolutionTrace; cross-domain bitemporal/cycle applicability; semantic policy diff/dependency impact; history and policy operator workflow.

`SourceSnapshotModel` keyed by `content_sha256`, `IngestRunModel`, idempotency/retry metadata, and existing source attribution/provenance are reusable; reference them rather than create a snapshot/provenance stack. BMSTU's Stage 2 admission document catalog is an adapter-specific discovery example, not a cross-university source registry. The scheduled `source-health` workflow is read-only CI probing, not an education-policy poller or production scheduling seam.

## Разрывы между текущей Andromeda и целевым состоянием

1. No durable source identity/trust registry independent from legal state.
2. No shared Claim → ChangeCandidate/Event → approved Rule lifecycle.
3. No general bitemporal “what did Andromeda know then?” query.
4. admission_year exists but source-backed AdmissionCycle mapping does not; calendar/effective year cannot imply campaign.
5. No general typed scope/exception/override precedence across federal, university and program.
6. No bounded rule AST; must not duplicate benefits evaluator.
7. No typed dependency graph, semantic policy diff, impact preview or targeted refresh.
8. Semantic review is curriculum-specific; no legal reviewer/audit/admin flow.
9. Conversation lacks change/applicability/history intent and typed session context.
10. ResponseEnvelope lacks complete status/effectivity/scope/actionability/uncertainty.
11. Stage 2 Jev runtime is wired but only current registered/locked operations are available; there is no claim/relation/policy operation, and its existing corpora/locks do not calibrate those operations.
12. Pre-observation historical knowledge cannot be reconstructed reliably.

## Ключевые архитектурные решения

- Keep one modular monolith, current canonical owners and composition root.
- Add exactly modules/knowledge and modules/policy; no change_intelligence, review, second entity resolver or staging deployment.
- Claims represent what evidence asserts, not truth. Canonical facts remain in current admissions/benefits/program/catalog owner; no universal facts table.
- Source trust, human review and legal lifecycle are independent axes. Official publisher does not imply adopted/effective rule.
- Existing content-addressed snapshots remain immutable; add source identity and capture observations referencing them.
- Use bitemporal revisions: valid time separate from system/knowledge time; never fabricate legacy history.
- Add AdmissionCycle under admissions and fail closed without source-backed cohort mapping.
- Use a small typed/versioned bounded selector AST with registered applicability predicates and typed owner-rule references; no generic domain-calculation effects or arbitrary execution. Existing domain owners/evaluators perform the final domain calculation.
- The policy-owned append-only `PolicyApprovalEvent` exists from the first persisted `PolicyRuleRevision`/`RuleCandidate`: that creation transaction includes `PENDING_SUBMITTED` for the exact immutable revision hash; later approval/rejection/withdrawal is appended and never overwrites history. Resolver v1 accepts only an exact approved revision; an `ACTIVE` legacy row is not proof of approval.
- Resolver filters approval/lifecycle/time/cycle/scope, uses explicit reviewed exception/supersession and authority/specificity, returns conflict for incomparable policies, and always returns typed `ResolutionTrace` with considered/rejected/selected rules and evidence.
- Existing Stage 2 admission-benefit/competitive-score evaluator remains the sole calculator for BVI, 100 points, confirmation, benefit validity and individual-achievement eligibility/points; policy only selects/references its approved domain revision and delegates.
- Bounded source discovery uses a versioned allowlist registry in `knowledge` and current capture/snapshot adapters in `ingestion`; it records health/hash/last-success/retry/gaps and only creates observations/snapshots/candidates. The Stage 2 scheduled source-health job is read-only and is not reused as production polling.
- Use PostgreSQL typed relations and dependency refresh; no graph database.
- Human review is only canonicalization path. Jev can suggest bounded links/classification but cannot decide law or write truth.
- Extend the existing assistant/ResponseEnvelope seam; optional LLM verbalization and outside-coverage fallback cannot add verified facts.
- What-if is read-only deterministic overlay. Historic answers state where retained knowledge history begins.
- Additive migrations and independent rollout flags; rollback disables capabilities rather than deleting audit data.

## Целевая карта модулей

| Module | Status | Owner responsibility | Explicit boundary |
|---|---|---|---|
| modules/knowledge | New | Source registry/observations, claims/evidence, change candidates/events, review envelope and audit | Not all facts, effective policy or snapshot body |
| modules/policy | New | Policy revisions and bounded selectors, approval-gated domain rule refs, temporal applicability/precedence, mandatory ResolutionTrace, typed dependencies, impact/what-if | Not source fetch/evidence bytes or domain calculation |
| modules/admissions | Extend | AdmissionCycle and admission canonical records | No general review/candidate store |
| modules/admission_benefits | Existing domain owner + narrow selector port if required | Stage 2 BVI/100/olympiad/confirmation/validity/achievement/competitive-score rules and evaluators | No second calculator and no policy-owned eligibility result |
| modules/ingestion | Extend existing adapter layer | Registry-driven bounded discovery, poll/capture, per-source observations and university-specific parsing into candidates | No open crawl, arbitrary URL or direct canonical policy writes |
| modules/entity_resolution | Extend | Stage 2 canonical/hierarchical identity resolution and bounded candidate ports | No parallel resolver |
| modules/conversation | Extend | Existing parser/session/assistant flow | No rule evaluation or direct DB |
| modules/presentation | Extend | Typed response mapping and optional verbalizer port | No truth selection |
| infrastructure/database/repositories | Extend | SQLAlchemy/Alembic persistence adapters | No subject business logic |
| API and AndromedaContainer | Extend | Use-case transport/composition | No ORM/business/JeV policy logic |

New modules follow modules/<module>/{domain,contracts,services,repository}. Subject modules do not import FastAPI, SQLAlchemy, Jev SDK or university parsers. Typed contracts/ports connect modules; AndromedaContainer remains the only composition root.

## Матрица ownership

| Понятие | Владелец | Canonical / derived | Кто записывает | Кто читает | Владелец хранения |
|---|---|---|---|---|---|
| Source registry/identity/trust | knowledge | Canonical versioned issuer/allowlist/trust config | Authorized source steward/admin command | ingestion poller, review, policy, assistant | knowledge repository |
| SourceSnapshot | ingestion | Immutable capture | Existing fetch/capture | knowledge, review, domain provenance | Existing SourceSnapshotModel/blob |
| SourceObservation / health | knowledge logical observation; ingestion owns attempt runner | Canonical per-source result/hash/registry version/last-success reference; runner telemetry is operational | Ingestion poller through typed port | claims, review, history, operations | knowledge repository references existing IngestRun/SourceSnapshot; never copies raw bytes |
| Claim | knowledge | Assertion record, not truth | Parser candidate then reviewer | staging, policy, assistant | knowledge repository |
| Fact | Existing subject owner | Canonical source-backed field | Owner command after review | policy, analytics, assistant | admissions/benefits/catalog owner |
| Relation | knowledge for evidence; policy for policy edges; domain owner for domain edges | Typed edge family | Candidate then validation/review | impact, policy, review | One repository per edge family |
| Rule | policy for generic policy selector/reference; admission_benefits for AdmissionBenefitRule | Canonical approved selector revision plus owner-canonical domain rule | Authorized reviewer for policy ref; domain owner writes domain rule | resolver; owner evaluator, admission, assistant | policy for selector/ref; current domain owner for its rule |
| RuleCandidate | policy payload; knowledge workflow envelope | Noncanonical pending proposal with initial exact-hash audit event | Validated extractor/manual proposal; Jev may only suggest | preview/reviewer only; never Effective Rule Resolver until the exact revision is approved | policy candidate/revision repository plus knowledge workflow |
| PolicyApprovalEvent | policy | Canonical immutable lifecycle/audit event for an exact policy revision hash | Policy repository appends `PENDING_SUBMITTED`; authorized human reviewer command appends approve/reject/withdraw | approved-revision query, knowledge review, operations, trace | policy approval ledger |
| ChangeEvent | knowledge for source changes; policy for lifecycle milestones | Audited history | Ingestion candidate/review | history, resolver, assistant | Respective owner |
| EffectivePolicy | policy | Derived/rebuildable | Deterministic resolver | admission, impact, assistant | Computed or measured read projection |
| ResolutionTrace | policy | Derived deterministic explanation artifact per resolution | Effective Rule Resolver | impact, review, debugging, ResponseEnvelope explanation, regression tests | In-memory/read result by default; optional bounded trace artifact reference, never canonical rule truth |
| ReviewItem | knowledge | Canonical workflow/audit | Review command | ops UI, canonical adapters | knowledge repository |
| Impact | policy | Derived/rebuildable | Impact service/refresh | review, API, assistant | policy projection or on demand |
| User relevance | policy | Derived per explicit query | Applicability/impact | ResponseEnvelope | Not canonical profile state |
| QuerySession | conversation | Canonical typed session | Existing assistant command | assistant | Existing conversation persistence |
| ResponseEnvelope | presentation | Derived response | ResponsePolicy | API/Web/Telegram/MAX | Not canonical |

Rule, Relation and ChangeEvent are explicitly separated typed families above, not competing owners of one record. No module owns all facts.

## Canonical и derived данные

Canonical/source-backed: source registry/capture; source claims/evidence; reviewed facts in existing owners; approved policy revisions, typed relations and audit; source-backed AdmissionCycle mapping.

Derived/rebuildable: effective policy by context/time; applicability; conflict interpretation from current revisions; semantic/effective/impact diff; dependency dirty state; actionability; response assembly and any LLM prose. Store revision inputs to rebuild. Generated prose never becomes truth.

Missing evidence is not negative. Missing scope, date, exception, quota, olympiad identity or cycle mapping yields unknown/unavailable/insufficient/unresolved/review_required/conflict as appropriate.

## Модель Source, Claim и Rule

Source records issuer, jurisdiction, origin, type and separate reliability tier: primary normative/legal; official regulator/ministry; official university rule/order/appendix; official university announcement/social channel; trusted secondary; unverified aggregator/community; user-supplied; unknown. Trust changes are audited.

Claim is one source assertion with observation/snapshot, text span, typed proposition, parser version, extraction method and page/section/table/row locator where available. Claims may support, contradict or clarify one another. Similarity alone never merges canonical identities.

Policy lifecycle is independent of source reliability and approval: hypothesis/signal → announced/proposal/draft → adopted → published → effective or future-effective → amended/superseded/repealed; withdrawn/rejected are historical outcomes. Human approval is a third explicit axis bound to the exact immutable policy revision hash. Official is not adopted; adopted is not necessarily effective; neither implies human approval.

Primary/official allowlisted sources may create observations and candidates but none auto-activates. Trusted secondary can support a claim or create review candidate. Unverified/community/user sources create hypothesis only and cannot directly make effective rules. The versioned allowlist and reviewer identity/capability are human decisions. Discovery is bounded to registered host/path/feed/API adapters; no open crawl.

## Temporal model и AdmissionCycle

Valid/legal time records when a fact/rule applies. System/knowledge time records when Andromeda stored a revision. Keep published_at, announced_at, adopted_at, effective_from/to, valid_from/to, captured_at/observed_at and recorded_at distinct where known; null means unknown.

Publication 2027-12-01, capture 2027-12-15 and effective 2028-09-01 must be queryable independently. Immutable revisions or closed system-time intervals enable as-known-at queries.

AdmissionCycle is owned by admissions and includes admission_year, academic_year, application/enrollment periods and source evidence. Context may include exam/result/olympiad year and route. No implicit equality between effective calendar year and admission year; missing mapping blocks or marks uncertain. Historic answer claims only retained revision coverage.

## Rule DSL и Effective Rule Resolver

Versioned bounded selector AST: all/any/not; eq/one_of/gte/lte/exists predicates over registered applicability/context fields; typed `DomainRuleRef(owner, canonical_id, owner_revision)` selects a source-backed domain rule. There are no generic domain-calculation effects. In particular, `policy` never calculates BVI, 100-point benefits, confirmation, Olympiad validity, individual-achievement eligibility/points, or admission scoring; it selects/links the approved owner revision and invokes the current owner service/evaluator.

Initial bounds: depth 8, 64 nodes, 32 list entries, 512-character scalar/text. Unknown schema/field/operator/owner contract fails closed. No eval/exec, SQL, dynamic import, arbitrary functions, domain effect registry or executable strings. JSONB only for bounded selector/extraction payload; scope/time/status/evidence/revision/approval/owner refs stay relational.

Before persisted rule candidates exist, an append-only approval-decision ledger records actor/capability, verdict/reason/time and the exact revision hash. Resolver v1 repository accepts only a matching approved event. It filters approval/lifecycle/system as-of/valid-time/cycle, applies explicit reviewed supersession/amendment/authorized exception, compares legal authority/jurisdiction and typed scope specificity, and returns a unique maximal domain-rule set or conflict/blocked result. Source trust is not precedence; row order/latest time/`ACTIVE` are not approval.

Every resolution returns a versioned typed `ResolutionTrace`: ordered rules considered; each rejection stage/reason; temporal/cycle/scope outcome; supersession/exception/override relation and evidence refs; conflict group; final selected owner revisions and provenance refs. This is mandatory for successful, empty, conflict and blocked results, deterministic, bounded and free of applicant prose. Impact, review, debugging, ResponseEnvelope explanation and regression tests consume it.

## Scope, exceptions и overrides

Typed scope references cover federal, ministry/regulator, university, campus, faculty, department, education level, direction, program, route, competition, applicant category, olympiad/profile and subject. Common dimensions are relational, extensions registered, no table per rule kind. Missing scope is not “all”.

Precedence applies explicit source-backed amendments/authorized exceptions, then reviewed authority/jurisdiction and specificity across intersecting scope/time/cycle. A narrow exception only overrides its declared intersection. Bad target/cycle, precedence cycle or incomparable tie blocks with conflict.

## Dependencies, diff и impact

Knowledge evidence edges: SUPPORTED_BY, CONTRADICTS, CLARIFIES, DERIVED_FROM. Policy edges: APPLIES_TO, EXCEPTION_TO, OVERRIDES, SUPERSEDES, AMENDS, IMPLEMENTS, REQUIRES. AFFECTS is derived. Validate endpoint types/provenance/time and reject cycles; initial traversal cap is depth 8 / 1000 nodes with explicit truncation.

Semantic diff compares source bytes, parsed fields, claims, canonical fields, selector/owner references/scope/time/approval, effective rules by cycle and impact. Reviewer sees diff pre-approval. Source disappearance does not repeal policy; retain snapshot and require explicit event.

Impact chain: change → claim → canonical owner → rule/dependency → affected program/olympiad/achievement/admission context. Recompute reverse dependencies after canonical commit; failed refresh marks stale. Impact is rebuildable and never fan-outs to persistent per-user decisions. Actionability: NOT_APPLICABLE, FUTURE_ONLY, INFORMATIONAL, ACTION_RECOMMENDED, ACTION_REQUIRED, UNCERTAIN or BLOCKED_BY_MISSING_DATA.

## Staging и human review

Write path: versioned allowlisted source registry → scheduled/operator-triggered bounded poller in current ingestion layer → immutable Stage 2 SourceSnapshot/IngestRun → deterministic parse → claim/change candidates → bounded deterministic entity resolution → validation → optional registered/calibrated Stage 2 Jev suggestion. Only when Phase 04 first persists a `PolicyRuleRevision`/`RuleCandidate`, the same transaction appends its exact-hash `PENDING_SUBMITTED` audit event; later human approval appends a decision event. Only that approved exact revision can reach the resolver → review with evidence/diff/impact/ResolutionTrace → owner canonical write → derived refresh. Discovery and unapproved suggestions create observations/snapshots/candidates only. `source-health.yml` is read-only CI probing, not the production poller; use a bounded command through the selected operations/deployment scheduler, no extra service.

Cold start permits standalone objects/claims/change candidates in NEEDS_REVIEW; absence never creates a relation. The first persisted `RuleCandidate`/`PolicyRuleRevision` must be committed atomically with a policy-owned, append-only `PENDING_SUBMITTED` event keyed to its exact revision hash. Human approve/reject/withdraw actions append further events through a typed policy port; edits create a new revision and a new pending event. The resolver reads only an exact revision whose derived approval state is approved. Full later Knowledge review UI adds approve/reject/edit/merge/resolve identity/unresolved/duplicate commands and delegates policy approval to that port; every action is actor/time/reason/exact-hash audited. Revalidate candidate revision at approval. University staff submit in scope; central steward approves federal rules by default pending decision. Manual data includes actor/reason/source/scope/revision/time/provenance/optional expiry.

Reuse semantic review mechanics, not its curriculum ontology or data model. Knowledge owns workflow; no review module.

What-if path: explicit user/operator candidate reference → read current approved effective-policy set → run a separate deterministic sandbox preview that applies the candidate only as an in-memory hypothetical overlay → calculate baseline/overlay selection and owner-evaluator result → build semantic/impact diff plus trace explanations → return a prominently hypothetical ResponseEnvelope → discard the overlay. The sandbox does not call/bypass the production Effective Rule Resolver approval gate, create approval, write canonical state, mutate applicant context or notify users.

## Граница Jev и evaluation

Jev may classify claim type, select existing entities from a deterministic bounded candidate set, classify allowed relation type or align wording to bounded ontology. It cannot invent facts/IDs, write canonical data, choose legal lifecycle/effectiveness, execute SQL, decide eligibility or calculate policy.

Flow: deterministic narrowing → existing Stage 2 module-owned typed port/DecisionModelPort as appropriate → shared QuestionRegistry + TypeSafeJevTransport/operation lock → typed candidate ID/enum → schema/allowlist validation → deterministic domain validation → exact-revision human approval. Reuse `resolve_olympiad_profile`/`JevAdmissionCandidateSelector` where applicable; do not duplicate them. No `KnowledgeJevClient`, question registry, provider stack or candidate resolver.

New operations for claims/relations/policy labels are separate versioned definitions, have independently authored corpora/ground truth and operation-specific calibration artifacts, and remain off/shadow until gates pass. Existing Jevcal locks/corpus are not mutated or treated as ground truth for a different operation. jev-align stays proposal/review tooling; jevQL stays bounded analytics; jev-tree stays large candidate selection. Jev flags are unchanged/disabled by this plan.

Each future production operation requires independently authored labels before model runs, bounded candidates, held-out synthetic/golden data and ambiguity/typo/paraphrase/adversarial strata. Entity/relation matching requires at least 500 deterministic golden synthetic cases. Measure hallucinated relations, false MATCH/NO_MATCH, unresolved recall, wrong relation, incorrect override/scope/temporal applicability. Calibration lock and fail-closed gates keep regression shadow/off.

## Assistant и три response modes

Read path: channel → existing /assistant/query → QuerySession/entity/context resolution → typed knowledge/policy lookup → applicability/resolver/impact → structured result/evidence/uncertainty → ResponseEnvelope → optional verbalization.

Add one KNOWLEDGE_POLICY_QUERY intent and nested versioned PolicyQueryContext for admission cycle/year, target, route, valid/system as-of, what-if candidate and input provenance. Keep current slot filling; no second assistant or growing flat session slots.

1. Trusted deterministic mode: fully source-backed typed result and deterministic render. Jev may help bounded query understanding only.
2. Optional source-backed verbalization: complete verified result is built first. Provider-neutral ResponseVerbalizerPort may order/select approved evidence references; server renders all factual values/status/dates. Invalid output/timeout falls back deterministically; model cannot add facts.
3. Outside-coverage general fallback: visibly unverified/outside Andromeda coverage, never stored as canonical data and never used in decisions. No provider means typed unsupported.

ResponseEnvelope exposes mapped user-facing status, trust/lifecycle separately, facts, publication/effective dates, scope/cycle, exceptions, applicability/actionability, impact delta, evidence URL/locator, unknowns, last check and typed `ResolutionExplanation` projected from ResolutionTrace. It is structured data, not LLM prose. Channels only consume shared envelope; MAX stays transport/notification.

## Эволюция database и API

Alembic changes are additive after clean Stage 2 head `0038_admission_offering_scope_and_exam_choices`, subject to a fresh deployed-head/remote check. The first new code revision is expected to follow 0038 (likely 0039 only if still a single current head). Stage 2's version-column sizing is already in `backend/alembic/env.py`. Do not edit applied migrations or recreate existing source snapshots, admission-benefit coverage, benefit scopes, campus/offering identity or exam choice groups. Ship each schema with its first write path; approval ledger/revision tables precede any PolicyRule candidate writes and the resolver.

Likely names, subject to Stage 2 naming conventions/final model review: versioned `knowledge_sources`; per-source `source_observations` referencing existing `source_snapshots.content_sha256` and `ingest_runs.id`; typed claims/revisions/evidence/change/conflict records; immutable `policy_approval_events` keyed to exact policy revision hash and ordered per revision; policy selector/revision/scope/relation/dependency records; admissions-owned `admission_cycles`; optional rebuildable impact projections. Do not duplicate SourceSnapshot, current admission-benefit rules/scopes/coverage, or create a generic Review platform table per entity. Add uniqueness for normalized registry identity, source+snapshot observation idempotency, claim fingerprint, revision/hash and typed edge identity; FKs to owner IDs/snapshots and checks for interval/approval shape. Never use one giant polymorphic table.

Use canonical IDs, foreign keys, uniqueness/idempotency/revision constraints. Keep allowlist identity, polling policy/health, scope/evidence/time/status/approval relational. JSONB is only bounded selector/extraction payload. Initial btree indexes by source/capture, claim fingerprint/recorded time, source health/last success, pending review, exact rule revision/hash/approval, scope key, valid/system time, cycle, reverse dependency. Add GIN/range only after PostgreSQL EXPLAIN. PostgreSQL, not SQLite alone, is authoritative.

Extend Stage 2 `/assistant/query` and its existing typed QuerySession/AssistantResult/ResponseEnvelope; do not add a second assistant. Add use-case APIs for effective policy/history, impact/what-if preview, authenticated review queue/actions, and source/evidence only where needed; no table-by-table CRUD. Extend OpenAPI via current backend exporter and regenerate `frontend-next` types. Preserve Stage 2 admission/session/evidence fields additively; never hand-edit generated types.

## Стратегия testing и evaluation

Future tests are in scope; no tests/build/migration command is run during planning.

- Unit: lifecycle/approval hash transitions, selector AST safety, temporal boundaries, scope/precedence/mandatory ResolutionTrace, conflict, impact/actionability.
- Contract: Pydantic/API serialization, old QuerySession compatibility, ResponseEnvelope/OpenAPI.
- Repository: PostgreSQL FKs/uniqueness/idempotency/index/time and Alembic empty/populated upgrades.
- Architecture: module boundaries, canonical ownership and composition root.
- Integration: allowlisted registry → scheduled bounded poll → source health/hash/snapshot → candidate → approval ledger/review → canonical owner → dependency refresh.
- Vertical: official document → claim/evidence → pending exact revision → explicit approval event → effective resolver/ResolutionTrace → domain-owner calculation → assistant answer → provenance.
- Temporal: one rule for 2027/2028; valid vs knowledge time.
- Conflict/exception: authoritative disagreement unresolved; federal+university/direction exception.
- Jev: reuse Stage 2 eval harness; independent frozen labels and at least 500 matching cases per production-used matching operation; existing locks/corpora do not calibrate new operations; false matches, hallucinated relations, unresolved recall, incorrect overrides/scope/time; fail closed and keep current locks/flags unchanged.
- E2E: FastAPI/OpenAPI to channel-neutral envelope; channels only consume it.
- Golden scenarios A-N: rumor; official proposal; adopted future not applicable 2027; 2028 applicant; university exception; direction exception; Olympiad BVI/100 change; achievement change; supersession; authoritative conflict; missing source with retained snapshot; duplicate news; no evidence means insufficient data; what-if without canonical mutation.
- All existing catalog, curricula, analytics, comparison, admissions, fit, benefits, proftest, recommendations, decision, assistant, Web and channel suites remain runnable.

## Rollout, совместимость, security и performance

Flags independently gate observation/candidate writes, parser, policy candidate write (only after immutable approval ledger exists), full review UI, resolver shadow/read (approved revisions only), domain adapter, assistant intent, response template and optional LLM. Jev operations retain Stage 2 defaults and are separately locked; no Jev flag changes here. Roll out additive schema → allowlisted observation/staging → approval gate → review UI → diff/impact → approved-only resolver shadow parity → one domain slice → verified assistant → optional LLM last. Each product capability flag has owner/default/metric/rollback. Mismatch/stale projection returns explicit unavailable/uncertain. Roll back by flag, not destructive DB downgrade.

Backfill only where snapshot/hash/locator exists; unknown trust, cycle, publication/effect/system time and relations stay unknown. Old API paths and vertical slices remain until parity.

Security: reuse HTTPS allowlist/public DNS/per-redirect validation/download/PDF/MIME limits; no arbitrary URL; bounded non-executable AST; untrusted text rendered safely; scoped authorization, immutable audit, idempotency. Logs use IDs/hash prefix/status/duration, not secrets/cookies/raw body/profile.

Plan for dozens of universities, thousands of programs, tens of thousands of documents, hundreds of thousands of claims/relations. Batch reads, bound pages/traversals, incremental reverse-dependency recomputation; no billions-scale design.

## Риски

| Risk | Mitigation |
|---|---|
| Dirty checkout mixed into implementation | Phase 00 clean worktree/baseline gate |
| Plan implemented from dirty old branch | Mandatory clean worktree pinned to Stage 2 SHA before Task 1 |
| Jev Stage 2 duplicated or locks silently invalidated | Reuse wired QuestionRegistry/TypeSafe/runtime; separate definitions/locks for new operations; preserve Stage 2 lock hashes |
| Candidate crosses resolver without review | Exact-revision approval-event gate is persisted before any PolicyRule candidate write; resolver repository returns approved rows only |
| Generic selector becomes second benefit calculator | Policy only selects owner rule revisions; current Stage 2 admission_benefits evaluator owns all benefit/confirmation/validity/achievement calculations |
| CI health probe mistaken for production poller | Distinguish read-only source-health workflow from allowlisted scheduled ingestion command and require a scheduler owner |
| Proposal reported as effective | Independent trust/lifecycle/review; resolver gates application |
| Knowledge becomes god module/facts table | Only two new contexts; preserve subject owners |
| Duplicate benefit evaluator | Stage 2 AdmissionDecisionService/Evaluator/IndividualAchievementCalculator/EffectiveCompetitiveScoreCalculator remain the only calculators |
| Resolver gives unexplained output | Mandatory typed ResolutionTrace accompanies success, no-match, conflict and blocked outcomes |
| Wrong cohort inferred | Source-backed AdmissionCycle and fail-closed mapping |
| Latest row silently wins | Explicit partial precedence/conflict trace |
| Jev hallucination changes truth | Bounded IDs, independent 500-case corpus, validation, review, calibration |
| False historical precision | Report retained history coverage; no invented backfill |
| Source disappearance treated as repeal | Retain snapshot; require explicit event |
| LLM adds facts | Structured result first, server factual rendering, deterministic fallback |
| Impact projection stale | Revision tags, targeted refresh, visible stale state and reconciliation |
| Existing admin role grants federal authority | Separate explicit policy capability |
| JSONB loses constraints | Bounded AST and relational fields/PostgreSQL tests |
| Scope drifts into news aggregator | First slice tied to applicant decision; no open crawl |

## Явно отвергнутые alternatives

No microservices, Knowledge Core/Data Staging deployment, Kafka, multiple databases, service discovery or distributed transactions. No graph DB simply because dependencies form a graph. No giant facts table/blob. No new change_intelligence/review/entity resolver/Jev client/assistant/provenance stack/benefit evaluator. No arbitrary scripts, dynamic code or model SQL. No Jev/LLM truth/legal/eligibility decisions. No trust=status conflation, latest-row-wins, calendar-year inference, missing-as-negative, applicant-wide impact persistence, fabricated history or auto-activation from news.

## Человеческие решения перед реализацией

1. **Policy approval authority:** name the human actor/capability that may approve an exact policy revision, and the distinct scope/authority available to university editors versus a central policy steward.
2. **Source acquisition:** approve the first versioned source allowlist (publisher, host/path or feed/API, reliability tier, allowed adapter) and discovery cadence; name the operational scheduler/runner owner. Stage 2's scheduled `source-health` workflow is read-only and does not meet this requirement.
3. **Pilot:** approve one future federal admission rule, one BMSTU exception/cycle mapping and one Admission Benefit or Individual Achievement slice; confirm broad multi-source news monitoring stays post-pilot.
4. **Cycle and history:** name the reviewer for ambiguous admission-cycle mappings and set the minimum retained history/coverage to promise “what did Andromeda know at date X?”.
5. **Domain ownership for novel semantics:** if a candidate cannot fit existing `admissions`, `admission_fit` or Stage 2 `admission_benefits` contracts/evaluators, approve the owning module/contract change before such a rule is represented as calculable data.
6. **Optional AI:** later decide if verbalizer or outside-coverage fallback ships; provider and retention policy are not selected. Defaults remain off.
7. **New Jev operations:** name independent corpus/label owner and approve safety thresholds if claim/relation/policy classification is proposed for production. This is not a Stage 2 merge decision; current Stage 2 locks/flags remain untouched by this plan.

Task 1 is the baseline-isolation gate: recheck the Stage 2 remote/deployed heads and create a separate clean worktree from verified SHA `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`. No architectural decision or merge blocks starting Task 1. Before source polling and policy-candidate writes, decisions 1-3 are required. Before calculating unsupported domain semantics, decision 5 is required. Decisions 4, 6 and 7 block their respective history, optional LLM or new Jev phases, not the deterministic core.

## Phase Index

1. [Фаза 00: Исходный baseline и архитектурные gates](phase-00-baseline-and-decisions.md) — Tasks 1-2
2. [Фаза 01: Canonical vocabulary и ownership](phase-01-vocabulary-ownership.md) — Tasks 3-4
3. [Фаза 02: Источники, provenance и temporal foundation](phase-02-source-temporal-foundations.md) — Tasks 5-6
4. [Фаза 03: Staging claims и changes](phase-03-staging-claims-changes.md) — Tasks 7-9
5. [Фаза 04: Правила как данные и typed DSL](phase-04-policy-rule-data.md) — Tasks 10-11
6. [Фаза 05: Temporal applicability, precedence и conflicts](phase-05-effective-resolution.md) — Tasks 12-14
7. [Фаза 06: Dependencies, semantic diff и impact](phase-06-dependencies-impact.md) — Tasks 15-17
8. [Фаза 07: Human review, manual data и operator workflow](phase-07-review-and-ops.md) — Tasks 18-20
9. [Фаза 08: Bounded Jev-assisted semantics](phase-08-jev-bounded-resolution.md) — Tasks 21-23
10. [Фаза 09: Admission cycles, benefits и achievements](phase-09-admission-domain-integration.md) — Tasks 24-25
11. [Фаза 10: Conversation и assistant queries](phase-10-assistant-integration.md) — Tasks 26-27
12. [Фаза 11: ResponseEnvelope и три режима ответа](phase-11-response-modes.md) — Tasks 28-30
13. [Фаза 12: What-if, future и historical queries](phase-12-what-if-history.md) — Tasks 31-32
14. [Фаза 13: Regression, evaluation, security и performance gates](phase-13-quality-security-performance.md) — Tasks 33-35
15. [Фаза 14: Backfill, rollout, compatibility и documentation](phase-14-evolution-rollout.md) — Tasks 36-39

## Cross-Phase Dependencies

- Task 1 creates a plan-only commit from the plan/research allowlist, creates a clean worktree at Stage 2 SHA `1f5777c892c2daf2f6f11a405bc19268b7dc0c88`, cherry-picks only that artifact commit, verifies path/parent integrity and proves the pre-change baseline green. It then invokes the bundle by explicit `@path`; Task 2 records source allowlist/scheduler/pilot/reviewer decisions. No old-branch merge is allowed.
- Tasks 3-4 freeze ownership/contracts; Task 10 atomically persists the first policy candidate/revision with its immutable `PENDING_SUBMITTED` audit event before any policy writer or resolver can consume it.
- Task 5 defines the versioned source registry/observations over existing Stage 2 snapshots; Task 6 adds admissions-owned cycle mapping and bitemporal contracts before applicability.
- Task 7 stages claims and source lifecycle only; Task 8 adds bounded registry-driven polling/candidate parsing; Task 9 deduplicates/diffs. Discovery never creates effective rules.
- Task 10 delivers the first persisted PolicyRule/RuleCandidate shape atomically with the initial `PENDING_SUBMITTED` event in the policy-owned approval ledger; no policy writer or resolver ships before this gate. Task 11 validates bounded applicability/owner dispatch without domain calculations.
- Tasks 12-14 resolve only exact approved revisions, require mandatory ResolutionTrace on every outcome, and model precedence/conflicts.
- Tasks 15-17 add dependencies/diff/impact after resolver contracts.
- Tasks 18-20 build the full review UI on top of the early immutable approval ledger; they are not the first approval gate.
- Tasks 21-23 reuse Stage 2 Jev runtime/Question Registry/TypeSafe/calibration/eval tooling; new operations wait for independent corpus/operation lock, with existing locks/flags untouched.
- Tasks 24-25 adapt approved policy references into Stage 2 domain owners; benefit/confirmation/validity/achievement calculation remains in admission_benefits.
- Tasks 26-30 extend current conversation/response after policy read contracts.
- Task 31 runs unapproved candidates only in a separate hypothetical sandbox, never through or around the approved-only production resolver; Task 32 uses bitemporal revisions/session context.
- Tasks 33-35 gate release and do not replace phase-level verification.
- Migration revisions are attached to the first persistence phase and continue after clean Stage 2 head 0038; Task 36 performs final chain/deployment-head reconciliation, Task 37 never infers approval from legacy ACTIVE rows, and Tasks 38-39 cover rollout/docs.

## Tasks

### Фаза 00: Исходный baseline и архитектурные gates

- [ ] Task 1: Перенести plan bundle на clean Stage 2 ветку и подтвердить green baseline ([details](phase-00-baseline-and-decisions.md#task-1))
- [ ] Task 2: Утвердить ownership, пилот и human approval ([details](phase-00-baseline-and-decisions.md#task-2))

### Фаза 01: Canonical vocabulary и ownership

- [ ] Task 3: Утвердить ownership vocabulary без параллельных canonical stores ([details](phase-01-vocabulary-ownership.md#task-3))
- [ ] Task 4: Описать module boundaries, public ports и lifecycle contracts ([details](phase-01-vocabulary-ownership.md#task-4))

### Фаза 02: Источники, provenance и temporal foundation

- [ ] Task 5: Сохранить source identity и повторные observations ([details](phase-02-source-temporal-foundations.md#task-5))
- [ ] Task 6: Ввести bitemporal revisions и владельца admission cycle ([details](phase-02-source-temporal-foundations.md#task-6))

### Фаза 03: Staging claims и changes

- [ ] Task 7: Смоделировать claims, evidence links, milestones и независимые оси статуса ([details](phase-03-staging-claims-changes.md#task-7))
- [ ] Task 8: Добавить deterministic parsing и bounded validation кандидатов ([details](phase-03-staging-claims-changes.md#task-8))
- [ ] Task 9: Определять source/claim diffs и безопасно объединять дубликаты ([details](phase-03-staging-claims-changes.md#task-9))

### Фаза 04: Правила как данные и typed DSL

- [ ] Task 10: Задать bounded policy selector DSL и immutable approval ledger ([details](phase-04-policy-rule-data.md#task-10))
- [ ] Task 11: Добавить deterministic applicability validation и domain dispatch ([details](phase-04-policy-rule-data.md#task-11))

### Фаза 05: Temporal applicability, precedence и conflicts

- [ ] Task 12: Определить temporal и cohort applicability ([details](phase-05-effective-resolution.md#task-12))
- [ ] Task 13: Реализовать authority, specificity и явное разрешение overrides ([details](phase-05-effective-resolution.md#task-13))
- [ ] Task 14: Смоделировать conflict groups и безопасный unresolved ответ ([details](phase-05-effective-resolution.md#task-14))

### Фаза 06: Dependencies, semantic diff и impact

- [ ] Task 15: Задать типизированные relation и dependency contracts ([details](phase-06-dependencies-impact.md#task-15))
- [ ] Task 16: Формировать semantic diff до approval ([details](phase-06-dependencies-impact.md#task-16))
- [ ] Task 17: Вычислять bounded impact и incremental refresh ([details](phase-06-dependencies-impact.md#task-17))

### Фаза 07: Human review, manual data и operator workflow

- [ ] Task 18: Реализовать review transitions и audit ([details](phase-07-review-and-ops.md#task-18))
- [ ] Task 19: Добавить авторизованный source/manual-data workflow ([details](phase-07-review-and-ops.md#task-19))
- [ ] Task 20: Создать review queue с diff и impact preview ([details](phase-07-review-and-ops.md#task-20))

### Фаза 08: Bounded Jev-assisted semantics

- [ ] Task 21: Определить bounded operations через существующий Jev seam ([details](phase-08-jev-bounded-resolution.md#task-21))
- [ ] Task 22: Задать независимый Jev evaluation lifecycle ([details](phase-08-jev-bounded-resolution.md#task-22))
- [ ] Task 23: Добавить shadow rollout и Jev audit ([details](phase-08-jev-bounded-resolution.md#task-23))

### Фаза 09: Admission cycles, benefits и achievements

- [ ] Task 24: Подключить AdmissionCycle и адаптер выбора benefit rule ([details](phase-09-admission-domain-integration.md#task-24))
- [ ] Task 25: Интегрировать правила экзаменов, admissions и achievements ([details](phase-09-admission-domain-integration.md#task-25))

### Фаза 10: Conversation и assistant queries

- [ ] Task 26: Расширить intent, parser и typed QuerySession context ([details](phase-10-assistant-integration.md#task-26))
- [ ] Task 27: Добавить policy lookup в assistant orchestration ([details](phase-10-assistant-integration.md#task-27))

### Фаза 11: ResponseEnvelope и три режима ответа

- [ ] Task 28: Расширить ResponseEnvelope для policy/evidence/relevance ([details](phase-11-response-modes.md#task-28))
- [ ] Task 29: Реализовать deterministic и constrained verbalization modes ([details](phase-11-response-modes.md#task-29))
- [ ] Task 30: Добавить явно unverified fallback вне coverage ([details](phase-11-response-modes.md#task-30))

### Фаза 12: What-if, future и historical queries

- [ ] Task 31: Реализовать deterministic what-if sandbox ([details](phase-12-what-if-history.md#task-31))
- [ ] Task 32: Поддержать current/future/historical/as-known-at queries ([details](phase-12-what-if-history.md#task-32))

### Фаза 13: Regression, evaluation, security и performance gates

- [ ] Task 33: Добавить golden scenarios и temporal/conflict regression ([details](phase-13-quality-security-performance.md#task-33))
- [ ] Task 34: Поставить fail-closed Jev evaluation gates ([details](phase-13-quality-security-performance.md#task-34))
- [ ] Task 35: Задать security, performance и operational budgets ([details](phase-13-quality-security-performance.md#task-35))

### Фаза 14: Backfill, rollout, compatibility и documentation

- [ ] Task 36: Согласовать clean baseline и порядок additive migrations ([details](phase-14-evolution-rollout.md#task-36))
- [ ] Task 37: Backfill recoverable provenance и сохранить legacy contracts ([details](phase-14-evolution-rollout.md#task-37))
- [ ] Task 38: Включать rollout по capabilities и мониторить parity ([details](phase-14-evolution-rollout.md#task-38))
- [ ] Task 39: Обновить architecture, operations, API и roadmap docs ([details](phase-14-evolution-rollout.md#task-39))

## Commit Plan

- **Plan-only handoff commit before implementation Task 1** (planning branch; cherry-pick onto Stage 2): `docs(plan): reconcile policy knowledge plan with Stage 2` — only the ultra plan bundle and the five named linked research artifacts; verify the full path list before committing.
- Commit 1 after Tasks 1-4: docs: establish policy ownership and clean baseline
- Commit 2 after Tasks 5-8: feat: add source observations and claim staging
- Commit 3 after Tasks 9-11: feat: add bounded policy rule data
- Commit 4 after Tasks 12-14: feat: resolve temporal policy and conflicts
- Commit 5 after Tasks 15-17: feat: add policy dependency and impact analysis
- Commit 6 after Tasks 18-20: feat: add auditable policy review
- Commit 7 after Tasks 21-23: feat: add gated Jev candidate assistance
- Commit 8 after Tasks 24-27: feat: integrate policy with admissions assistant
- Commit 9 after Tasks 28-30: feat: expose typed policy response modes
- Commit 10 after Tasks 31-35: test: gate historical policy and impact rollout
- Commit 11 after Tasks 36-39: docs: document source-backed policy rollout

## Definition of Done

- Official source → immutable snapshot → deterministic claims/change/rule candidate → validation → human review → semantic diff/impact → canonical owner update → targeted refresh.
- Approved policy resolves deterministically for explicit cycle/program/applicant context, including source-backed exceptions and conflicts.
- Current benefit evaluator remains sole calculator with olympiad/profile/BVI/100/confirmation/validity/achievement provenance.
- Typed multi-turn QuerySession and existing /assistant/query return channel-neutral evidence/status/uncertainty.
- Jev stays bounded/evaluated/reviewed. LLM is optional and adds no facts; fallback is visibly unverified and cannot affect canonical decisions.
- Before the first runtime edit, the implementation branch contains only Stage 2 code plus the plan-only artifacts, and the full pre-change baseline evidence is green at the Stage 2 code SHA.
- A-N and existing product regressions pass on a selected clean baseline.
- PostgreSQL/Alembic evolution is additive and linear; rollout flags preserve old paths; docs/OpenAPI reflect shipped behavior; pre-existing changes remain untouched.
