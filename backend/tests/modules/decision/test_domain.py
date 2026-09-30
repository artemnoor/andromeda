from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from andromeda.modules.decision.domain.entities import DecisionChoice, DecisionState
from andromeda.modules.decision.domain.values import DecisionSourceKind, ShortlistEntryState, ShortlistRole
from andromeda.modules.decision.contracts.applicant_profile import ApplicantExamPlan, ApplicantOnboardingProfile


NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(minutes=1)
PROGRAM_A = "program:09.03.01-01"
PROGRAM_B = "program:09.03.01-02"


def test_explicit_choice_lifecycle_preserves_order_and_removed_history() -> None:
    choice = DecisionChoice().consider(PROGRAM_A)
    choice = choice.add_shortlist(
        PROGRAM_A,
        role=ShortlistRole.PRIMARY,
        origin=DecisionSourceKind.USER,
        now=NOW,
    )
    choice = choice.add_shortlist(
        PROGRAM_B,
        role=ShortlistRole.ALTERNATIVE,
        origin=DecisionSourceKind.SUGGESTION_ACCEPTED,
        now=NOW,
    )

    assert choice.considered_program_ids == (PROGRAM_A,)
    assert tuple(entry.program_id for entry in choice.active_shortlist) == (PROGRAM_A, PROGRAM_B)
    assert choice.active_shortlist[1].role is ShortlistRole.ALTERNATIVE

    choice = choice.remove_shortlist(PROGRAM_A, now=LATER)
    assert tuple(entry.program_id for entry in choice.removed_shortlist) == (PROGRAM_A,)
    assert choice.shortlist_entries[0].state is ShortlistEntryState.REMOVED

    choice = choice.restore_shortlist(PROGRAM_A, now=LATER + timedelta(minutes=1))
    assert choice.shortlist_entries[0].state is ShortlistEntryState.ACTIVE
    assert len(choice.shortlist_entries) == 2

    choice = choice.set_role(PROGRAM_A, role=ShortlistRole.ALTERNATIVE, now=LATER + timedelta(minutes=2))
    assert choice.shortlist_entries[0].role is ShortlistRole.ALTERNATIVE
    assert tuple(entry.program_id for entry in choice.active_shortlist) == (PROGRAM_A, PROGRAM_B)


def test_repeated_explicit_commands_are_idempotent() -> None:
    choice = DecisionChoice().add_shortlist(
        PROGRAM_A,
        role=ShortlistRole.PRIMARY,
        origin=DecisionSourceKind.USER,
        now=NOW,
    )

    assert choice.add_shortlist(
        PROGRAM_A,
        role=ShortlistRole.PRIMARY,
        origin=DecisionSourceKind.USER,
        now=LATER,
    ) == choice
    assert choice.remove_shortlist(PROGRAM_A, now=LATER).remove_shortlist(PROGRAM_A, now=LATER) == choice.remove_shortlist(
        PROGRAM_A,
        now=LATER,
    )


def test_onboarding_profile_persists_and_projects_only_entered_scores() -> None:
    initial = DecisionState(created_at=NOW, updated_at=NOW)
    profile = ApplicantOnboardingProfile(
        grade=11,
        planned_ege_subjects=("Русский язык", "Информатика"),
        exam_scores=(
            ApplicantExamPlan(subject="Русский язык", score=Decimal("86"), score_certainty="known"),
            ApplicantExamPlan(subject="Информатика"),
        ),
        quota_preference="unsure",
    )

    updated = initial.with_applicant_profile(profile, now=LATER)
    restored = DecisionState.model_validate(updated.model_dump(mode="json"), strict=False)

    assert restored.applicant_profile == profile
    assert restored.revision == initial.revision + 1
    assert restored.admission_constraints is not None
    assert restored.admission_constraints.applicant is not None
    assert [(item.subject, item.score) for item in restored.admission_constraints.applicant.scores] == [
        ("Русский язык", Decimal("86")),
    ]


def test_exclusion_is_explicit_and_does_not_create_a_shortlist_entry() -> None:
    choice = DecisionChoice().consider(PROGRAM_A).exclude(PROGRAM_A)
    assert choice.excluded_program_ids == (PROGRAM_A,)
    assert choice.shortlist_entries == ()
    assert choice.restore_excluded(PROGRAM_A).excluded_program_ids == ()

    with pytest.raises(ValueError, match="removed"):
        DecisionChoice().add_shortlist(
            PROGRAM_A,
            role=ShortlistRole.PRIMARY,
            origin=DecisionSourceKind.USER,
            now=NOW,
        ).exclude(PROGRAM_A)


def test_domain_state_never_mutates_when_a_candidate_reader_only_inspects_it() -> None:
    state = DecisionState(
        choice=DecisionChoice().add_shortlist(
            PROGRAM_A,
            role=ShortlistRole.PRIMARY,
            origin=DecisionSourceKind.USER,
            now=NOW,
        ),
        created_at=NOW,
        updated_at=NOW,
    )
    before = state.model_dump(mode="json")

    _ = state.choice.active_shortlist
    _ = state.choice.removed_shortlist
    _ = state.status

    assert state.model_dump(mode="json") == before
