# Frontend API

Документ описывает, как браузерный клиент Andromeda общается с backend: какие HTTP-операции вызывает frontend, какие параметры и JSON отправляет, какие данные получает и как эти данные превращаются в экраны.

Источник истины для имён полей, типов, ограничений и response-кодов — [frontend/openapi.json](openapi.json). Реализация транспортного слоя находится в [src/api/client.ts](src/api/client.ts), а типы в [src/api/generated.ts](src/api/generated.ts) генерируются из OpenAPI и вручную не редактируются.

[← README frontend](README.md) · [Backend API overview](../docs/api.md)

## 1. Общая схема обмена

```text
Пользователь
    ↓ действия на экране
frontend/src/features/*
    ↓ типизированный wrapper из src/api/client.ts
requestJson()
    ↓ fetch + credentials: include + JSON
FastAPI backend (/programs, /proftest, /auth, ...)
    ↓ application service через dependency composition
Repositories / canonical DB / source-backed projections
    ↓ typed response по OpenAPI
JSON → frontend state → HTML-рендеринг страницы
```

| Уровень | Что делает | Что не делает |
|---|---|---|
| UI feature | Показывает loading, данные, empty/error states; собирает пользовательский ввод | Не читает SQLite/PostgreSQL, PDF, parser snapshots или файлы напрямую |
| `src/api/client.ts` | Формирует URL, query string, JSON body, credentials и разбирает ошибки | Не содержит бизнес-правил рекомендаций, сравнения или ingestion |
| FastAPI route | Принимает и валидирует HTTP contract, вызывает application service | Не содержит расчёты предметной области и SQLAlchemy-модели |
| Application service | Выполняет use case: каталог, сравнение, профиль, admissions, рекомендации | Не зависит от DOM и frontend-кода |
| Infrastructure/repository | Читает canonical projection и source provenance из базы | Не меняет формат frontend response самостоятельно |
| OpenAPI/generated types | Фиксируют public contract между backend и TypeScript | Не являются отдельным runtime API |

В текущем контракте опубликовано 29 backend-операций. В `client.ts` для большинства есть удобные функции-обёртки; два endpoint-а (`GET /discipline-areas` и `GET /campus/points`) уже есть в backend/OpenAPI, но отдельного wrapper-а в текущем frontend client пока нет.

## 2. Как работает HTTP-клиент

### 2.1. Настройки

| Настройка | Где задаётся | Текущее поведение |
|---|---|---|
| `VITE_API_BASE_URL` | `.env`/переменные Vite | Префикс перед API path. Если не задан, используется пустая строка и запросы идут на тот же origin, например `/programs`. |
| `VITE_LOG_LEVEL` | `.env`/переменные Vite | По умолчанию `WARN`. В development при значении `DEBUG` включаются `request_start` и `request_complete`. |
| Timeout | Константа `API_REQUEST_TIMEOUT_MS` | 45 000 мс на запрос. По истечении времени выбрасывается `ApiTimeoutError`. |
| Credentials | `requestJson()` | Всегда `credentials: "include"`, поэтому browser отправляет и принимает cookie backend. |
| Формат | `requestJson()` | `Accept: application/json`, `Content-Type: application/json`; тела POST/PUT сериализуются через `JSON.stringify`. |
| Path id | публичные wrappers | Значения `id` проходят через `encodeURIComponent`, поэтому canonical ID безопасно передаётся в path. |

Пример локальной конфигурации:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_LOG_LEVEL=DEBUG
```

Если frontend и backend работают на разных origin, backend должен разрешить именно frontend origin для credentialed CORS. `POST /auth/register`, `POST /auth/login` и `POST /auth/logout` дополнительно проверяют заголовок `Origin` по списку доверенных frontend origins.

### 2.2. Единый алгоритм запроса

1. Feature вызывает типизированную функцию, например `getProgram(id)`.
2. Wrapper строит path и query string и передаёт их в `requestJson<T>()`.
3. Клиент добавляет JSON headers и `credentials: "include"`, затем вызывает `fetch`.
4. Ответ всегда читается как JSON.
5. Для `2xx` payload приводится к типу из `generated.ts` и возвращается feature.
6. Для неуспешного ответа клиент пытается распознать `ErrorResponse`. Если распознал, выбрасывается `ApiError` с HTTP status и payload; иначе — обычный `Error`.
7. Timeout превращается в `ApiTimeoutError`; сетевые ошибки и ошибки разбора JSON остаются обычными runtime errors.

Frontend не хранит access token в `localStorage` и не добавляет `Authorization: Bearer`. Сессия передаётся cookie-механизмом browser.

## 3. Полная таблица endpoint-ов

В колонке «Состояние wrapper-а» указано состояние именно текущего [client.ts](src/api/client.ts), а не возможность backend в целом.

### 3.1. Каталог, программа и учебный план

| UI-сценарий | Метод и path | Параметры | Тело | Успешный ответ | Авторизация и состояние wrapper-а |
|---|---|---|---|---|---|
| Старт приложения и страница «Каталог» | `GET /programs` | Нет | Нет | `ProgramListResponse`: `items` — список программ | Public read. Wrapper `getPrograms()` есть; `main.ts` вызывает его до рендера AppShell. |
| Открытие карточки программы | `GET /programs/{id}` | Path `id`, canonical `program:NN.NN.NN-NN` | Нет | `ProgramResponse`: объект `program` | Public read. Wrapper `getProgram(id)` есть; `ProgramPage` передаёт полученный `program.id`. |
| Вкладка «Учебный план» | `GET /programs/{id}/curriculum` | Path `id` | Нет | `CurriculumResponse`: metadata плана и `items` | Public read. Wrapper `getCurriculum(id)` есть; вызывается параллельно с admissions. |
| Вкладка «Поступление» | `GET /programs/{id}/admissions` | Path `id` | Нет | `ProgramAdmissionsResponse`: `program`, `programId`, `offerings[]` | Public read. Wrapper `getProgramAdmissions(id)` есть. |
| Справочник taxonomy | `GET /discipline-areas` | Нет | Нет | `DisciplineAreaCatalogResponse`: `items[]` с `code`, `name`, `description`, `position` | Public read. Backend/OpenAPI endpoint есть; отдельной функции в `client.ts` и текущего UI-вызова нет. |

Один запрос `GET /programs` возвращает весь доступный backend-каталог. В текущем frontend API для него нет параметров `page`, `offset` или `limit`, поэтому клиент не реализует отдельную pagination-логику: фильтры по коду, названию, году и `directionId` применяются локально к уже полученному `items` в `CatalogPage`.

### 3.2. Admissions и Admission Fit

| UI-сценарий | Метод и path | Параметры | Тело | Успешный ответ | Авторизация и состояние wrapper-а |
|---|---|---|---|---|---|
| Показать все наборы, экзамены, квоты и проходные баллы | `GET /programs/{id}/admissions` | Path `id` | Нет | `ProgramAdmissionsResponse` с `offerings[]` | Public read. Вызов общий с экраном программы. |
| Рассчитать реалистичность поступления | `POST /programs/{id}/admission-fit` | Path `id` и `offeringId` внутри body | `AdmissionFitRequestBody` | `AdmissionFitResponse` | Public calculation. Wrapper `calculateAdmissionFit(id, request)` есть; Content Fit/ranking не меняет. |

Frontend сначала получает admissions, затем выбирает конкретный `offering.id`. В запрос нельзя подставлять только год или тип квоты: backend сравнивает данные именно с тем offering, который пришёл из `GET /programs/{id}/admissions`.

#### Формат admissions

| Объект | Поля | Смысл для UI |
|---|---|---|
| `AdmissionOfferingResponse` | `id`, `admissionYear`, `studyForm`, `fundingType`, `scope`, `places`, `exams[]`, `quotas[]`, `passingScores[]`, `tuition[]`, `provenance[]` | Один вариант набора с конкретным годом, формой, финансированием и областью действия. `scope` — `program` или `direction`. |
| `ExamRequirementResponse` | `subject`, `sourceName`, `minimumScore`, `isChoice`, `isRequired`, `provenance` | Предмет вступительного испытания, минимальный балл и признак «на выбор»/обязательности. |
| `QuotaResponse` | `quotaType`, `sourceName`, `places`, `provenance` | Квота и число мест, если оно опубликовано источником. |
| `PassingScoreResponse` | `scoreType`, `competitionType`, `status`, `score`, `provenance` | Проходной ориентир для типа конкурса. `competitionType` различает общий конкурс, особую/отдельную/целевую квоту, БВИ и прочие варианты. |
| `TuitionCostResponse` | `amount`, `currency`, `academicYear`, `period`, `studyForm`, `isDiscounted`, `provenance` | Стоимость платного обучения, скидка и период действия. Денежные значения приходят строками. |
| `AdmissionProvenanceResponse` | `sourceKind`, `sourceUrl`, `capturedAt`, `contentSha256`, `locator`, `sourceName` | Доказательство происхождения admission-факта: официальный URL, время capture, SHA-256 и необязательная позиция в источнике. |

Значения `competitionType`:

| Значение | Отображаемый смысл |
|---|---|
| `general` | Общий конкурс |
| `special_quota` | Особая квота |
| `separate_quota` | Отдельная квота |
| `targeted` | Целевой набор |
| `bvi` | Без вступительных испытаний |
| `other` | Иной тип конкурса, который источник не удалось точнее классифицировать |

БВИ передаётся без искусственного нулевого или числового балла: у записи `PassingScoreResponse` должно быть `status: "bvi"` и `score: null`. Числовой проходной балл передаётся как строка, например `"276.00"`, чтобы не терять decimal precision. `null` также используется, если источник не опубликовал соответствующий факт.

#### Запрос Admission Fit

```json
{
  "version": 1,
  "offeringId": "admission-offering:program:09.03.01-02:2026:full_time:budget:direction",
  "applicant": {
    "version": 1,
    "scores": [
      {"subject": "Математика", "score": 90},
      {"subject": "Русский язык", "score": 88},
      {"subject": "Информатика", "score": 92}
    ]
  }
}
```

| Поле | Тип и ограничение | Источник значения |
|---|---|---|
| `version` | Const `1`, необязателен в body, default `1` | Версия public request contract. |
| `offeringId` | Непустая строка до 512 символов | `offerings[].id` из admissions. |
| `applicant.version` | Const `1` | Версия applicant contract. |
| `applicant.scores[]` | Массив введённых результатов | Поля `subject` и `score`; score — число или строка в диапазоне `0..100`. |

Ответ содержит `status` (`realistic`, `borderline`, `unlikely`, `insufficient_data`), integer `score` от 0 до 100, `applicantTotalScore`, `dataQuality`, три метрики `breakdown` (`minimumReadiness`, `passingReadiness`, `dataCompleteness`), а также объяснения `reasons`, `antiReasons` и `dataGaps`.

`Admission Fit` — отдельное измерение. Его результат не подмешивается в Content Fit, не меняет порядок `/recommendations` и не принимает `UserProfile` вместо applicant scores.

### 3.3. Сравнение программ

| UI-сценарий | Метод и path | Параметры | Тело | Успешный ответ | Авторизация и состояние wrapper-а |
|---|---|---|---|---|---|
| Сравнить две программы целиком | `GET /compare?programIds=ID_A,ID_B&scope=all` | Обязательный `programIds` — две canonical IDs через запятую; `scope=all` по умолчанию | Нет | `ComparisonResponse` | Public read. Wrapper `comparePrograms([idA, idB], options)` есть. |
| Сравнить один семестр | `GET /compare?programIds=ID_A,ID_B&scope=semester&semester=3` | `semester` — integer `1..12`; обязателен по смыслу при `scope=semester` | Нет | Тот же `ComparisonResponse`, с `semester` | Public read. `URLSearchParams` кодирует query. |

`ComparisonResponse` содержит:

| Поле | Содержимое |
|---|---|
| `programA`, `programB` | Полные `ProgramSummaryResponse` двух выбранных программ. |
| `scope`, `semester` | Применённый режим сравнения и выбранный семестр либо `null`. |
| `rows[]` | Дисциплина, семестр, workload A/B, статус наличия и deltas часов/ЗЕТ. |
| `totalsA`, `totalsB` | Итоги по часам и кредитам для каждой программы. |
| `areaBreakdownA`, `areaBreakdownB` | Необязательная разбивка по 22 discipline areas. |

### 3.4. Профиль, профтест и рекомендации

| UI-сценарий | Метод и path | Параметры/body | Успешный ответ | Где используется |
|---|---|---|---|---|
| Загрузить банк вопросов | `GET /proftest/questions` | Нет | `QuestionnaireResponse`: `version`, `questions[]` | `ProftestPage` передаёт вопросы на base/adaptive screens. Wrapper `getProftestQuestions()`. |
| Получить preview во время теста | `POST /proftest/preview` | `ProftestSubmissionRequest` | `ProftestPreviewResponse`: профиль, adaptive decision, следующий вопрос, candidates | `ProftestPage`/state при промежуточной отправке. Wrapper `previewProftest(request)`. |
| Завершить тест и получить TOP | `POST /proftest/results` | `ProftestSubmissionRequest` | `ProftestResultsResponse`: финальный профиль и `recommendations[]` | `ProftestPage`/results screen. Wrapper `getProftestResults(request)`. Профиль сохраняется backend. |
| Прочитать текущий профиль | `GET /proftest/profile` | Нет | `UserProfileSnapshotResponse` | Account, recommendations, unified flow и profile persistence. Wrapper `getCurrentProfile()`. |
| Создать профиль явно | `POST /proftest/profile` | `UserProfileCreateRequest` с `profile` | `UserProfileSnapshotResponse`, HTTP `201` | Wrapper `createCurrentProfile(request)` есть; текущий основной test flow сохраняет профиль через `/proftest/results`. |
| Обновить профиль явно | `PUT /proftest/profile` | `UserProfileUpdateRequest`: `profile` + `expectedRevision` | Новый snapshot | Wrapper `updateCurrentProfile(request)` есть; optimistic concurrency через revision. |
| Посчитать рекомендации для переданного профиля | `POST /recommendations` | `RecommendationRequest`: `profile` + `limit` `1..20` | `RecommendationsResponse` | Wrapper `getRecommendations(request)` есть; основной UI может получить тот же результат через proftest results/current. |
| Получить рекомендации сохранённого профиля | `GET /recommendations/current?limit=10` | `limit` `1..20`, default `10` | `RecommendationsResponse`: профиль + TOP | Recommendations page, account, unified flow, profile persistence. Wrapper `getCurrentRecommendations(limit)`. |

#### Вопросы и ответы профтеста

| Объект | Поля | Назначение |
|---|---|---|
| `QuestionResponse` | `id`, `block`, `prompt`, `options[]`, `required`, `adaptive`, `multiSelect`, `maxSelected` | Описание вопроса, его вариантов и правил выбора. `block`: `interests`, `activities`, `anti_interests` или `adaptive`. |
| `QuestionOptionResponse` | `id`, `label` | Вариант, который frontend показывает пользователю; наружу отправляется только `id`. |
| `ProftestAnswerRequest` | `questionId`, `optionIds[]`, optional `intensity` | Base-ответ. `optionIds` содержит от 1 до 6 значений; intensity лежит в `0..1`. |
| `ProftestAdaptiveAnswerRequest` | `questionId`, `optionId`, `dimension` | Ответ на adaptive-вопрос и выбранное измерение. |
| `ProftestSubmissionRequest` | `answers[]`, `adaptiveAnswers[]` | Общий body для preview и results. Ответы не должны содержать внутренних весов или runtime LLM data. |

Пример body для обоих POST proftest endpoint-ов:

```json
{
  "answers": [
    {
      "questionId": "interests-1",
      "optionIds": ["option-computing"],
      "intensity": "0.8500"
    }
  ],
  "adaptiveAnswers": [
    {
      "questionId": "adaptive-1",
      "optionId": "option-research",
      "dimension": "research"
    }
  ]
}
```

`UserProfileResponse` состоит из `interests`, `activityPreferences`, `antiInterests`, весов `preferredSubjectWeights`, `preferredActivityWeights`, `negativeWeights`, `confidence` и `adaptiveAnswers`. В input decimal values допускаются как number или string; в output веса и confidence сериализуются строками с фиксированной точностью.

Текущая 22-area taxonomy:

| Code | Отображаемое название |
|---|---|
| `mathematics_statistics` | Математика и статистика |
| `computer_science_data` | Компьютерные науки и данные |
| `physics_astronomy` | Физика и астрономия |
| `chemistry_materials` | Химия и материаловедение |
| `biology_biotechnology` | Биология и биотехнологии |
| `earth_environment` | Земля, экология и окружающая среда |
| `engineering_technology` | Инженерия и технологии |
| `architecture_construction` | Архитектура, строительство и урбанистика |
| `agriculture_veterinary` | Сельское хозяйство и ветеринария |
| `medicine_health` | Медицина и здоровье |
| `psychology_cognitive` | Психология и когнитивные науки |
| `society_social_sciences` | Общество и социальные науки |
| `economics_finance` | Экономика и финансы |
| `business_management` | Бизнес, управление и предпринимательство |
| `law_policy_public_administration` | Право, политика и государственное управление |
| `languages_linguistics_literature` | Языки, лингвистика и литература |
| `history_philosophy_humanities` | История, философия и гуманитарные науки |
| `art_design_media` | Искусство, дизайн, медиа и коммуникации |
| `education_pedagogy` | Образование и педагогика |
| `sport_tourism_hospitality` | Спорт, туризм и индустрия гостеприимства |
| `safety_defense_transport` | Безопасность, оборона и транспортные системы |
| `universal_interdisciplinary` | Универсальные и междисциплинарные дисциплины |

#### Формат рекомендаций

Каждый `RecommendationResponse` содержит:

| Поле | Смысл |
|---|---|
| `programId`, `programCode`, `programName` | Canonical identity и отображаемые данные программы. |
| `contentFit` | Integer Content Fit. Это основной content ranking score. |
| `score` | `MatchScoreResponse` с тем же program identity и `breakdown`. |
| `score.breakdown` | `subjectFit`, `activityFit`, `distinctiveFit`, `antiPenalty`, `rawContentFit`; decimal values — строки. |
| `reasons`, `antiFitReasons` | Объяснения fit/anti-fit с area/activity, текстом, workload, share и source names. |
| `areaShare`, `semesterDistribution` | Доли структуры учебного плана для объяснимого ranking. |
| `distinctiveSubjects` | Исходные названия отличительных дисциплин. |
| `workloadReadiness`, `careerFit`, `admissionFit` | Optional metrics. Они могут иметь `status` без числа и не превращаются автоматически в Content Fit. |

## 4. Гостевая сессия и аккаунт

Пользователь может работать без регистрации. Это не отдельный fake mode: backend создаёт anonymous profile scope и связывает его с HttpOnly cookie.

### 4.1. Auth endpoint-ы

| UI-сценарий | Метод и path | Body | Успешный ответ | Поведение cookie |
|---|---|---|---|---|
| Проверить статус профиля в правом верхнем меню | `GET /auth/session` | Нет | `AuthSessionResponse`: `authenticated` и nullable `account` | Неавторизованный пользователь получает `authenticated: false`, `account: null`. |
| Создать аккаунт | `POST /auth/register` | `email`, `password` | `AuthSessionResponse`, HTTP `201` | Backend создаёт account session и ставит auth cookie. |
| Войти | `POST /auth/login` | `email`, `password` | `AuthSessionResponse`, HTTP `200` | Backend ставит новую auth cookie. |
| Выйти | `POST /auth/logout` | Нет | `{authenticated:false, account:null}` | Backend отзывает session и удаляет auth cookie. |

Ограничения request:

| Поле | Register | Login |
|---|---:|---:|
| `email` | Непустая строка 3–320 символов | Непустая строка 3–320 символов |
| `password` | 12–128 символов | 1–128 символов |

Raw auth token не читается JavaScript и не возвращается в JSON. Backend хранит только hash session token. Frontend не логирует пароль, cookie или полный профиль.

### 4.2. Как меняется scope данных

| Ситуация | Что делает backend | Что видит frontend |
|---|---|---|
| Нет auth cookie | Создаёт/переиспользует anonymous profile session cookie | Можно пройти профтест, посмотреть рекомендации и использовать public catalog как гость. |
| Есть валидная auth cookie | `get_profile_scope` использует account scope, сохраняя fallback anonymous session boundary | `/proftest/profile`, `/recommendations/current` и `/personal-route` читают профиль аккаунта. |
| Guest регистрируется или входит | Активный anonymous profile переносится к аккаунту, если у аккаунта ещё нет своего профиля | После успешного auth UI открывает личный кабинет; профиль и рекомендации не должны пропасть. |
| Account выходит | Auth session удаляется; anonymous profile cookie может остаться отдельной | Меню снова показывает «Гость», а account-only данные могут стать недоступны. |
| Профиля нет или TTL истёк | Profile-dependent endpoint возвращает `404 NOT_FOUND` | UI показывает profile-required/empty state, а не зависает и не подставляет фальшивые рекомендации. |

В `AppShell` профильная кнопка располагается в правом верхнем углу. `AuthPanel` сначала вызывает `/auth/session`; затем показывает «Войти», «Создать аккаунт» и «Продолжить как гость» либо меню авторизованного account. Гостевая кнопка не делает отдельный API-запрос: она закрывает меню и оставляет текущий anonymous cookie scope.

## 5. Рекомендации, события, campus и Personal Route

### 5.1. События

| UI-сценарий | Метод и path | Query | Ответ | Frontend wrapper |
|---|---|---|---|---|
| Список событий | `GET /events` | `from`, `to` — ISO datetime; `kind`; `format`; `universityId`; `departmentId`; `programId`; `recommended`; `limit` `1..100`, default `50` | `EventListResponse`: `items[]`, `total` | `getEvents(options)`; вызывается `EventsPage`. |
| Карточка события | `GET /events/{id}` | Path canonical `event:source:slug` | `EventDetailResponse`: `event` | `getEvent(id)`; вызывается `EventPage`. |

Допустимые значения `kind`: `additional_education`, `open_day`, `lecture`, `competition`, `career`, `other`. Значения `format`: `offline`, `online`, `hybrid`.

`recommended=true` означает не «событие придумано для пользователя», а фильтр по program IDs текущих рекомендаций. Для этого backend читает текущий profile scope; если профиля нет, endpoint может вернуть profile-related error.

`EventResponse` содержит `id`, `title`, `kind`, `format`, `startsAt`, nullable `endsAt`, nullable `description`, nullable `registrationUrl`, массивы `universityIds`, `departmentIds`, `programIds`, nullable `venue` и `provenance[]`. Все события должны быть source-backed; frontend не создаёт и не дополняет их выдуманными fixture-значениями.

### 5.2. Campus points

| UI-сценарий | Метод и path | Query/path | Ответ | Состояние frontend |
|---|---|---|---|---|
| Список точек кампуса | `GET /campus/points` | `universityId`, `departmentId`, `programId`, `pointType`, `limit` `1..100`, default `50` | `CampusPointListResponse`: `items[]`, `total` | Backend/OpenAPI есть; отдельного `getCampusPoints()` в `client.ts` сейчас нет. |
| Рекомендованные точки и события | `GET /campus/recommendations` | `limit` `1..100`, default `50` | `CampusRecommendationsResponse`: recommended program IDs, recommendations, points, events и `eventsWithoutPoint` | Wrapper `getCampusRecommendations(limit)` есть; текущие страницы не вызывают его напрямую. |
| Детали точки | `GET /campus/points/{id}` | Path canonical `venue:source:slug` | `CampusPointDetailResponse` | Wrapper `getCampusPoint(id)`; `EventPage` вызывает его, если событие имеет venue. |
| События в точке | `GET /campus/points/{id}/events` | `from`, `to`, `recommended`, `limit` `1..100` | `CampusPointEventsResponse`: `pointId`, `items[]`, `total` | Wrapper `getCampusPointEvents(id, options)`; `EventPage` показывает связанные события. |

Campus point — map-agnostic contract. API отдаёт semantic `pointType`, name, address, optional `latitude`/`longitude`, связи и provenance; frontend не обязан строить карту, геометрию, distance calculation или navigation route.

### 5.3. Personal Route

| UI-сценарий | Метод и path | Query | Ответ | Frontend wrapper |
|---|---|---|---|---|
| Логический «Мой план» | `GET /personal-route` | `limit` `1..20`, default `10` | `PersonalRouteResponse` | `getPersonalRoute(limit)`; вызывается страницей Personal Route, Account и account summary. |

`PersonalRouteResponse` содержит `status`: `ready`, `no_recommendations` или `no_events`; `summary`; рекомендации и ordered `steps[]`. У шага есть `position`, `kind`, `reason`, `programIds` и optional recommendation/event/venue/point/startsAt.

Типы шага:

| `kind` | Смысл |
|---|---|
| `explore_program` | Изучить рекомендованную программу. |
| `compare_programs` | Сопоставить несколько программ. |
| `attend_event` | Рассмотреть связанное событие. |

Это логическая последовательность действий, а не карта перемещения. При отсутствии профиля backend возвращает `404 NOT_FOUND`; frontend показывает `profile-required`, а отсутствие будущих событий — отдельный `no_events` state.

## 6. Операторский ingestion API

Эти операции нужны для operator screen `#ops`, а не обычному посетителю. Доступ включается только если backend настроен непустым `ANDROMEDA_OPS_API_KEY`.

| UI-сценарий | Метод и path | Query/header/body | Успешный ответ | Wrapper |
|---|---|---|---|---|
| Список ingestion runs | `GET /ops/ingestion/runs` | Query `status` (`running`, `completed`, `failed`), `limit` `1..100`; header `X-Andromeda-Ops-Key` | `IngestionRunListResponse`: `items[]`, `total` | `getIngestionRuns(options, opsKey)` |
| Детали run | `GET /ops/ingestion/runs/{id}` | Path `id` формата `ingest:<32 hex>`; header `X-Andromeda-Ops-Key` | `{run: IngestionRunDetailResponse}` | `getIngestionRun(id, opsKey)` |
| Ограниченный retry | `POST /ops/ingestion/runs/retry` | Header `X-Andromeda-Ops-Key`; body `{ "source": "bmstu_fixture" }` или allowlisted `bmstu_live` | `{run: IngestionRunDetailResponse}` | `retryIngestion(request, opsKey)` |

`IngestionRunDetailResponse` содержит status, timestamps, counts (`sourceCount`, `programCount`, `curriculumItemCount`, `eventCount`, `campusPointCount`), inserted/updated/unchanged/removed counts, safe error fields и `sourceHashes[]`/`sourceKinds[]`.

Ops key хранится только в памяти текущей страницы: operator вводит его в форме, после submit input очищается, а значение передаётся только заголовком этим трём endpoint-ам. Оно не должно попадать в URL, query, JSON, localStorage или логи.

При выключенном Ops API, отсутствии или неверном ключе backend намеренно возвращает `404 NOT_FOUND`, чтобы не раскрывать наличие operator surface. Retry не принимает URL, shell-команду, raw payload или произвольный program ID.

## 7. Основные response-модели

### 7.1. Program и curriculum

| Модель | Поля |
|---|---|
| `ProgramSummaryResponse` | `id`, `directionId`, `code`, `name`, `educationYear`, `studyPlanUrl`, `sourceUrl` |
| `ProgramResponse` | `program: ProgramSummaryResponse` |
| `CurriculumResponse` | `program`, `curriculumId`, `educationYear`, `sourceUrl`, `capturedAt`, `items[]` |
| `CurriculumItemResponse` | `id`, `discipline`, `sourceName`, `hours`; optional/null `semester`, `credits`, `assessmentTypes`, `sourcePosition` |
| `DisciplineResponse` | `id`, исходное `name`, `normalizedName`, `areaWeights[]`, `primaryArea` |
| `DisciplineAreaResponse` | `code`, `name`, `description`, `weight` |

`sourceName` и `discipline.name` сохраняют исходные названия дисциплин. `areaWeights` может содержать несколько областей для междисциплинарной дисциплины; каждая weight положительна, а сумма нормализована backend-ом до 1.0000. Frontend показывает discipline data, но не выполняет runtime classification.

### 7.2. Даты, decimal и `null`

| Формат | Правило |
|---|---|
| ISO datetime | `capturedAt`, `createdAt`, `updatedAt`, `expiresAt`, `startsAt`, `endsAt`, `from`, `to` передаются с timezone, например `2026-09-15T10:00:00Z`. |
| Decimal | Суммы, credits, баллы admissions и веса часто приходят JSON-строками, например `"12.5000"`; frontend не должен предполагать JavaScript number без явного форматирования. |
| `null` | Факт отсутствует или неприменим: например, `PassingScoreResponse.score` для БВИ, `venue` у online event, `semester` для непозиционированной дисциплины. |
| Пустой массив | Нет элементов в этом срезе: `items: []`, `recommendations: []`, `eventsWithoutPoint: []`; это не то же самое, что transport error. |

### 7.3. Provenance

В каталоговых и admissions-моделях provenance подтверждает, откуда взят факт. Типичный набор:

| Поле | Для чего нужно |
|---|---|
| `sourceKind`/`kind` | Тип официального источника или adapter source. |
| `sourceUrl`/`url` | Ссылка, которую можно открыть для проверки. |
| `capturedAt` | Когда источник был снят ingestion-ом. |
| `contentSha256` | Hash конкретного содержимого, чтобы повторный ingestion можно было сравнить детерминированно. |
| `locator` | Необязательная позиция: строка, таблица, секция, detail page или иной locator. |
| `sourceName` | Человекочитаемое имя источника, если опубликовано. |

Frontend отображает ссылку и source name, но не пытается повторно скачивать источник для построения UI.

## 8. Ошибки и состояния UI

### 8.1. Единый error contract

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [
    {
      "path": "applicant.scores.0.score",
      "message": "Input should be less than or equal to 100",
      "type": "less_than_equal"
    }
  ]
}
```

| `ErrorResponse.code` | Когда встречается | Ожидаемая реакция frontend |
|---|---|---|
| `VALIDATION_ERROR` | Неверный path/query/body, enum, score, limit, format или Origin | Показать понятное сообщение около формы/фильтра, сохранить возможность повторить после исправления. |
| `UNAUTHORIZED` | Auth-required операция без валидной auth session | Показать login/account guidance; не показывать stack trace. |
| `NOT_FOUND` | Неизвестный canonical ID, отсутствующий profile, run или выключенный Ops API | Различить resource-not-found и profile-required там, где feature знает контекст. |
| `CONFLICT` | Duplicate profile, stale `expectedRevision`, параллельный retry или другой конфликт состояния | Попросить обновить состояние/повторить с актуальной revision. |
| `SOURCE_CONTRACT_ERROR` | Backend/source adapter не смог подтвердить внешний contract | Показать source gap/error state, не подставлять нули или догадки. |
| `CONTRACT_ERROR` | Несогласованность внутреннего typed contract | Зафиксировать как backend/API issue; не маскировать пустым успешным ответом. |
| `INTERNAL_ERROR` | Непредвиденная server-side ошибка | Показать безопасное общее сообщение и возможность retry. |

`ErrorDetail` всегда имеет `path`, `message`, `type`. Массив `details` может быть пустым. Backend может использовать HTTP `400`, `401`, `404`, `409`, `422` или `500` в зависимости от причины; UI должен ориентироваться и на HTTP status, и на `payload.code`.

### 8.2. Ошибки транспортного слоя

| Ситуация | Что выбрасывает client | Практический смысл |
|---|---|---|
| Ответ `2xx` | Typed payload | Feature продолжает рендеринг. |
| Ответ не `2xx` с валидным `ErrorResponse` | `ApiError(status, payload)` | Можно безопасно использовать `status`, `payload.code`, `payload.message`, `payload.details`. |
| Ответ не `2xx` без ErrorResponse | Обычный `Error` | Контракт ответа сервера нарушен или body не JSON. |
| Timeout после 45 секунд | `ApiTimeoutError(path, timeoutMs)` | Показать retry/network state. |
| Network/CORS/DNS failure | Обычный runtime error | Проверить backend, `VITE_API_BASE_URL`, CORS и доступность порта. |
| Пользователь покинул страницу/abort | Abort error | Не превращать отмену пользователем в timeout; текущие public wrappers собственный `AbortSignal` не принимают. |

Стартовый `main.ts` при ошибке `GET /programs` показывает contract error и подсказывает проверить backend/заполненную базу. Остальные features имеют локальные loading, error, empty и profile-required states; зависший infinite loading не является ожидаемым способом обработки ошибки.

## 9. Что frontend делает с ответами

| Экран | Последовательность API-вызовов | Результат |
|---|---|---|
| Catalog | `GET /programs` один раз при старте | Локальный поиск по `code`, `name`, `directionId`; фильтры по `educationYear` и направлению. |
| Program | `GET /programs/{id}` → параллельно `GET /curriculum` и `GET /admissions` | Заголовок, provenance, таблица дисциплин, admissions и форма Admission Fit. |
| Compare | `GET /compare` с двумя IDs | Таблица дисциплин, часов/кредитов и переключение full plan/semester. |
| Proftest | `GET /proftest/questions` → `POST /preview` при промежуточных ответах → `POST /results` на финише | Adaptive question flow, финальный profile и TOP recommendations. |
| Recommendations | `GET /proftest/profile` + `GET /recommendations/current` | Сохранённый профиль и объяснимый TOP ranking. |
| Events | `GET /events` с фильтрами; `GET /events/{id}` для detail | Список официальных событий, provenance, registration URL и venue. |
| Event detail | `GET /events/{id}` → при наличии venue `GET /campus/points/{id}` + `GET /campus/points/{id}/events` | Карточка события и связанная campus information. |
| Account | Параллельно `GET /auth/session`, `/proftest/profile`, `/recommendations/current`, `/personal-route` | Личный кабинет или корректные guest/profile-required states. |
| Personal Route | `GET /personal-route` | Логическая последовательность explore/compare/attend. |
| Ops | Ввод key → `GET /ops/ingestion/runs`; выбор run → detail; retry → повторный list | Контроль ingestion без выдачи raw snapshots и credentials. |

## 10. Синхронизация OpenAPI и generated TypeScript

Изменение public API выполняется в таком порядке:

```powershell
# из корня репозитория
python backend/scripts/export_openapi.py --out frontend/openapi.json

cd frontend
npm run generate-api
npm run check-api-drift
npm run test:unit
npm run build
```

| Файл/команда | Роль |
|---|---|
| `backend/src/andromeda/api/routes/*` | HTTP entry points и dependency wiring. |
| `backend/src/andromeda/api/schemas/*` | Pydantic request/response models. |
| `frontend/openapi.json` | Зафиксированный frontend-readable contract, полученный из backend. |
| `frontend/scripts/generate-api.mjs` | Генерация TypeScript declarations. |
| `frontend/src/api/generated.ts` | Generated `paths`/`components`; не редактировать вручную. |
| `frontend/src/api/client.ts` | Узкий набор typed wrappers и transport policy. |
| `npm run check-api-drift` | Проверяет, что generated artifact соответствует OpenAPI contract. |

Если меняется только документация, OpenAPI регенерировать не нужно. Если меняется endpoint, поле, enum, status code или validation rule, необходимо обновить backend schema, экспортировать OpenAPI, регенерировать `generated.ts` и пройти drift check.

## 11. Диагностика локального обмена

| Проверка | Команда/URL | Что подтверждает |
|---|---|---|
| Backend health | Открыть `http://127.0.0.1:8000/docs` | FastAPI запущен и публикует contract. |
| OpenAPI backend | `http://127.0.0.1:8000/openapi.json` | Runtime schema backend. |
| Frontend | `http://127.0.0.1:5173/` | Browser загрузил `GET /programs` и AppShell. |
| Offline drift | `OPENAPI_FILE=openapi.json npm run check-api-drift` из `frontend` | Локальный `openapi.json` и generated client не расходятся. |
| Full fixture smoke | `python backend/scripts/run_tracer_demo.py --mode fixture --check` из корня | SQLite fixture, FastAPI, Vite, OpenAPI и compare flow работают вместе. |

Во вкладке Network браузера для обычного пользовательского сценария должны быть видны JSON-запросы к этим public paths. Parser, PDF и database connection остаются backend-side и из браузера не доступны.

## See Also

- [Frontend README](README.md) — запуск Vite и fixture smoke.
- [Backend API overview](../docs/api.md) — backend routes и application boundaries.
- [Admission Fit contract](../docs/admission-fit.md) — отдельная модель оценки поступления.
