"""Small strict DTOs for the public backend responses used by the bot."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class WireModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", populate_by_name=True)


class Program(WireModel):
    id: str
    direction_id: str = Field(alias="directionId")
    code: str
    name: str
    education_year: int = Field(alias="educationYear")
    study_plan_url: str = Field(alias="studyPlanUrl")
    source_url: str = Field(alias="sourceUrl")


class ProgramList(WireModel):
    items: list[Program]


class ProgramResponse(WireModel):
    program: Program


class DecisionContext(WireModel):
    decision_id: str = Field(alias="decisionId")
    profile_revision: int | None = Field(default=None, alias="profileRevision")
    context_revision: int = Field(alias="metadata.revision", default=1)


class DecisionSuggestion(WireModel):
    program_id: str = Field(alias="programId")
    program_code: str = Field(alias="programCode")
    program_name: str = Field(alias="programName")
    partition: str
    admission_status: str | None = Field(default=None, alias="admissionStatus")
    admission_risk: str = Field(alias="admissionRisk")
    content_fit: dict[str, object] | int | None = Field(default=None, alias="contentFit")


class RefinementOption(WireModel):
    id: str
    label: str


class RefinementQuestion(WireModel):
    id: str
    prompt: str
    candidate_program_ids: list[str] = Field(alias="candidateProgramIds")
    options: list[RefinementOption]


class DecisionSuggestions(WireModel):
    decision_id: str = Field(alias="decisionId")
    context_revision: int = Field(alias="contextRevision")
    active_shortlist: list[DecisionSuggestion] = Field(default_factory=list, alias="activeShortlist")
    primary_candidates: list[DecisionSuggestion] = Field(default_factory=list, alias="primaryCandidates")
    alternative_candidates: list[DecisionSuggestion] = Field(default_factory=list, alias="alternativeCandidates")
    suggestions: list[DecisionSuggestion] = Field(default_factory=list)
    refinement_question: RefinementQuestion | None = Field(default=None, alias="refinementQuestion")
    source_gaps: list[str] = Field(default_factory=list, alias="sourceGaps")
    missing_data: list[str] = Field(default_factory=list, alias="missingData")


class ComparisonProgram(WireModel):
    program_id: str = Field(alias="programId")
    program_code: str = Field(alias="programCode")
    program_name: str = Field(alias="programName")
    total_hours: int | None = Field(default=None, alias="totalHours")
    total_credits: str | int | float | None = Field(default=None, alias="totalCredits")
    area_breakdown: dict[str, str | int | float] = Field(default_factory=dict, alias="areaBreakdown")
    source_gaps: list[str] = Field(default_factory=list, alias="sourceGaps")


class ComparisonSummary(WireModel):
    programs: list[ComparisonProgram]
    key_differences: list[str] = Field(default_factory=list, alias="keyDifferences")
    tradeoffs: list[str] = Field(default_factory=list)
    source_gaps: list[str] = Field(default_factory=list, alias="sourceGaps")


class RefinementResponse(WireModel):
    suggestions: DecisionSuggestions
    profile_revision: int = Field(alias="profileRevision")


class AnalyticsAccepted(WireModel):
    accepted: int


class MutationResponse(WireModel):
    decision_id: str = Field(alias="decisionId")
    changed: bool
    context: dict[str, object]


class AssistantEnvelope(WireModel):
    response_type: str = Field(alias="response_type")
    text: str = ""
    template: str
    data: dict[str, object] = Field(default_factory=dict)
    actions: list[dict[str, object]] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class AssistantResponse(WireModel):
    state: str
    session_id: str = Field(alias="session_id")
    revision: int
    question: str | None = None
    options: list[str] = Field(default_factory=list)
    missing_slots: list[str] = Field(default_factory=list)
    response: AssistantEnvelope | None = None
    query: dict[str, object] | None = None
    admission_request: dict[str, object] | None = None
    admission_result: dict[str, object] | None = None


__all__ = [
    "AnalyticsAccepted",
    "AssistantEnvelope",
    "AssistantResponse",
    "ComparisonSummary",
    "DecisionContext",
    "DecisionSuggestion",
    "DecisionSuggestions",
    "MutationResponse",
    "Program",
    "ProgramList",
    "ProgramResponse",
    "RefinementResponse",
]
