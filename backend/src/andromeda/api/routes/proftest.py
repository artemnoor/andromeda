from __future__ import annotations

from fastapi import APIRouter, Depends

from andromeda.api.dependencies.services import get_proftest_service
from andromeda.api.schemas.proftest import ProftestPreviewResponse, ProftestResultsResponse, ProftestSubmissionRequest, QuestionnaireResponse, preview_response, questionnaire_response, results_response
from andromeda.modules.proftest.services.proftest import ProftestService


router = APIRouter(prefix="/proftest", tags=["proftest"])


@router.get("/questions", response_model=QuestionnaireResponse)
def get_questions(service: ProftestService = Depends(get_proftest_service)) -> QuestionnaireResponse:
    return questionnaire_response(service.questionnaire())


@router.post("/preview", response_model=ProftestPreviewResponse)
def preview(request: ProftestSubmissionRequest, service: ProftestService = Depends(get_proftest_service)) -> ProftestPreviewResponse:
    return preview_response(service.preview(request.to_contract()))


@router.post("/results", response_model=ProftestResultsResponse)
def results(request: ProftestSubmissionRequest, service: ProftestService = Depends(get_proftest_service)) -> ProftestResultsResponse:
    return results_response(service.results(request.to_contract()))
