# Правила Andromeda

Это hard rules для разработки и AI-агентов. Если новый запрос требует исключения, сначала зафиксируй архитектурное решение; не выводи исключение молча из удобства реализации.

## Архитектура и границы

1. Andromeda остаётся modular monolith: один backend и общая infrastructure boundary. Microservices, Kafka, CQRS и отдельные deployment units не вводятся без отдельного решения.
2. Subject module в `backend/src/andromeda/modules/<module>` использует слои `domain`, `contracts`, `services`, `repository`. Domain хранит предметные типы и policy, contracts — typed inputs/outputs/public surface, services — use cases, repository — Protocol ports и module-local persistence abstractions.
3. Module A взаимодействует с module B только через `B.contracts.public` или `B.repository.ports`. Импорты `B.domain.*`, `B.services.*`, concrete `B.repository.*` и private files запрещены. `api`, `composition`, `infrastructure` и university-specific ingestion могут wiring concrete implementations на своих adapter boundaries.
4. Три legacy compatibility facades в `modules/proftest/services/{ranking,matching,explanations}.py` — точечные переходные aliases для старых import paths. Они не являются новым business interaction; их exact allowlist поддерживается architecture test. Новые обходы через facade запрещены.
5. ORM, SQLAlchemy `Session`, models и database-specific code находятся только в `andromeda.infrastructure`. Subject modules не импортируют `andromeda.api`, `andromeda.infrastructure`, SQLAlchemy или legacy parser package.

## Данные и университеты

6. Используй существующие canonical IDs и не дублируй `UniversityId`, `DepartmentId`, `ProgramId`, `VenueId` или другие shared identity types. Публичные данные и `UserProfile` — typed contracts; storage metadata не проникает в domain contract.
7. University-specific URL, selectors, parser, mappings, fixtures and normalizers находятся только в `ingestion/universities/<university>`. Новый вуз = новый adapter, а не условная ветка BMSTU в core module; adapter зависит от core contracts, а subject modules не импортируют ingestion.
8. Raw source snapshots сохраняют provenance и не подменяются догадками или нулевыми значениями. Canonical projection обновляется атомарно; не ломай существующие migration invariants.

## Product dimensions

9. `Content Fit` оценивает соответствие интересов структуре учебной программы. `Admission Fit` оценивает реалистичность поступления по admissions facts. `Career Fit` и `Workload Readiness` остаются отдельными dimensions. Не смешивай их модели, score, reasons, request или ranking.
10. Admission Fit не изменяет Content Fit/ranking и не принимает `UserProfile` как скрытую замену своему applicant contract.

## API, migrations и generated code

11. Business logic не размещается в API routes или transport schemas. API вызывает application service через composition/dependency wiring и возвращает typed result.
12. Alembic migrations линейны, безопасны для upgrade/downgrade в поддерживаемых targets и не переписывают опубликованную историю. Проверяй migration head и database constraints после изменения schema.
13. OpenAPI и generated frontend clients синхронны. При изменении public contract обновляй generated artifact по существующему workflow и проверяй drift; docs-only/internal changes не требуют регенерации.
14. Events/campus spatial data остаются map-agnostic: API может отдавать point identity/type/address/optional coordinates, relations, events и card fields, но не определяет визуальную раскладку, маршруты или библиотеку карты.

## Workflow и качество

15. До edits прочитай `AGENTS.md`, DESCRIPTION, RULES, relevant architecture docs/tests и текущий code path. Сначала переиспользуй существующий contract/module.
16. Не меняй scope, main history или пользовательские файлы без запроса. Не используй force-push, destructive reset/delete или rebase опубликованной ветки.
17. После изменений запускай релевантные unit/integration/architecture tests, typing/build и `git diff --check`; для API/contract changes проверяй OpenAPI/generated clients. Failing CI нельзя скрывать ослаблением checks.
18. Логи и отчёты не содержат secrets, tokens, cookies, raw database URLs или полные профили пользователей. Для ошибок используй safe IDs/counts и существующий logging policy.
