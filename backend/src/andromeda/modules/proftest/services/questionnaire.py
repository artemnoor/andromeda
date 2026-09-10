"""Deterministic, scenario-based questionnaire for educational content fit."""

from __future__ import annotations

from decimal import Decimal

from andromeda.modules.disciplines.contracts.public import DisciplineAreaCode

from ..contracts.public import ActivityCode, Question, QuestionBlock, QuestionOption, Questionnaire


def _option(
    option_id: str,
    label: str,
    *,
    subjects: tuple[tuple[DisciplineAreaCode, str], ...] = (),
    activities: tuple[tuple[ActivityCode, str], ...] = (),
    anti: tuple[tuple[DisciplineAreaCode, str], ...] = (),
) -> QuestionOption:
    return QuestionOption(
        id=option_id,
        label=label,
        subject_weights={area: Decimal(weight) for area, weight in subjects},
        activity_weights={activity: Decimal(weight) for activity, weight in activities},
        anti_interest_weights={area: Decimal(weight) for area, weight in anti},
    )


def build_questionnaire() -> Questionnaire:
    """Return a fresh questionnaire contract for every request."""

    return Questionnaire.from_questions(
        (
            Question(
                id="interest_free_day",
                block=QuestionBlock.INTERESTS,
                prompt="У тебя есть свободный день для проекта. Что интереснее?",
                options=(
                    _option("software_tool", "Собрать цифровой инструмент", subjects=((DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "1"),), activities=((ActivityCode.SOFTWARE_CREATION, "1"),)),
                    _option("physical_device", "Разобраться, как работает устройство", subjects=((DisciplineAreaCode.PHYSICS_ASTRONOMY, "0.7"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.3")), activities=((ActivityCode.PHYSICAL_ENGINEERING, "1"),)),
                    _option("data_story", "Найти закономерность в данных", subjects=((DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.5"), (DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.5")), activities=((ActivityCode.DATA, "1"),)),
                    _option("product_concept", "Придумать, как улучшить продукт", subjects=((DisciplineAreaCode.BUSINESS_MANAGEMENT, "0.7"), (DisciplineAreaCode.ART_DESIGN_MEDIA, "0.3")), activities=((ActivityCode.CREATIVE, "0.7"), (ActivityCode.BUSINESS, "0.3"))),
                ),
            ),
            Question(
                id="interest_investigation",
                block=QuestionBlock.INTERESTS,
                prompt="Какая задача кажется тебе наиболее увлекательной?",
                options=(
                    _option("prove_model", "Проверить модель расчётами", subjects=((DisciplineAreaCode.MATHEMATICS_STATISTICS, "1"),), activities=((ActivityCode.ANALYTICAL, "1"),)),
                    _option("understand_nature", "Понять, почему происходит явление", subjects=((DisciplineAreaCode.PHYSICS_ASTRONOMY, "0.8"), (DisciplineAreaCode.CHEMISTRY_MATERIALS, "0.2")), activities=((ActivityCode.RESEARCH, "1"),)),
                    _option("understand_people", "Понять, как люди принимают решения", subjects=((DisciplineAreaCode.PSYCHOLOGY_COGNITIVE, "0.7"), (DisciplineAreaCode.SOCIETY_SOCIAL_SCIENCES, "0.3")), activities=((ActivityCode.RESEARCH, "0.7"), (ActivityCode.COMMUNICATION, "0.3"))),
                    _option("tell_clearly", "Объяснить сложную идею понятным языком", subjects=((DisciplineAreaCode.LANGUAGES_LINGUISTICS_LITERATURE, "0.6"), (DisciplineAreaCode.EDUCATION_PEDAGOGY, "0.4")), activities=((ActivityCode.COMMUNICATION, "1"),)),
                ),
            ),
            Question(
                id="activity_build",
                block=QuestionBlock.ACTIVITIES,
                prompt="Какой результат работы тебе приятнее увидеть?",
                options=(
                    _option("working_code", "Работающий код или сервис", activities=((ActivityCode.SOFTWARE_CREATION, "1"),)),
                    _option("system_scheme", "Продуманную схему системы", activities=((ActivityCode.SYSTEM_DESIGN, "1"),)),
                    _option("tested_hypothesis", "Подтверждённую гипотезу", activities=((ActivityCode.RESEARCH, "0.6"), (ActivityCode.ANALYTICAL, "0.4"),)),
                    _option("visible_concept", "Визуальную концепцию или макет", activities=((ActivityCode.CREATIVE, "1"),)),
                ),
            ),
            Question(
                id="activity_working_style",
                block=QuestionBlock.ACTIVITIES,
                prompt="В командном проекте тебе ближе какая роль?",
                options=(
                    _option("organize_work", "Собрать план и организовать работу", activities=((ActivityCode.BUSINESS, "1"),)),
                    _option("analyze_options", "Сравнить варианты и найти лучшее решение", activities=((ActivityCode.ANALYTICAL, "1"),)),
                    _option("design_architecture", "Спроектировать устройство или систему", activities=((ActivityCode.SYSTEM_DESIGN, "0.7"), (ActivityCode.PHYSICAL_ENGINEERING, "0.3"))),
                    _option("explain_to_team", "Синхронизировать людей и объяснить идею", activities=((ActivityCode.COMMUNICATION, "1"),)),
                ),
            ),
            Question(
                id="anti_subjects",
                block=QuestionBlock.ANTI_INTERESTS,
                prompt="Какие области ты точно не хотел бы изучать много? Можно выбрать до трёх.",
                multi_select=True,
                max_selected=3,
                options=(
                    _option("avoid_physics", "Физика и физические системы", anti=((DisciplineAreaCode.PHYSICS_ASTRONOMY, "1"),)),
                    _option("avoid_chemistry", "Химия и материалы", anti=((DisciplineAreaCode.CHEMISTRY_MATERIALS, "1"),)),
                    _option("avoid_programming", "Программирование и цифровые системы", anti=((DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "1"),)),
                    _option("avoid_math", "Большой объём математики", anti=((DisciplineAreaCode.MATHEMATICS_STATISTICS, "1"),)),
                    _option("avoid_business", "Экономика и управление", anti=((DisciplineAreaCode.ECONOMICS_FINANCE, "0.6"), (DisciplineAreaCode.BUSINESS_MANAGEMENT, "0.4"))),
                    _option("avoid_humanities", "Языки и гуманитарные дисциплины", anti=((DisciplineAreaCode.LANGUAGES_LINGUISTICS_LITERATURE, "0.6"), (DisciplineAreaCode.HISTORY_PHILOSOPHY_HUMANITIES, "0.4"))),
                ),
            ),
            Question(
                id="activity_depth",
                block=QuestionBlock.ACTIVITIES,
                prompt="Какой темп и формат обучения тебе ближе?",
                options=(
                    _option("deep_theory", "Разобраться в принципах и доказательствах", activities=((ActivityCode.RESEARCH, "0.6"), (ActivityCode.ANALYTICAL, "0.4")), subjects=((DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.6"),)),
                    _option("practical_prototype", "Быстро собрать прототип и проверить его", activities=((ActivityCode.SOFTWARE_CREATION, "0.4"), (ActivityCode.SYSTEM_DESIGN, "0.6"))),
                    _option("physical_experiment", "Поставить эксперимент с реальным объектом", activities=((ActivityCode.PHYSICAL_ENGINEERING, "0.7"), (ActivityCode.RESEARCH, "0.3"))),
                    _option("team_case", "Решить задачу через обсуждение и командный кейс", activities=((ActivityCode.COMMUNICATION, "0.5"), (ActivityCode.BUSINESS, "0.5"))),
                ),
            ),
        )
    )


__all__ = ["build_questionnaire"]
