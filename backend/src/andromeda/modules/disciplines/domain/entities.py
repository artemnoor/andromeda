from __future__ import annotations

from hashlib import sha256
import logging
from typing import Self

from pydantic import Field, model_validator

from ....shared.contracts.base import ContractModel
from ....shared.contracts.ids import DisciplineId, ShortText


logger = logging.getLogger("andromeda.contracts.validation")


class Discipline(ContractModel):
    id: DisciplineId
    name: str = Field(min_length=1, max_length=256)
    normalized_name: ShortText

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        expected = sha256(self.normalized_name.encode("utf-8")).hexdigest()[:16]
        if self.id != f"discipline:{expected}":
            logger.error("contract_semantic_violation model=Discipline field=id")
            raise ValueError("discipline id must derive from normalized_name")
        return self


__all__ = ["Discipline"]
