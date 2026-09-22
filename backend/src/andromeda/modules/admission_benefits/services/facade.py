"""Application-facing facade over the admission-benefit repository port."""

from __future__ import annotations

import logging
from time import perf_counter

from andromeda.modules.admission_benefits.contracts.public import (
    AdmissionBenefitRule,
    IndividualAchievementPolicy,
)
from andromeda.modules.admission_benefits.contracts.results import (
    AdmissionDecisionResult,
)
from andromeda.modules.admission_benefits.contracts.snapshot import (
    AdmissionBenefitsSnapshot,
)
from andromeda.modules.admission_benefits.repository.ports import AdmissionBenefitReader
from andromeda.modules.admission_benefits.services.admission_decision import (
    AdmissionDecisionService,
)
from andromeda.modules.admission_benefits.services.evaluator import (
    AdmissionBenefitEvaluationInput,
)
from andromeda.shared.contracts.enums import EducationLevel
from andromeda.shared.contracts.ids import (
    DirectionCode,
    EducationYear,
    OlympiadId,
    ProgramId,
    UniversityId,
)

logger = logging.getLogger("andromeda.modules.admission_benefits.facade")


class AdmissionBenefitCatalogService:
    """Read source-backed benefit facts in forward and reverse directions."""

    def __init__(self, reader: AdmissionBenefitReader) -> None:
        self._reader = reader

    def university_catalog(
        self,
        university_id: UniversityId,
        admission_year: EducationYear,
        education_level: EducationLevel | None = None,
    ) -> AdmissionBenefitsSnapshot | None:
        started = perf_counter()
        result = self._reader.get_catalog(university_id, admission_year, education_level)
        logger.info(
            "admission_benefit_catalog_read university_id=%s year=%d found=%s duration_ms=%d",
            university_id,
            admission_year,
            result is not None,
            _elapsed_ms(started),
        )
        return result

    def program_rules(
        self,
        program_id: ProgramId,
        admission_year: EducationYear,
        *,
        include_review: bool = False,
    ) -> tuple[AdmissionBenefitRule, ...]:
        return self._reader.get_rules_for_program(program_id, admission_year, include_review=include_review)

    def direction_rules(
        self,
        direction_code: DirectionCode,
        university_id: UniversityId,
        admission_year: EducationYear,
        *,
        education_level: EducationLevel | None = None,
        include_review: bool = False,
    ) -> tuple[AdmissionBenefitRule, ...]:
        return self._reader.get_rules_for_direction(
            direction_code,
            university_id,
            admission_year,
            education_level=education_level,
            include_review=include_review,
        )

    def olympiad_rules(
        self,
        olympiad_id: OlympiadId,
        university_id: UniversityId,
        admission_year: EducationYear,
        *,
        benefit_type: str | None = None,
        include_review: bool = False,
    ) -> tuple[AdmissionBenefitRule, ...]:
        return self._reader.get_programs_for_olympiad(
            olympiad_id,
            university_id,
            admission_year,
            benefit_type=benefit_type,
            include_review=include_review,
        )

    def individual_achievement_policy(
        self,
        university_id: UniversityId,
        admission_year: EducationYear,
        education_level: EducationLevel | None = None,
        *,
        include_review: bool = False,
    ) -> IndividualAchievementPolicy | None:
        return self._reader.get_individual_achievement_policy(
            university_id,
            admission_year,
            education_level,
            include_review=include_review,
        )


class AdmissionEligibilityService:
    """Load canonical rules, then delegate legal evaluation to pure services."""

    def __init__(
        self,
        reader: AdmissionBenefitReader,
        decision_service: AdmissionDecisionService | None = None,
    ) -> None:
        self._reader = reader
        self._decision_service = decision_service or AdmissionDecisionService()

    def evaluate(
        self,
        request: AdmissionBenefitEvaluationInput,
        *,
        university_id: UniversityId,
        include_review: bool = True,
    ) -> AdmissionDecisionResult:
        started = perf_counter()
        rules = self._reader.get_rules_for_program(
            request.program_id,
            request.admission_year,
            include_review=include_review,
        )
        policy = self._reader.get_individual_achievement_policy(
            university_id,
            request.admission_year,
            request.education_level,
            include_review=include_review,
        )
        result = self._decision_service.evaluate(
            request.model_copy(update={"rules": rules}),
            individual_policy=policy,
        )
        logger.info(
            "admission_eligibility_service_complete program_id=%s university_id=%s year=%d rules=%d policy=%s status=%s duration_ms=%d",
            request.program_id,
            university_id,
            request.admission_year,
            len(rules),
            policy is not None,
            result.status,
            _elapsed_ms(started),
        )
        return result


def _elapsed_ms(started: float) -> int:
    return int((perf_counter() - started) * 1000)


__all__ = ["AdmissionBenefitCatalogService", "AdmissionEligibilityService"]
