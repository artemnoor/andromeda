"""Seed definitions for the extensible first semantic taxonomy version."""

from __future__ import annotations

from andromeda.shared.contracts.versions import SEMANTIC_TAXONOMY_VERSION

from ..contracts.public import SemanticFeature, SemanticFeatureGroup, SemanticValueType

_SUBJECT_FEATURES = (
    ("mathematics", "Математика", "Математический аппарат и математические методы"),
    ("statistics", "Статистика", "Статистика, вероятность и количественный анализ"),
    ("programming", "Программирование", "Разработка программного обеспечения и алгоритмов"),
    ("computer_science", "Компьютерные науки", "Основы computer science и вычислительных систем"),
    ("data", "Данные", "Работа с данными, базами и data-процессами"),
    ("ai_ml", "AI и машинное обучение", "Искусственный интеллект и machine learning"),
    ("physics", "Физика", "Физические явления и модели"),
    ("engineering", "Инженерия", "Инженерные методы и проектирование систем"),
    ("business", "Бизнес", "Бизнес-процессы и предпринимательство"),
    ("management", "Менеджмент", "Управление организациями и командами"),
    ("economics", "Экономика", "Экономические модели и анализ"),
    ("finance", "Финансы", "Финансовые инструменты и управление финансами"),
    ("linguistics", "Лингвистика", "Язык и лингвистический анализ"),
    ("design", "Дизайн", "Проектирование визуальных и пользовательских решений"),
)
_ACTIVITY_FEATURES = (
    ("research", "Исследования", "Исследовательская и научная деятельность", SemanticFeatureGroup.ACTIVITY),
    ("analytics", "Аналитика", "Аналитическая деятельность и интерпретация данных", SemanticFeatureGroup.SKILL),
    ("theory", "Теория", "Теоретическая направленность обучения", SemanticFeatureGroup.LEARNING_STYLE),
    ("practice", "Практика", "Практическая направленность обучения", SemanticFeatureGroup.LEARNING_STYLE),
    ("project_work", "Проектная работа", "Проектная и командная работа", SemanticFeatureGroup.ACTIVITY),
    ("communication", "Коммуникация", "Коммуникационные и презентационные навыки", SemanticFeatureGroup.SKILL),
)


def _feature(code: str, name: str, description: str, group: SemanticFeatureGroup) -> SemanticFeature:
    return SemanticFeature(
        id=f"semantic-feature:{code}",
        code=code,
        name=name,
        description=description,
        feature_group=group,
        value_type=SemanticValueType.INTENSITY,
        semantic_version=SEMANTIC_TAXONOMY_VERSION,
    )


DEFAULT_SEMANTIC_FEATURES: tuple[SemanticFeature, ...] = tuple(
    _feature(code, name, description, SemanticFeatureGroup.SUBJECT)
    for code, name, description in _SUBJECT_FEATURES
) + tuple(_feature(*item) for item in _ACTIVITY_FEATURES)


__all__ = ["DEFAULT_SEMANTIC_FEATURES"]
