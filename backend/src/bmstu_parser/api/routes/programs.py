from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dependencies import get_session
from ..services.program_service import build_curriculum_response, build_program_response
from ...contracts.api import CurriculumResponse, ProgramResponse
from ...contracts.constraints import ProgramId

logger = logging.getLogger("api.request")
curriculum_logger = logging.getLogger("api.curriculum")
router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("/{id}", response_model=ProgramResponse)
def get_program_endpoint(id: ProgramId, session: Session = Depends(get_session)) -> ProgramResponse:
    logger.debug("program_read_start route=/programs/{id} validated_id=%s", id)
    result = build_program_response(session, id)
    logger.info("program_read_complete program_id=%s", result.program.id)
    return result


@router.get("/{id}/curriculum", response_model=CurriculumResponse)
def get_curriculum_endpoint(id: ProgramId, session: Session = Depends(get_session)) -> CurriculumResponse:
    logger.debug("curriculum_read_start route=/programs/{id}/curriculum validated_id=%s", id)
    result = build_curriculum_response(session, id)
    curriculum_logger.info("curriculum_read_complete program_id=%s item_count=%d", result.program.id, len(result.items))
    return result
