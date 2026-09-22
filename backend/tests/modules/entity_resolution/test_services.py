from __future__ import annotations

from hashlib import sha256

from andromeda.modules.disciplines.contracts.public import Discipline
from andromeda.modules.disciplines.domain.areas import default_area_weights
from andromeda.modules.entity_resolution.contracts.public import (
    ResolutionEntityType,
    ResolutionContext,
    ResolutionStatus,
)
from andromeda.modules.entity_resolution.contracts.hierarchical import SelectionResult
from andromeda.modules.entity_resolution.services.resolvers import (
    CachedEntityCatalog,
    DirectionResolverService,
    DisciplineResolverService,
    MetricResolverService,
    ProgramResolverService,
    EntityResolverService,
    UniversityResolverService,
)
from andromeda.modules.entity_resolution.services.hierarchical import (
    HierarchicalResolutionService,
    compute_candidate_hash,
)
from andromeda.modules.programs.contracts.public import Program
from andromeda.modules.universities.contracts.public import Direction, University
from andromeda.shared.contracts.enums import EducationLevel


def _university(university_id: str, name: str) -> University:
    return University(
        id=university_id,
        name=name,
        city="Москва",
        official_site="https://example.com",
        address="ул. Тестовая, 1",
    )


def _direction(university_id: str, code: str, name: str) -> Direction:
    slug = university_id.removeprefix("university:")
    return Direction(
        id=f"direction:{slug}:{code}",
        university_id=university_id,
        code=code,
        name=name,
        education_level=EducationLevel.BACHELOR,
    )


def _program(direction: Direction, suffix: str, name: str) -> Program:
    return Program(
        id=f"program:{direction.university_id.removeprefix('university:')}:{direction.code}-{suffix}",
        direction_id=direction.id,
        code=f"{direction.code}-{suffix}",
        name=name,
        education_year=2025,
        study_plan_url="https://example.com/plan",
        source_url="https://example.com/source",
    )


class _Catalog:
    def __init__(self) -> None:
        bmstu = _university("university:bmstu", "МГТУ им. Н. Э. Баумана")
        hse = _university("university:hse", "Национальный исследовательский университет")
        pi_bmstu = _direction("university:bmstu", "09.03.03", "Прикладная информатика")
        pi_hse = _direction("university:hse", "09.03.03", "Прикладная информатика")
        ivt = _direction("university:bmstu", "09.03.01", "Информатика и вычислительная техника")
        self.universities = (bmstu, hse)
        self.directions = (pi_bmstu, pi_hse, ivt)
        self.programs = (
            _program(pi_bmstu, "01", "Прикладная информатика"),
            _program(ivt, "02", "Информатика и вычислительная техника"),
        )
        normalized = "математический анализ"
        self.disciplines = (
            Discipline(
                id=f"discipline:{sha256(normalized.encode()).hexdigest()[:16]}",
                name="Математический анализ",
                normalized_name=normalized,
                area_weights=default_area_weights(),
            ),
        )
        self.calls = {"universities": 0, "directions": 0, "programs": 0, "disciplines": 0}

    def list_universities(self):
        self.calls["universities"] += 1
        return self.universities

    def list_directions(self):
        self.calls["directions"] += 1
        return self.directions

    def list_programs(self):
        self.calls["programs"] += 1
        return self.programs

    def list_disciplines(self):
        self.calls["disciplines"] += 1
        return self.disciplines


def test_resolvers_support_aliases_context_and_explicit_ambiguity() -> None:
    source = _Catalog()
    catalog = CachedEntityCatalog(source)

    university = UniversityResolverService(catalog).resolve("Бауманка")
    assert university.status is ResolutionStatus.RESOLVED
    assert university.selected_id == "university:bmstu"

    ambiguous = DirectionResolverService(catalog).resolve("09.03.03")
    assert ambiguous.status is ResolutionStatus.AMBIGUOUS
    scoped = DirectionResolverService(catalog).resolve(
        "ПИ",
        context=ResolutionContext(university_id="university:bmstu"),
    )
    assert scoped.selected_id == "direction:bmstu:09.03.03"

    program = ProgramResolverService(catalog).resolve(
        "Прикладная информатика",
        context=ResolutionContext(direction_id="direction:bmstu:09.03.03"),
    )
    assert program.status is ResolutionStatus.RESOLVED
    assert program.selected_id == "program:bmstu:09.03.03-01"


def test_catalog_is_cached_and_metric_and_discipline_aliases_are_shared() -> None:
    source = _Catalog()
    catalog = CachedEntityCatalog(source)
    UniversityResolverService(catalog).resolve("МГТУ")
    DirectionResolverService(catalog).resolve("09.03.01")
    DisciplineResolverService(catalog).resolve("матан")
    assert source.calls == {"universities": 1, "directions": 1, "programs": 1, "disciplines": 1}

    metric = MetricResolverService().resolve("матан")
    assert metric.status is ResolutionStatus.RESOLVED
    assert metric.selected_id == "metric:math_share"


def test_entity_resolver_invokes_hierarchical_port_only_above_threshold() -> None:
    source = _Catalog()
    direction = source.directions[0]
    source.programs = tuple(_program(direction, f"{index:03d}", f"Программа {index}") for index in range(1, 257))

    class Port:
        calls = 0

        def select(self, request):
            self.calls += 1
            selected_id = request.candidates[-1].canonical_id
            return SelectionResult(
                status=ResolutionStatus.RESOLVED,
                selected_id=selected_id,
                candidate_ids=tuple(item.canonical_id for item in request.candidates),
                strategy="test-jevtree",
                candidate_hash=compute_candidate_hash(request.candidates),
            )

    port = Port()
    resolver = EntityResolverService(
        CachedEntityCatalog(source),
        hierarchical=HierarchicalResolutionService(port, candidate_threshold=255),
    )

    result = resolver.resolve(ResolutionEntityType.PROGRAM, "Программа", limit=3)

    assert port.calls == 1
    assert result.selected_id == "program:bmstu:09.03.03-256"
    assert len(result.candidates) == 3


def test_entity_resolver_bypasses_hierarchical_port_for_small_set() -> None:
    source = _Catalog()

    class Port:
        calls = 0

        def select(self, request):
            self.calls += 1
            raise AssertionError("small candidate set must not reach jev-tree")

    port = Port()
    resolver = EntityResolverService(
        CachedEntityCatalog(source),
        hierarchical=HierarchicalResolutionService(port, candidate_threshold=255),
    )

    resolver.resolve(ResolutionEntityType.PROGRAM, "Прикладная информатика")

    assert port.calls == 0
