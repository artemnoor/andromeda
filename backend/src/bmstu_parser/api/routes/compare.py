from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...contracts.api import CompareResponse
from ..dependencies import get_session
from ..services.compare_service import build_compare_response

router = APIRouter(tags=["compare"])


@router.get("/compare", response_model=CompareResponse)
def compare_endpoint(
    program_ids: str = Query(..., alias="programIds", min_length=1, max_length=512),
    session: Session = Depends(get_session),
) -> CompareResponse:
    return build_compare_response(session, program_ids)
