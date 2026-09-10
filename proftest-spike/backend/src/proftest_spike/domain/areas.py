"""Canonical area codes mirrored from the public Andromeda API contract.

The Spike intentionally reuses the existing string codes without importing the
main backend. Labels are kept here only as a presentation fallback for API
responses that do not include the optional area catalog.
"""

from __future__ import annotations

from enum import StrEnum


class AreaCode(StrEnum):
    MATHEMATICS_STATISTICS = "mathematics_statistics"
    COMPUTER_SCIENCE_DATA = "computer_science_data"
    PHYSICS_ASTRONOMY = "physics_astronomy"
    CHEMISTRY_MATERIALS = "chemistry_materials"
    BIOLOGY_BIOTECHNOLOGY = "biology_biotechnology"
    EARTH_ENVIRONMENT = "earth_environment"
    ENGINEERING_TECHNOLOGY = "engineering_technology"
    ARCHITECTURE_CONSTRUCTION = "architecture_construction"
    AGRICULTURE_VETERINARY = "agriculture_veterinary"
    MEDICINE_HEALTH = "medicine_health"
    PSYCHOLOGY_COGNITIVE = "psychology_cognitive"
    SOCIETY_SOCIAL_SCIENCES = "society_social_sciences"
    ECONOMICS_FINANCE = "economics_finance"
    BUSINESS_MANAGEMENT = "business_management"
    LAW_POLICY_PUBLIC_ADMINISTRATION = "law_policy_public_administration"
    LANGUAGES_LINGUISTICS_LITERATURE = "languages_linguistics_literature"
    HISTORY_PHILOSOPHY_HUMANITIES = "history_philosophy_humanities"
    ART_DESIGN_MEDIA = "art_design_media"
    EDUCATION_PEDAGOGY = "education_pedagogy"
    SPORT_TOURISM_HOSPITALITY = "sport_tourism_hospitality"
    SAFETY_DEFENSE_TRANSPORT = "safety_defense_transport"
    UNIVERSAL_INTERDISCIPLINARY = "universal_interdisciplinary"


AREA_ORDER: tuple[AreaCode, ...] = tuple(AreaCode)

AREA_LABELS: dict[AreaCode, str] = {
    AreaCode.MATHEMATICS_STATISTICS: "Математика и статистика",
    AreaCode.COMPUTER_SCIENCE_DATA: "Компьютерные науки и данные",
    AreaCode.PHYSICS_ASTRONOMY: "Физика и астрономия",
    AreaCode.CHEMISTRY_MATERIALS: "Химия и материаловедение",
    AreaCode.BIOLOGY_BIOTECHNOLOGY: "Биология и биотехнологии",
    AreaCode.EARTH_ENVIRONMENT: "Земля, экология и окружающая среда",
    AreaCode.ENGINEERING_TECHNOLOGY: "Инженерия и технологии",
    AreaCode.ARCHITECTURE_CONSTRUCTION: "Архитектура, строительство и урбанистика",
    AreaCode.AGRICULTURE_VETERINARY: "Сельское хозяйство и ветеринария",
    AreaCode.MEDICINE_HEALTH: "Медицина и здоровье",
    AreaCode.PSYCHOLOGY_COGNITIVE: "Психология и когнитивные науки",
    AreaCode.SOCIETY_SOCIAL_SCIENCES: "Общество и социальные науки",
    AreaCode.ECONOMICS_FINANCE: "Экономика и финансы",
    AreaCode.BUSINESS_MANAGEMENT: "Бизнес, управление и предпринимательство",
    AreaCode.LAW_POLICY_PUBLIC_ADMINISTRATION: "Право, политика и государственное управление",
    AreaCode.LANGUAGES_LINGUISTICS_LITERATURE: "Языки, лингвистика и литература",
    AreaCode.HISTORY_PHILOSOPHY_HUMANITIES: "История, философия и гуманитарные науки",
    AreaCode.ART_DESIGN_MEDIA: "Искусство, дизайн, медиа и коммуникации",
    AreaCode.EDUCATION_PEDAGOGY: "Образование и педагогика",
    AreaCode.SPORT_TOURISM_HOSPITALITY: "Спорт, туризм и индустрия гостеприимства",
    AreaCode.SAFETY_DEFENSE_TRANSPORT: "Безопасность, оборона и транспортные системы",
    AreaCode.UNIVERSAL_INTERDISCIPLINARY: "Универсальные и междисциплинарные дисциплины",
}


def area_label(code: AreaCode) -> str:
    """Return a stable Russian label for a canonical area code."""

    return AREA_LABELS[code]


__all__ = ["AREA_LABELS", "AREA_ORDER", "AreaCode", "area_label"]
