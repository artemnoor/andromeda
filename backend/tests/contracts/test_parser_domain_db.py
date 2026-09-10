from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from bmstu_parser.db.models import CurriculumItemModel, DisciplineModel


def test_parser_output_is_typed_and_persisted(parsed_bundle: tuple[object, object], ingested_db: tuple[str, object, object]) -> None:
    raw, normalized = parsed_bundle
    assert all(hasattr(row, "model_dump") for row in raw.curriculum_rows)  # type: ignore[attr-defined]
    assert all(item.hours >= 0 for curriculum in normalized.curricula for item in curriculum.items)  # type: ignore[attr-defined]

    database_url, _, _ = ingested_db
    from bmstu_parser.db.base import create_engine_for_url

    engine = create_engine_for_url(database_url)
    with Session(engine) as session:
        assert session.scalar(select(DisciplineModel.id)) is not None
        assert session.scalar(select(CurriculumItemModel.id)) is not None
