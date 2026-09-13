from __future__ import annotations

from fastapi import APIRouter, Depends

from andromeda.api.dependencies.profile_session import get_profile_scope
from andromeda.api.dependencies.services import get_proftest_service
from andromeda.api.dependencies.services import get_profile_persistence_service
from andromeda.api.schemas.proftest import ProftestPreviewResponse, ProftestResultsResponse, ProftestSubmissionRequest, QuestionnaireResponse, UserProfileCreateRequest, UserProfileSnapshotResponse, UserProfileUpdateRequest, preview_response, questionnaire_response, results_response, snapshot_response
from andromeda.modules.proftest.contracts.public import ProfileScope
from andromeda.modules.proftest.services.profile_persistence import UserProfilePersistenceService
from andromeda.modules.proftest.services.proftest import ProftestService


router = APIRouter(prefix="/proftest", tags=["proftest"])


@router.get("/questions", response_model=QuestionnaireResponse)
def get_questions(service: ProftestService = Depends(get_proftest_service)) -> QuestionnaireResponse:
    return questionnaire_response(service.questionnaire())


@router.post("/preview", response_model=ProftestPreviewResponse)
def preview(request: ProftestSubmissionRequest, service: ProftestService = Depends(get_proftest_service)) -> ProftestPreviewResponse:
    return preview_response(service.preview(request.to_contract()))


@router.post("/results", response_model=ProftestResultsResponse)
def results(
    request: ProftestSubmissionRequest,
    scope: ProfileScope = Depends(get_profile_scope),
    service: ProftestService = Depends(get_proftest_service),
) -> ProftestResultsResponse:
    return results_response(service.results(request.to_contract(), profile_scope=scope))


@router.get("/profile", response_model=UserProfileSnapshotResponse)
def get_profile(
    scope: ProfileScope = Depends(get_profile_scope),
    service: UserProfilePersistenceService = Depends(get_profile_persistence_service),
) -> UserProfileSnapshotResponse:
    snapshot = service.get_current(scope)
    return snapshot_response(snapshot)


@router.post("/profile", response_model=UserProfileSnapshotResponse, status_code=201)
def create_profile(
    request: UserProfileCreateRequest,
    scope: ProfileScope = Depends(get_profile_scope),
    service: UserProfilePersistenceService = Depends(get_profile_persistence_service),
) -> UserProfileSnapshotResponse:
    snapshot = service.create(scope, request.to_contract())
    return snapshot_response(snapshot)


@router.put("/profile", response_model=UserProfileSnapshotResponse)
def update_profile(
    request: UserProfileUpdateRequest,
    scope: ProfileScope = Depends(get_profile_scope),
    service: UserProfilePersistenceService = Depends(get_profile_persistence_service),
) -> UserProfileSnapshotResponse:
    snapshot = service.update(scope, request.to_contract(), expected_revision=request.expected_revision)
    return snapshot_response(snapshot)
