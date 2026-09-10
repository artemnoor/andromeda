"""Application facade orchestrating questionnaire, catalog and matching."""

from __future__ import annotations

from decimal import Decimal
import logging

from andromeda.shared.contracts.errors import ValidationError

from ..contracts.public import Answer, AnswerSet, ProftestPreview, ProftestResults, PreviewCandidate, Question, Recommendation, ReasonKind
from ..domain.adaptive import AdaptiveSelection
from ..repository.ports import ProftestCatalogReader
from .adaptive import AdaptiveCandidate, AdaptiveQuestionFactory, AdaptiveQuestionSelector
from .catalog import ProftestCatalogService
from .explanations import ExplanationBuilder
from .profile_builder import UserProfileBuilder
from .questionnaire import build_questionnaire
from .ranking import RankingService


logger = logging.getLogger("andromeda.proftest.application")


class ProftestService:
    def __init__(self, catalog: ProftestCatalogService, profile_builder: UserProfileBuilder | None = None, ranking: RankingService | None = None, explanations: ExplanationBuilder | None = None) -> None:
        self._catalog = catalog
        self._profile_builder = profile_builder or UserProfileBuilder()
        self._ranking = ranking or RankingService()
        self._explanations = explanations or ExplanationBuilder()
        self._adaptive_selector = AdaptiveQuestionSelector()
        self._adaptive_factory = AdaptiveQuestionFactory()

    def questionnaire(self):
        return build_questionnaire()

    def preview(self, answer_set: AnswerSet) -> ProftestPreview:
        questions = self.questionnaire().questions
        profile = self._build_profile(answer_set, questions)
        fingerprints = self._catalog.list_fingerprints()
        ranked = self._rank_all(profile, fingerprints)
        selection = self._select_adaptive(ranked)
        question = self._adaptive_factory.create(selection)
        logger.info("preview_complete fingerprint_count=%d candidate_count=%d adaptive_status=%s", len(fingerprints), len(ranked), selection.status.value)
        return ProftestPreview(profile=profile, adaptive=selection, question=question, candidates=tuple(PreviewCandidate(program_id=fingerprint.program_id, program_code=fingerprint.program_code, content_fit=score.content_fit) for fingerprint, score in ranked[:10]))

    def results(self, answer_set: AnswerSet) -> ProftestResults:
        questions = self.questionnaire().questions
        base_profile = self._build_profile(answer_set, questions)
        fingerprints = self._catalog.list_fingerprints()
        base_ranked = self._rank_all(base_profile, fingerprints)
        selection = self._select_adaptive(base_ranked)
        adaptive_question = self._adaptive_factory.create(selection)
        final_answer_set = answer_set
        if answer_set.adaptive_answers:
            if adaptive_question is None:
                raise ValidationError("Adaptive question is not available for this catalog")
            final_answer_set = self._validate_adaptive_answers(answer_set, adaptive_question)
            profile = self._build_profile(final_answer_set, questions, (adaptive_question,))
        else:
            profile = base_profile
        ranked = self._rank_all(profile, fingerprints)
        recommendations: list[Recommendation] = []
        for fingerprint, score in ranked[:10]:
            reasons = self._explanations.build(profile, fingerprint)
            recommendation = Recommendation.from_fingerprint(fingerprint, score).model_copy(
                update={
                    "reasons": tuple(reason for reason in reasons if reason.kind is ReasonKind.FIT),
                    "anti_fit_reasons": tuple(reason for reason in reasons if reason.kind is ReasonKind.ANTI_FIT),
                }
            )
            recommendations.append(recommendation)
        logger.info("results_complete fingerprint_count=%d recommendation_count=%d adaptive_answers=%d", len(fingerprints), len(recommendations), len(answer_set.adaptive_answers))
        return ProftestResults(profile=profile, recommendations=tuple(recommendations))

    def _build_profile(self, answer_set: AnswerSet, questions: tuple[Question, ...], adaptive_questions: tuple[Question, ...] = ()):
        try:
            return self._profile_builder.build(answer_set, questions, adaptive_questions)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def _rank_all(self, profile, fingerprints):
        return self._ranking.rank(profile, fingerprints, limit=max(1, len(fingerprints)))

    def _select_adaptive(self, ranked) -> AdaptiveSelection:
        return self._adaptive_selector.select(tuple(AdaptiveCandidate(fingerprint=fingerprint, score=Decimal(score.content_fit)) for fingerprint, score in ranked))

    @staticmethod
    def _validate_adaptive_answers(answer_set: AnswerSet, question: Question) -> AnswerSet:
        for adaptive_answer in answer_set.adaptive_answers:
            if adaptive_answer.question_id != question.id or adaptive_answer.option_id not in {option.id for option in question.options}:
                raise ValidationError("Adaptive answer does not match the current question")
        return AnswerSet(answers=answer_set.answers, adaptive_answers=answer_set.adaptive_answers)


__all__ = ["ProftestService"]
