from __future__ import annotations

from decimal import Decimal

from andromeda.modules.disciplines.domain.areas import DisciplineAreaCode, area_catalog
from andromeda.modules.disciplines.services.classifier import RuleBasedDisciplineClassifier


def _as_dict(name: str) -> dict[DisciplineAreaCode, Decimal]:
    return {item.area: item.weight for item in RuleBasedDisciplineClassifier().classify(name)}


def test_taxonomy_has_exactly_22_ordered_areas() -> None:
    areas = area_catalog()
    assert len(areas) == 22
    assert [area.position for area in areas] == list(range(1, 23))
    assert len({area.code for area in areas}) == 22


def test_classifier_preserves_multidisciplinary_vectors() -> None:
    machine_learning = _as_dict("Машинное обучение")
    assert machine_learning[DisciplineAreaCode.COMPUTER_SCIENCE_DATA] == Decimal("0.75")
    assert machine_learning[DisciplineAreaCode.MATHEMATICS_STATISTICS] == Decimal("0.25")

    bioinformatics = _as_dict("Биоинформатика")
    assert bioinformatics == {
        DisciplineAreaCode.BIOLOGY_BIOTECHNOLOGY: Decimal("0.50"),
        DisciplineAreaCode.COMPUTER_SCIENCE_DATA: Decimal("0.40"),
        DisciplineAreaCode.MATHEMATICS_STATISTICS: Decimal("0.10"),
    }


def test_classifier_falls_back_to_universal_without_false_precision() -> None:
    result = RuleBasedDisciplineClassifier().classify("Неизвестный предмет")
    assert result[0].area is DisciplineAreaCode.UNIVERSAL_INTERDISCIPLINARY
    assert result[0].weight == Decimal("1.0000")
