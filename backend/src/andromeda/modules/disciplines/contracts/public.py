"""Public discipline contract; source name remains on curriculum items."""

from ..domain.areas import DisciplineAreaCode, DisciplineAreaDefinition, DisciplineAreaSummary, DisciplineAreaWeight, area_catalog, area_definition, area_position
from ..domain.entities import Discipline

__all__ = [
    "Discipline",
    "DisciplineAreaCode",
    "DisciplineAreaDefinition",
    "DisciplineAreaSummary",
    "DisciplineAreaWeight",
    "area_catalog",
    "area_definition",
    "area_position",
]
