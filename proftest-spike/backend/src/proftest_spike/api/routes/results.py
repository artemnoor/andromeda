"""Thin result route: request -> profile -> catalog -> rank -> explanation."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from proftest_spike.api.dependencies import get_catalog_service, get_container
from proftest_spike.api.schemas.results import (
    MetricResponse,
    ReasonResponse,
    RecommendationResponse,
    ResultsResponse,
    ScoreBreakdownResponse,
    TestAnswersRequest,
    result_program,
)
from proftest_spike.api.schemas.questions import to_answer_set
from proftest_spike.catalog.service import CatalogService
from proftest_spike.composition.container import Container
from proftest_spike.explanations.builder import ExplanationBuilder
from proftest_spike.matching.ranking import RankingService

router = APIRouter(prefix="/api/test", tags=["test"])


@router.post("/results", response_model=ResultsResponse)
async def results(
    payload: TestAnswersRequest,
    container: Container = Depends(get_container),
    catalog: CatalogService = Depends(get_catalog_service),
) -> ResultsResponse:
    answer_set = to_answer_set(payload)
    profile = container.profile_builder.build(answer_set)
    snapshot = await catalog.get_catalog()
    if not snapshot.fingerprints:
        return ResultsResponse(
            status="empty",
            data_source="andromeda_http_api",
            catalog_program_count=0,
            profile_confidence=profile.confidence.value,
            recommendations=(),
            note="Не удалось найти доступные учебные планы для сравнения.",
        )

    ranked = RankingService().rank(profile, snapshot.fingerprints, limit=10)
    explanation_builder = ExplanationBuilder()
    recommendations = tuple(
        RecommendationResponse(
            rank=index,
            program=result_program(fingerprint),
            content_fit=score.content_fit,
            breakdown=ScoreBreakdownResponse.model_validate(score.breakdown.model_dump()),
            reasons=tuple(ReasonResponse.model_validate(reason.model_dump()) for reason in explanation_builder.build(profile, fingerprint)),
            metrics=_metrics(),
        )
        for index, (fingerprint, score) in enumerate(ranked, start=1)
    )
    return ResultsResponse(
        status="ready",
        data_source="andromeda_http_api",
        catalog_program_count=len(snapshot.fingerprints),
        profile_confidence=profile.confidence.value,
        recommendations=recommendations,
        note="Рейтинг отражает совпадение с содержанием загруженных учебных планов, а не прогноз профессии.",
    )


def _metrics() -> tuple[MetricResponse, ...]:
    return (
        MetricResponse(code="workload_readiness", label="Готовность к нагрузке", value=None, status="not_available"),
        MetricResponse(code="career_fit", label="Career Fit", value=None, status="not_available"),
        MetricResponse(code="admission_fit", label="Admission Fit", value=None, status="not_available"),
    )


__all__ = ["router"]
