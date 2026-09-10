from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bmstu_parser.db.base import Base, create_engine_for_url
from bmstu_parser.db.models import CurriculumItemModel


def test_database_enforces_foreign_key_and_check_constraints() -> None:
    engine = create_engine_for_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(CurriculumItemModel(id="bad", curriculum_id="missing", discipline_id="missing", semester=0, hours=-1))
        with pytest.raises(IntegrityError):
            session.flush()
