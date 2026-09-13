"""Transform validated answers into a normalized UserProfile."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
import logging

from proftest_spike.domain.areas import AreaCode
from proftest_spike.domain.values import ZERO, quantize_ratio
from proftest_spike.program_fingerprints.entities import ActivityCode
from proftest_spike.questions.entities import AdaptiveAnswer, Answer, AnswerSet, Question, QuestionKind

from .entities import AntiInterest, Confidence, UserProfile
from .normalization import normalize_weights

logger = logging.getLogger("proftest_spike.profiling")


class ProfileValidationError(ValueError):
    """Raised when an answer set cannot become a valid profile."""


class UserProfileBuilder:
    def __init__(self, questions: tuple[Question, ...]) -> None:
        self._questions = {question.id: question for question in questions}

    def build(self, answer_set: AnswerSet, *, require_complete: bool = True) -> UserProfile:
        logger.debug("profile_build_start answer_count=%d adaptive_count=%d", len(answer_set.answers), len(answer_set.adaptive_answers))
        if not answer_set.answers and not answer_set.adaptive_answers:
            logger.warning("profile_neutral_empty")
            return self._empty_profile()
        grouped: dict[str, list[Answer]] = defaultdict(list)
        for answer in answer_set.answers:
            question = self._questions.get(answer.question_id)
            if question is None:
                logger.error("profile_unknown_question")
                raise ProfileValidationError(f"unknown question: {answer.question_id}")
            if any(existing.option_id == answer.option_id for existing in grouped[answer.question_id]):
                logger.error("profile_duplicate_answer question_id=%s", _safe_id(answer.question_id))
                raise ProfileValidationError(f"duplicate answer: {answer.question_id}/{answer.option_id}")
            option = next((candidate for candidate in question.options if candidate.id == answer.option_id), None)
            if option is None:
                logger.error("profile_unknown_option question_id=%s", _safe_id(answer.question_id))
                raise ProfileValidationError(f"unknown option: {answer.question_id}/{answer.option_id}")
            if option.requires_intensity and answer.intensity is None:
                logger.error("profile_missing_intensity question_id=%s", _safe_id(answer.question_id))
                raise ProfileValidationError(f"intensity is required: {answer.option_id}")
            if not option.requires_intensity and answer.intensity is not None:
                raise ProfileValidationError(f"intensity is only valid for anti-interest options: {answer.option_id}")
            grouped[answer.question_id].append(answer)

        if require_complete:
            missing = [
                question.id
                for question in self._questions.values()
                if question.required and question.min_selections > 0 and question.id not in grouped
            ]
            if missing:
                logger.error("profile_incomplete missing_count=%d", len(missing))
                raise ProfileValidationError(f"required questions are missing: {','.join(missing)}")
        for question_id, answers in grouped.items():
            question = self._questions[question_id]
            if len(answers) < question.min_selections or len(answers) > question.max_selections:
                raise ProfileValidationError(f"invalid selection count: {question_id}")

        subject_scores: dict[AreaCode, Decimal] = defaultdict(lambda: ZERO)
        activity_scores: dict[ActivityCode, Decimal] = defaultdict(lambda: ZERO)
        anti_scores: dict[AreaCode, Decimal] = defaultdict(lambda: ZERO)
        anti_interests: dict[AreaCode, AntiInterest] = {}
        for answer in answer_set.answers:
            option = next(candidate for candidate in self._questions[answer.question_id].options if candidate.id == answer.option_id)
            for area, weight in option.subject_weights.items():
                subject_scores[area] += weight
            for activity, weight in option.activity_weights.items():
                activity_scores[activity] += weight
            if option.anti_area is not None:
                intensity = answer.intensity or ZERO
                anti_scores[option.anti_area] = max(anti_scores[option.anti_area], intensity)
                anti_interests[option.anti_area] = AntiInterest(area=option.anti_area, intensity=quantize_ratio(intensity))

        subject_weights = normalize_weights(subject_scores)
        activity_weights = normalize_weights(activity_scores)
        negative_weights = {area: value for area, value in sorted(anti_scores.items(), key=lambda entry: entry[0].value) if value > ZERO}
        base_count = len({answer.question_id for answer in answer_set.answers})
        adaptive_count = len(answer_set.adaptive_answers)
        confidence_value = min(Decimal("1"), Decimal(base_count) / Decimal(max(len(self._questions), 1)) + Decimal(adaptive_count) * Decimal("0.05"))
        profile = UserProfile(
            interests=tuple(subject_weights),
            activity_preferences=tuple(activity_weights),
            anti_interests=tuple(anti_interests[area] for area in sorted(anti_interests, key=lambda value: value.value)),
            preferred_subject_weights=subject_weights,
            preferred_activity_weights=activity_weights,
            negative_weights=negative_weights,
            confidence=Confidence(value=quantize_ratio(confidence_value), answered_base=base_count, answered_adaptive=adaptive_count),
            adaptive_answers=(),
        )
        for adaptive_answer in answer_set.adaptive_answers:
            profile = self.apply_adaptive_answer(profile, adaptive_answer)
        logger.info(
            "profile_built base_count=%d adaptive_count=%d subject_axis=%d activity_axis=%d anti_axis=%d confidence=%s",
            base_count,
            adaptive_count,
            len(profile.preferred_subject_weights),
            len(profile.preferred_activity_weights),
            len(profile.negative_weights),
            profile.confidence.value,
        )
        return profile

    def apply_adaptive_answer(self, profile: UserProfile, adaptive_answer: AdaptiveAnswer) -> UserProfile:
        """Apply one explicit adaptive choice and return a new validated profile."""

        if adaptive_answer.option_id not in {"more_first", "balanced", "more_second"}:
            logger.error("profile_invalid_adaptive_option")
            raise ProfileValidationError("unknown adaptive option")
        if adaptive_answer.first_dimension == adaptive_answer.second_dimension:
            raise ProfileValidationError("adaptive dimensions must differ")
        first_weight, second_weight = {
            "more_first": (Decimal("1"), ZERO),
            "balanced": (Decimal("0.5"), Decimal("0.5")),
            "more_second": (ZERO, Decimal("1")),
        }[adaptive_answer.option_id]
        subject_scores: dict[AreaCode, Decimal] = defaultdict(lambda: ZERO, profile.preferred_subject_weights)
        activity_scores: dict[ActivityCode, Decimal] = defaultdict(lambda: ZERO, profile.preferred_activity_weights)
        for dimension, weight in ((adaptive_answer.first_dimension, first_weight), (adaptive_answer.second_dimension, second_weight)):
            prefix, raw_code = dimension.split(":", maxsplit=1) if ":" in dimension else ("", "")
            if prefix == "area":
                subject_scores[AreaCode(raw_code)] += weight
            elif prefix == "activity":
                activity_scores[ActivityCode(raw_code)] += weight
            else:
                logger.error("profile_invalid_adaptive_dimension")
                raise ProfileValidationError("unknown adaptive dimension")
        adaptive_answers = tuple(profile.adaptive_answers) + (adaptive_answer,)
        updated = UserProfile(
            interests=tuple(normalize_weights(subject_scores)),
            activity_preferences=tuple(normalize_weights(activity_scores)),
            anti_interests=profile.anti_interests,
            preferred_subject_weights=normalize_weights(subject_scores),
            preferred_activity_weights=normalize_weights(activity_scores),
            negative_weights=profile.negative_weights,
            confidence=Confidence(
                value=quantize_ratio(min(Decimal("1"), profile.confidence.value + Decimal("0.05"))),
                answered_base=profile.confidence.answered_base,
                answered_adaptive=profile.confidence.answered_adaptive + 1,
            ),
            adaptive_answers=adaptive_answers,
        )
        logger.debug("profile_adaptive_applied adaptive_count=%d", len(updated.adaptive_answers))
        return updated

    @staticmethod
    def _empty_profile() -> UserProfile:
        return UserProfile(
            interests=(),
            activity_preferences=(),
            anti_interests=(),
            preferred_subject_weights={},
            preferred_activity_weights={},
            negative_weights={},
            confidence=Confidence(value=ZERO, answered_base=0, answered_adaptive=0),
            adaptive_answers=(),
        )


def _safe_id(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ")[:128]


__all__ = ["ProfileValidationError", "UserProfileBuilder"]
