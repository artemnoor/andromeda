from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from andromeda.modules.curricula.contracts.public import Curriculum, CurriculumItem
from andromeda.modules.curricula.repository.ports import CurriculumReader, CurriculumWriter
from andromeda.shared.contracts.enums import AssessmentType
from andromeda.shared.contracts.errors import ContractError, ErrorCode
from andromeda.shared.contracts.ids import ProgramId

from ..database.models import AssessmentTypeModel, CurriculumItemAssessmentModel, CurriculumItemModel, CurriculumModel


class SqlAlchemyCurriculumRepository(CurriculumReader, CurriculumWriter):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_for_program(self, program_id: ProgramId) -> Curriculum | None:
        model = self._session.execute(
            select(CurriculumModel).where(CurriculumModel.program_id == program_id).order_by(CurriculumModel.education_year.desc())
        ).scalars().first()
        if model is None:
            return None
        items = self._session.execute(
            select(CurriculumItemModel)
            .where(CurriculumItemModel.curriculum_id == model.id)
            .order_by(CurriculumItemModel.semester.is_(None), CurriculumItemModel.semester, CurriculumItemModel.source_position, CurriculumItemModel.source_name)
        ).scalars().all()
        return Curriculum.model_validate(
            {
                "id": model.id,
                "program_id": model.program_id,
                "education_year": model.education_year,
                "source_url": model.source_url,
                "captured_at": model.captured_at,
                "items": tuple(self._to_item(item) for item in items),
            }
        )

    def save(self, curriculum: Curriculum) -> None:
        existing = self._session.get(CurriculumModel, curriculum.id)
        values = {
            "id": curriculum.id,
            "program_id": curriculum.program_id,
            "education_year": curriculum.education_year,
            "source_url": str(curriculum.source_url),
            "captured_at": curriculum.captured_at,
        }
        if existing is None:
            self._session.add(CurriculumModel(**values))
        elif any(getattr(existing, key) != value for key, value in values.items() if key != "id"):
            raise ValueError(f"curriculum identity conflict: {curriculum.id}")

    def _to_item(self, model: CurriculumItemModel) -> CurriculumItem:
        assessment_rows = self._session.execute(
            select(CurriculumItemAssessmentModel).where(CurriculumItemAssessmentModel.curriculum_item_id == model.id)
        ).scalars().all()
        try:
            assessments = tuple(AssessmentType(row.assessment_type_id) for row in assessment_rows)
        except ValueError as exc:
            raise ContractError(ErrorCode.CONTRACT_ERROR, "Persisted assessment type is not canonical") from exc
        return CurriculumItem.model_validate(
            {
                "id": model.id,
                "discipline_id": model.discipline_id,
                "source_name": model.source_name,
                "semester": model.semester,
                "hours": model.hours,
                "credits": model.credits,
                "assessment_types": assessments or None,
                "subject_group": model.subject_group,
                "source_position": model.source_position,
            }
        )
