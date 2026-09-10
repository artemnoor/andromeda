from __future__ import annotations

from fastapi import APIRouter, Depends

from andromeda.api.dependencies.services import get_compare_service
from andromeda.api.schemas.common import ComparisonResponse
from andromeda.api.schemas.compare import CompareQuery, parse_compare_query
from andromeda.modules.comparison.services.compare_programs import CompareProgramsService

router = APIRouter(tags=["comparison"])


@router.get("/compare", response_model=ComparisonResponse)
def compare(
    query: CompareQuery = Depends(parse_compare_query),
    service: CompareProgramsService = Depends(get_compare_service),
) -> ComparisonResponse:
    result = service.compare(query.to_request())
    return ComparisonResponse.model_validate(result.model_dump())
