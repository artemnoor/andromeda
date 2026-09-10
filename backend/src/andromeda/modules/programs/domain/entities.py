from __future__ import annotations

from typing import Self
import logging

from pydantic import HttpUrl, model_validator

from ....shared.contracts.base import ContractModel
from ....shared.contracts.ids import DirectionId, EducationYear, NonEmptyText, ProgramCode, ProgramId


logger = logging.getLogger("andromeda.contracts.validation")


class Program(ContractModel):
    id: ProgramId
    direction_id: DirectionId
    code: ProgramCode
    name: NonEmptyText
    education_year: EducationYear
    study_plan_url: HttpUrl
    source_url: HttpUrl

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.id != f"program:{self.code}":
            logger.error("contract_semantic_violation model=Program field=id")
            raise ValueError("program id must equal program:<code>")
        if not self.code.startswith(self.direction_id.removeprefix("direction:") + "-"):
            logger.error("contract_semantic_violation model=Program field=direction_id")
            raise ValueError("program code must belong to its direction")
        return self


__all__ = ["Program"]
