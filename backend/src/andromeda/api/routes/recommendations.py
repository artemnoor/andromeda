"""Thin HTTP adapter for the recommendation application service."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from andromeda.api.dependencies.services import get_recommendation_service
from andromeda.api.schemas.recommendations import RecommendationRequest, RecommendationsResponse, recommendations_response
from andromeda.modules.recommendations.services.recommendations import RecommendationService


logger = logging.getLogger("andromeda.api.recommendations")
router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationsResponse)
def recommend(request: RecommendationRequest, service: RecommendationService = Depends(get_recommendation_service)) -> RecommendationsResponse:
    logger.debug("recommendations_request_accepted limit=%d subject_axes=%d", request.limit, len(request.profile.preferred_subject_weights))
    result = service.recommend(request.to_contract())
    logger.info("recommendations_http_complete status=200 result_count=%d top_fit=%s", len(result.recommendations), result.recommendations[0].content_fit if result.recommendations else "none")
    return recommendations_response(result)


__all__ = ["router"]
