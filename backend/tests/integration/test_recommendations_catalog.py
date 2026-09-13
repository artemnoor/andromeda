from __future__ import annotations

from pathlib import Path
from decimal import Decimal

from andromeda.infrastructure.database import Base, create_engine_for_url
from andromeda.infrastructure.repositories.curricula import SqlAlchemyCurriculumRepository
from andromeda.infrastructure.repositories.disciplines import SqlAlchemyDisciplineRepository
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository
from andromeda.infrastructure.repositories.programs import SqlAlchemyProgramRepository
from andromeda.infrastructure.repositories.proftest import SqlAlchemyProftestCatalogRepository
from andromeda.infrastructure.repositories.recommendations import CatalogRecommendationRepository
from andromeda.ingestion.universities.bmstu import BmstuUniversityAdapter
from andromeda.modules.disciplines.contracts.public import DisciplineAreaCode
from andromeda.modules.proftest.services.catalog import ProftestCatalogService
from andromeda.modules.proftest.contracts.public import Confidence
from andromeda.modules.recommendations.contracts.public import RecommendationRequest, UserProfile
from andromeda.modules.recommendations.services.recommendations import RecommendationService


def test_db_catalog_adapter_feeds_recommendation_service(tmp_path: Path) -> None:
    adapter = BmstuUniversityAdapter()
    try:
        raw, canonical = adapter.parse_sources(fixture_dir=Path(__file__).parents[1] / "fixtures" / "tracer" / "raw")
    finally:
        adapter.close()
    engine = create_engine_for_url(f"sqlite:///{(tmp_path / 'recommendations.db').as_posix()}")
    Base.metadata.create_all(engine)
    SqlAlchemyIngestionRepository(engine).ingest(raw, canonical)
    from sqlalchemy.orm import Session

    with engine.begin() as connection:
        catalog_reader = SqlAlchemyProftestCatalogRepository(
            SqlAlchemyProgramRepository(Session(bind=connection)),
            SqlAlchemyCurriculumRepository(Session(bind=connection)),
            SqlAlchemyDisciplineRepository(Session(bind=connection)),
        )
        catalog = ProftestCatalogService(catalog_reader)
        reader = CatalogRecommendationRepository(catalog)
        fingerprints = reader.list_fingerprints()

    assert len(fingerprints) == 2
    result = RecommendationService(reader).recommend_from_fingerprints(
        RecommendationRequest(
            profile=UserProfile(
                preferred_subject_weights={DisciplineAreaCode.COMPUTER_SCIENCE_DATA: Decimal("1")},
                confidence=Confidence(value=Decimal("1"), answered_base=6, answered_adaptive=0),
            ),
            limit=2,
        ),
        fingerprints,
    )
    assert len(result.recommendations) == 2
    assert all(item.score.program_code == item.program_code for item in result.recommendations)
