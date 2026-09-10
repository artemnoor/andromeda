"""Initial test bootstrap endpoint.

The catalog and question contracts are added by later Spike modules. Keeping a
typed bootstrap route from the beginning gives the frontend one stable entry
point and avoids exposing upstream payloads.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends

from proftest_spike.adaptive.entities import AdaptiveQuestion
from proftest_spike.adaptive.question_factory import AdaptiveQuestionFactory
from proftest_spike.adaptive.selector import AdaptiveCandidate, AdaptiveQuestionSelector
from proftest_spike.api.dependencies import get_catalog_service, get_container
from proftest_spike.api.schemas.adaptive import (
    AdaptiveDimensionResponse,
    AdaptiveOptionResponse,
    AdaptiveQuestionResponse,
    PreviewResponse,
    ProgressResponse,
    adaptive_response,
)
from proftest_spike.api.schemas.bootstrap import BootstrapResponse
from proftest_spike.api.schemas.questions import TestAnswersRequest, question_response, to_answer_set
from proftest_spike.catalog.service import CatalogService
from proftest_spike.composition.container import Container
from proftest_spike.matching.scoring import ScoringService
from proftest_spike.questions.entities import AnswerSet

from ..schemas.common import ApiModel

router = APIRouter(prefix="/api/test", tags=["test"])


@router.get("/bootstrap", response_model=BootstrapResponse)
async def bootstrap(container: Container = Depends(get_container)) -> BootstrapResponse:
    questions = tuple(question_response(question) for question in container.questions.list_base())
    return BootstrapResponse(
        status="ready",
        service="andromeda-proftest-spike",
        test_version="0.1.0",
        catalog_status="not_loaded",
        data_source="andromeda_http_api",
        questions=questions,
        total_base=len(questions),
    )


@router.post("/preview", response_model=PreviewResponse)
async def preview(
    payload: TestAnswersRequest,
    container: Container = Depends(get_container),
    catalog: CatalogService = Depends(get_catalog_service),
) -> PreviewResponse:
    answer_set = to_answer_set(payload)
    profile = container.profile_builder.build(answer_set)
    snapshot = await catalog.get_catalog()
    if not snapshot.fingerprints:
        return PreviewResponse(
            status="empty",
            catalog_program_count=0,
            profile_confidence=profile.confidence.value,
            adaptive=None,
            progress=_progress(container, answer_set),
        )
    candidates = tuple(
        AdaptiveCandidate(fingerprint=fingerprint, score=Decimal(ScoringService().score(profile, fingerprint).content_fit))
        for fingerprint in snapshot.fingerprints
    )
    selection = AdaptiveQuestionSelector().select(candidates)
    question = AdaptiveQuestionFactory().create(selection)
    question_response_model = _adaptive_question_response(question)
    return PreviewResponse(
        status="ready",
        catalog_program_count=len(snapshot.fingerprints),
        profile_confidence=profile.confidence.value,
        adaptive=adaptive_response(selection, question_response_model),
        progress=_progress(container, answer_set, has_adaptive=question is not None),
    )


def _progress(container: Container, answer_set: AnswerSet, *, has_adaptive: bool = False) -> ProgressResponse:
    total_base = len(container.questions.list_base())
    answered_base = len({answer.question_id for answer in answer_set.answers})
    return ProgressResponse(
        answered_base=answered_base,
        total_base=total_base,
        answered_adaptive=len(answer_set.adaptive_answers),
        total_steps=total_base + (1 if has_adaptive else 0),
    )


def _adaptive_question_response(question: AdaptiveQuestion | None) -> AdaptiveQuestionResponse | None:
    if question is None:
        return None
    return AdaptiveQuestionResponse(
        id=question.id,
        prompt=question.prompt,
        helper_text=question.helper_text,
        first_dimension=AdaptiveDimensionResponse.model_validate(question.first_dimension.model_dump()),
        second_dimension=AdaptiveDimensionResponse.model_validate(question.second_dimension.model_dump()),
        options=tuple(AdaptiveOptionResponse(id=option.id, label=option.label, description=option.description) for option in question.options),
    )


__all__ = ["router"]
