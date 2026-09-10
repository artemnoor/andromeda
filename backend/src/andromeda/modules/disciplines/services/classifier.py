from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Protocol

from ..domain.areas import AreaVector, DisciplineAreaCode, DisciplineAreaWeight, area_vector, default_area_weights
from ..domain.identity import normalize_discipline_name


logger = logging.getLogger("andromeda.disciplines.classifier")


class DisciplineClassifier(Protocol):
    def classify(self, source_name: str) -> tuple[DisciplineAreaWeight, ...]: ...


class RuleBasedDisciplineClassifier:
    """Classify subject content into the Andromeda multi-area taxonomy.

    The classifier is deliberately transparent and conservative. Source-owned
    mappings may provide an exact vector; generic keyword rules are only a
    fallback for a new university or a newly encountered subject.
    """

    def __init__(self, overrides: Mapping[str, AreaVector] | None = None) -> None:
        self._overrides = dict(overrides or {})

    def classify(self, source_name: str) -> tuple[DisciplineAreaWeight, ...]:
        normalized_name = normalize_discipline_name(source_name)
        vector = self._overrides.get(normalized_name)
        if vector is None:
            vector = self._classify_by_rules(normalized_name)
        if vector is None:
            logger.debug("discipline_classification_fallback area=%s", DisciplineAreaCode.UNIVERSAL_INTERDISCIPLINARY.value)
            return default_area_weights()
        return tuple(DisciplineAreaWeight(area=area, weight=weight) for area, weight in vector)

    @staticmethod
    def _classify_by_rules(normalized_name: str) -> AreaVector | None:
        for keywords, vector in _DEFAULT_RULES:
            if any(keyword in normalized_name for keyword in keywords):
                return vector
        return None


_DEFAULT_RULES: tuple[tuple[tuple[str, ...], AreaVector], ...] = (
    (("биоинформ",), area_vector((DisciplineAreaCode.BIOLOGY_BIOTECHNOLOGY, "0.50"), (DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.40"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.10"))),
    (("эконометр",), area_vector((DisciplineAreaCode.ECONOMICS_FINANCE, "0.55"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.45"))),
    (("машинн", "нейросет", "искусственн интеллект", "глубок обуч"), area_vector((DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.75"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.25"))),
    (("естественн язык", "лингвистическ технолог"), area_vector((DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.65"), (DisciplineAreaCode.LANGUAGES_LINGUISTICS_LITERATURE, "0.25"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.10"))),
    (("ux", "эргоном", "человеко-машин", "конфликтолог"), area_vector((DisciplineAreaCode.PSYCHOLOGY_COGNITIVE, "0.45"), (DisciplineAreaCode.ART_DESIGN_MEDIA, "0.30"), (DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.25"))),
    (("веб-разработ", "web", "программирован", "алгоритм", "информационн систем", "баз данн", "операционн систем", "телекоммуникац", "кибербезопас", "информационн безопас", "данн", "информатик", "нейросет", "робототех"), area_vector((DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.75"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.15"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.10"))),
    (("математ", "алгебр", "геометр", "статист", "вероятност", "оптимизац", "исследовани операц", "дифференциальн уравнен"), area_vector((DisciplineAreaCode.MATHEMATICS_STATISTICS, "1.00"))),
    (("физик", "астроном", "оптик", "квантов", "механик"), area_vector((DisciplineAreaCode.PHYSICS_ASTRONOMY, "0.65"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.35"))),
    (("хими", "материаловед", "полимер"), area_vector((DisciplineAreaCode.CHEMISTRY_MATERIALS, "1.00"))),
    (("биолог", "биотехнолог", "генетик", "микробиолог", "биохими"), area_vector((DisciplineAreaCode.BIOLOGY_BIOTECHNOLOGY, "1.00"))),
    (("геолог", "географ", "эколог", "климат", "океанолог", "гидролог", "природопользован"), area_vector((DisciplineAreaCode.EARTH_ENVIRONMENT, "1.00"))),
    (("архитектур", "строительств", "градостро", "урбанист", "bim", "здан"), area_vector((DisciplineAreaCode.ARCHITECTURE_CONSTRUCTION, "1.00"))),
    (("агроном", "сельск", "ветеринар", "лесн хозяйств", "животновод"), area_vector((DisciplineAreaCode.AGRICULTURE_VETERINARY, "1.00"))),
    (("медицин", "медиц", "стоматолог", "фармац", "сестрин", "реабилитац", "общественн здоров"), area_vector((DisciplineAreaCode.MEDICINE_HEALTH, "1.00"))),
    (("психолог", "когнитив", "психодиагност"), area_vector((DisciplineAreaCode.PSYCHOLOGY_COGNITIVE, "1.00"))),
    (("социолог", "антрополог", "демограф", "этнограф", "социальн работ"), area_vector((DisciplineAreaCode.SOCIETY_SOCIAL_SCIENCES, "1.00"))),
    (("эконом", "финанс", "инвестиц", "банк", "миров эконом"), area_vector((DisciplineAreaCode.ECONOMICS_FINANCE, "0.80"), (DisciplineAreaCode.BUSINESS_MANAGEMENT, "0.20"))),
    (("менеджмент", "маркетинг", "бухгалтер", "управлен", "предприним", "бизнес-процесс", "hr"), area_vector((DisciplineAreaCode.BUSINESS_MANAGEMENT, "1.00"))),
    (("прав", "юридичес", "политолог", "государственн управлен", "дипломат", "международн отношен"), area_vector((DisciplineAreaCode.LAW_POLICY_PUBLIC_ADMINISTRATION, "1.00"))),
    (("язык", "лингвист", "перевод", "филолог", "литератур", "фонетик", "морфолог", "синтаксис"), area_vector((DisciplineAreaCode.LANGUAGES_LINGUISTICS_LITERATURE, "1.00"))),
    (("истори", "археолог", "философ", "этик", "религиовед", "культуролог"), area_vector((DisciplineAreaCode.HISTORY_PHILOSOPHY_HUMANITIES, "1.00"))),
    (("искусств", "дизайн", "медиа", "мультимед", "журналист", "реклам", "музык", "театр", "кино"), area_vector((DisciplineAreaCode.ART_DESIGN_MEDIA, "1.00"))),
    (("педагог", "образовательн", "преподаван", "методик обуч"), area_vector((DisciplineAreaCode.EDUCATION_PEDAGOGY, "1.00"))),
    (("физическ культур", "спорт", "туризм", "гостинич", "ресторан"), area_vector((DisciplineAreaCode.SPORT_TOURISM_HOSPITALITY, "1.00"))),
    (("безопасност", "оборона", "пожарн", "транспорт", "навигац", "защит насел"), area_vector((DisciplineAreaCode.SAFETY_DEFENSE_TRANSPORT, "1.00"))),
    (("практик", "введение в специальност", "проектн деятельност", "академическ", "исследовательск", "вкр", "карьерн"), area_vector((DisciplineAreaCode.UNIVERSAL_INTERDISCIPLINARY, "1.00"))),
)


__all__ = ["DisciplineClassifier", "RuleBasedDisciplineClassifier"]
