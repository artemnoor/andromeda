from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from andromeda.modules.disciplines.contracts.public import Discipline
from andromeda.modules.disciplines.repository.ports import DisciplineReader, DisciplineWriter
from andromeda.shared.contracts.ids import DisciplineId

from ..database.models import DisciplineModel


class SqlAlchemyDisciplineRepository(DisciplineReader, DisciplineWriter):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, discipline_id: DisciplineId) -> Discipline | None:
        model = self._session.get(DisciplineModel, discipline_id)
        return _to_contract(model) if model is not None else None

    def list(self) -> tuple[Discipline, ...]:
        models = self._session.execute(select(DisciplineModel).order_by(DisciplineModel.normalized_name)).scalars().all()
        return tuple(_to_contract(model) for model in models)

    def save(self, discipline: Discipline) -> None:
        existing = self._session.get(DisciplineModel, discipline.id)
        values = {"id": discipline.id, "name": discipline.name, "normalized_name": discipline.normalized_name}
        if existing is None:
            self._session.add(DisciplineModel(**values))
        elif any(getattr(existing, key) != value for key, value in values.items() if key != "id"):
            raise ValueError(f"discipline identity conflict: {discipline.id}")


def _to_contract(model: DisciplineModel) -> Discipline:
    return Discipline.model_validate({"id": model.id, "name": model.name, "normalized_name": model.normalized_name})
