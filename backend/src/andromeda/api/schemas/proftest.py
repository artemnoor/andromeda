"""Strict HTTP schemas for the Andromeda proftest flow."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field

from andromeda.modules.disciplines.contracts.public import DisciplineAreaCode
from andromeda.modules.proftest.contracts.public import ActivityCode, AdaptiveAnswer, AdaptiveSelection, AdaptiveStatus, Answer, AnswerSet, AntiInterest, Confidence, MatchReason, MatchScore, ProftestPreview, ProftestResults, Question, Questionnaire, QuestionBlock, Recommendation, ReasonKind, UserProfile, UserProfileSnapshot

from .common import ApiModel


def _decimal_from_json(value: object) -> object:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value)
        except Exception:
            return value
    return value


JsonDecimal = Annotated[Decimal, BeforeValidator(_decimal_from_json), Field(strict=True, ge=0, le=1, max_digits=5, decimal_places=4)]


def _discipline_area_from_json(value: object) -> DisciplineAreaCode:
    if isinstance(value, DisciplineAreaCode):
        return value
    if isinstance(value, str):
        return DisciplineAreaCode(value)
    raise TypeError("discipline area must be a string")


def _activity_code_from_json(value: object) -> ActivityCode:
    if isinstance(value, ActivityCode):
        return value
    if isinstance(value, str):
        return ActivityCode(value)
    raise TypeError("activity code must be a string")


JsonDisciplineAreaCode = Annotated[DisciplineAreaCode, BeforeValidator(_discipline_area_from_json)]
JsonActivityCode = Annotated[ActivityCode, BeforeValidator(_activity_code_from_json)]


class ProftestAnswerRequest(ApiModel):
    question_id: str = Field(alias="questionId", min_length=1, max_length=256)
    option_ids: list[str] = Field(alias="optionIds", min_length=1, max_length=6)
    intensity: JsonDecimal | None = None

    def to_contract(self) -> Answer:
        return Answer(question_id=self.question_id, option_ids=tuple(self.option_ids), intensity=self.intensity)


class ProftestAdaptiveAnswerRequest(ApiModel):
    question_id: str = Field(alias="questionId", min_length=1, max_length=256)
    option_id: str = Field(alias="optionId", min_length=1, max_length=256)
    dimension: str = Field(min_length=3, max_length=128)

    def to_contract(self) -> AdaptiveAnswer:
        return AdaptiveAnswer(question_id=self.question_id, option_id=self.option_id, dimension=self.dimension)


class ProftestSubmissionRequest(ApiModel):
    answers: list[ProftestAnswerRequest] = Field(default_factory=list)
    adaptive_answers: list[ProftestAdaptiveAnswerRequest] = Field(default_factory=list, alias="adaptiveAnswers")

    def to_contract(self) -> AnswerSet:
        return AnswerSet(answers=tuple(answer.to_contract() for answer in self.answers), adaptive_answers=tuple(answer.to_contract() for answer in self.adaptive_answers))


class QuestionOptionResponse(ApiModel):
    id: str
    label: str


class QuestionResponse(ApiModel):
    id: str
    block: QuestionBlock
    prompt: str
    options: tuple[QuestionOptionResponse, ...]
    required: bool
    adaptive: bool
    multi_select: bool
    max_selected: int


class QuestionnaireResponse(ApiModel):
    version: Literal[1]
    questions: tuple[QuestionResponse, ...]


class ConfidenceResponse(ApiModel):
    value: JsonDecimal
    answered_base: int
    answered_adaptive: int


class AntiInterestResponse(ApiModel):
    area: JsonDisciplineAreaCode
    intensity: JsonDecimal


class AdaptiveAnswerResponse(ApiModel):
    question_id: str
    option_id: str
    dimension: str


class UserProfileResponse(ApiModel):
    version: Literal[1]
    interests: list[JsonDisciplineAreaCode]
    activity_preferences: list[JsonActivityCode]
    anti_interests: list[AntiInterestResponse]
    preferred_subject_weights: dict[JsonDisciplineAreaCode, JsonDecimal]
    preferred_activity_weights: dict[JsonActivityCode, JsonDecimal]
    negative_weights: dict[JsonDisciplineAreaCode, JsonDecimal]
    confidence: ConfidenceResponse
    adaptive_answers: list[AdaptiveAnswerResponse]


class UserProfileCreateRequest(ApiModel):
    profile: UserProfileResponse

    def to_contract(self) -> UserProfile:
        return profile_contract(self.profile)


class UserProfileUpdateRequest(ApiModel):
    profile: UserProfileResponse
    expected_revision: int = Field(alias="expectedRevision", strict=True, ge=1)

    def to_contract(self) -> UserProfile:
        return profile_contract(self.profile)


class UserProfileSnapshotResponse(ApiModel):
    profile_id: str = Field(alias="profileId", min_length=1, max_length=96)
    profile: UserProfileResponse
    revision: int = Field(strict=True, ge=1)
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    expires_at: datetime = Field(alias="expiresAt")


class AdaptiveDimensionResponse(ApiModel):
    code: str
    label: str
    kind: str
    spread: Decimal
    significance: Decimal


class AdaptiveSelectionResponse(ApiModel):
    status: AdaptiveStatus
    reason: str | None = None
    candidate_count: int
    top_candidate_count: int
    dimensions: tuple[AdaptiveDimensionResponse, ...]


class PreviewCandidateResponse(ApiModel):
    program_id: str
    program_code: str
    content_fit: int


class ProftestPreviewResponse(ApiModel):
    profile: UserProfileResponse
    adaptive: AdaptiveSelectionResponse
    question: QuestionResponse | None = None
    candidates: tuple[PreviewCandidateResponse, ...]


class ScoreBreakdownResponse(ApiModel):
    subject_fit: Decimal
    activity_fit: Decimal
    distinctive_fit: Decimal
    anti_penalty: Decimal
    raw_content_fit: Decimal


class MatchScoreResponse(ApiModel):
    program_id: str
    program_code: str
    content_fit: int
    breakdown: ScoreBreakdownResponse


class ReasonResponse(ApiModel):
    kind: ReasonKind
    area: DisciplineAreaCode | None = None
    activity: ActivityCode | None = None
    text: str
    workload: Decimal
    share: Decimal
    source_names: tuple[str, ...]


class OptionalMetricResponse(ApiModel):
    status: str
    value: int | None = None


class RecommendationResponse(ApiModel):
    program_id: str
    program_code: str
    program_name: str
    content_fit: int
    score: MatchScoreResponse
    reasons: tuple[ReasonResponse, ...]
    anti_fit_reasons: tuple[ReasonResponse, ...]
    area_share: dict[DisciplineAreaCode, Decimal]
    subject_group_share: dict[str, Decimal]
    semester_distribution: dict[str, Decimal]
    distinctive_subjects: tuple[str, ...]
    workload_readiness: OptionalMetricResponse
    career_fit: OptionalMetricResponse
    admission_fit: OptionalMetricResponse


class ProftestResultsResponse(ApiModel):
    profile: UserProfileResponse
    recommendations: tuple[RecommendationResponse, ...]


def questionnaire_response(questionnaire: Questionnaire) -> QuestionnaireResponse:
    return QuestionnaireResponse(version=questionnaire.version, questions=tuple(_question_response(question) for question in questionnaire.questions))


def preview_response(preview: ProftestPreview) -> ProftestPreviewResponse:
    return ProftestPreviewResponse(
        profile=profile_response(preview.profile),
        adaptive=AdaptiveSelectionResponse.model_validate(preview.adaptive.model_dump()),
        question=_question_response(preview.question) if preview.question is not None else None,
        candidates=tuple(PreviewCandidateResponse.model_validate(candidate.model_dump()) for candidate in preview.candidates),
    )


def results_response(results: ProftestResults) -> ProftestResultsResponse:
    return ProftestResultsResponse(profile=profile_response(results.profile), recommendations=tuple(recommendation_response(recommendation) for recommendation in results.recommendations))


def _question_response(question: Question) -> QuestionResponse:
    return QuestionResponse(id=question.id, block=question.block, prompt=question.prompt, options=tuple(QuestionOptionResponse(id=option.id, label=option.label) for option in question.options), required=question.required, adaptive=question.adaptive, multi_select=question.multi_select, max_selected=question.max_selected)


def profile_response(profile: UserProfile) -> UserProfileResponse:
    return UserProfileResponse(
        version=profile.version,
        interests=list(profile.interests),
        activity_preferences=list(profile.activity_preferences),
        anti_interests=[AntiInterestResponse(area=item.area, intensity=item.intensity) for item in profile.anti_interests],
        preferred_subject_weights=profile.preferred_subject_weights,
        preferred_activity_weights=profile.preferred_activity_weights,
        negative_weights=profile.negative_weights,
        confidence=ConfidenceResponse.model_validate(profile.confidence.model_dump()),
        adaptive_answers=[AdaptiveAnswerResponse.model_validate(answer.model_dump()) for answer in profile.adaptive_answers],
    )


def profile_contract(profile: UserProfileResponse) -> UserProfile:
    """Convert the sole HTTP profile shape to the stable module contract."""

    return UserProfile(
        version=profile.version,
        interests=tuple(DisciplineAreaCode(value) for value in profile.interests),
        activity_preferences=tuple(ActivityCode(value) for value in profile.activity_preferences),
        anti_interests=tuple(AntiInterest(area=DisciplineAreaCode(item.area), intensity=item.intensity) for item in profile.anti_interests),
        preferred_subject_weights={
            DisciplineAreaCode(area): weight
            for area, weight in profile.preferred_subject_weights.items()
        },
        preferred_activity_weights={
            ActivityCode(activity): weight
            for activity, weight in profile.preferred_activity_weights.items()
        },
        negative_weights={
            DisciplineAreaCode(area): weight
            for area, weight in profile.negative_weights.items()
        },
        confidence=Confidence(**profile.confidence.model_dump()),
        adaptive_answers=tuple(AdaptiveAnswer(**answer.model_dump()) for answer in profile.adaptive_answers),
    )


def snapshot_response(snapshot: UserProfileSnapshot) -> UserProfileSnapshotResponse:
    return UserProfileSnapshotResponse(
        profileId=snapshot.profile_id,
        profile=profile_response(snapshot.profile),
        revision=snapshot.revision,
        createdAt=snapshot.created_at,
        updatedAt=snapshot.updated_at,
        expiresAt=snapshot.expires_at,
    )


def recommendation_response(recommendation: Recommendation) -> RecommendationResponse:
    return RecommendationResponse(
        program_id=recommendation.program_id,
        program_code=recommendation.program_code,
        program_name=recommendation.program_name,
        content_fit=recommendation.content_fit,
        score=MatchScoreResponse.model_validate(recommendation.score.model_dump()),
        reasons=tuple(_reason_response(reason) for reason in recommendation.reasons),
        anti_fit_reasons=tuple(_reason_response(reason) for reason in recommendation.anti_fit_reasons),
        area_share=recommendation.area_share,
        subject_group_share=recommendation.subject_group_share,
        semester_distribution=recommendation.semester_distribution,
        distinctive_subjects=recommendation.distinctive_subjects,
        workload_readiness=OptionalMetricResponse.model_validate(recommendation.workload_readiness.model_dump()),
        career_fit=OptionalMetricResponse.model_validate(recommendation.career_fit.model_dump()),
        admission_fit=OptionalMetricResponse.model_validate(recommendation.admission_fit.model_dump()),
    )


def _reason_response(reason: MatchReason) -> ReasonResponse:
    return ReasonResponse(kind=reason.kind, area=reason.area, activity=reason.activity, text=reason.text, workload=reason.workload, share=reason.share, source_names=reason.source_names)


_profile_response = profile_response
_recommendation_response = recommendation_response


__all__ = [
    "ProftestSubmissionRequest",
    "ProftestPreviewResponse",
    "ProftestResultsResponse",
    "QuestionnaireResponse",
    "UserProfileCreateRequest",
    "UserProfileResponse",
    "UserProfileSnapshotResponse",
    "UserProfileUpdateRequest",
    "questionnaire_response",
    "preview_response",
    "results_response",
    "profile_contract",
    "profile_response",
    "snapshot_response",
    "recommendation_response",
]
