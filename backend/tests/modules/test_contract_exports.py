from __future__ import annotations

from andromeda.modules.curricula.contracts.public import Curriculum, CurriculumItem
from andromeda.modules.disciplines.contracts.public import Discipline
from andromeda.modules.programs.contracts.public import Program
from andromeda.modules.universities.contracts.public import Direction, University


def test_subject_modules_expose_typed_public_contracts() -> None:
    assert all(cls.model_config["extra"] == "forbid" for cls in (University, Direction, Program, Curriculum, CurriculumItem, Discipline))
