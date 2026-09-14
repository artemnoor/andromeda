from __future__ import annotations

from decimal import Decimal

from andromeda.ingestion.universities.bmstu.mappings.discipline_areas import BMSTU_DISCIPLINE_AREA_OVERRIDES
from andromeda.modules.disciplines.domain.areas import DisciplineAreaCode
from andromeda.modules.disciplines.services.classifier import RuleBasedDisciplineClassifier


def test_bmstu_classification_vectors_are_positive_and_sum_to_one() -> None:
    classifier = RuleBasedDisciplineClassifier(BMSTU_DISCIPLINE_AREA_OVERRIDES)
    names = (
        "Дискретная математика",
        "Технологии искусственного интеллекта",
        "История России",
        "Основы эффективной коммуникации и конфликтологии",
        "Ознакомительная практика",
    )

    for name in names:
        weights = classifier.classify(name)
        assert weights
        assert all(weight.weight > Decimal("0") for weight in weights)
        assert sum((weight.weight for weight in weights), Decimal("0")) == Decimal("1.0000")


def test_bmstu_classification_is_deterministic_and_keeps_multidisciplinary_signal() -> None:
    classifier = RuleBasedDisciplineClassifier(BMSTU_DISCIPLINE_AREA_OVERRIDES)
    name = "Основы эффективной коммуникации и конфликтологии"

    first = classifier.classify(name)
    second = classifier.classify(name)
    assert first == second
    assert {weight.area for weight in first} == {
        DisciplineAreaCode.PSYCHOLOGY_COGNITIVE,
        DisciplineAreaCode.SOCIETY_SOCIAL_SCIENCES,
        DisciplineAreaCode.UNIVERSAL_INTERDISCIPLINARY,
    }
