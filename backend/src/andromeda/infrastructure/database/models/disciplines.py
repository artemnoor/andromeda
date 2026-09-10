from __future__ import annotations

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class DisciplineModel(Base):
    __tablename__ = "disciplines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)

    __table_args__ = (
        CheckConstraint("length(name) > 0", name="ck_discipline_name_non_empty"),
        CheckConstraint("length(normalized_name) > 0", name="ck_discipline_normalized_non_empty"),
    )
