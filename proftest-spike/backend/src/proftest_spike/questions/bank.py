"""Deterministic scenario question bank.

Option labels describe situations and desired work products. They intentionally
do not mention professions, program ids or recommendation outcomes.
"""

from __future__ import annotations

from decimal import Decimal

from proftest_spike.domain.areas import AreaCode
from proftest_spike.program_fingerprints.entities import ActivityCode

from .entities import AnswerOption, Question, QuestionBlock, QuestionKind


def _option(
    option_id: str,
    label: str,
    description: str,
    *,
    subjects: tuple[tuple[AreaCode, str], ...] = (),
    activities: tuple[tuple[ActivityCode, str], ...] = (),
    anti_area: AreaCode | None = None,
    requires_intensity: bool = False,
) -> AnswerOption:
    return AnswerOption(
        id=option_id,
        label=label,
        description=description,
        subject_weights={area: Decimal(weight) for area, weight in subjects},
        activity_weights={activity: Decimal(weight) for activity, weight in activities},
        anti_area=anti_area,
        requires_intensity=requires_intensity,
    )


BASE_QUESTIONS: tuple[Question, ...] = (
    Question(
        id="interest_scenario_1",
        block=QuestionBlock.INTERESTS,
        kind=QuestionKind.SINGLE,
        title="Ситуация 1 из 2",
        prompt="У тебя есть свободный день для небольшого проекта. Что хочется довести до результата?",
        helper_text="Выбирай то, что было бы интересно делать, даже если тема пока незнакома.",
        options=(
            _option("prototype_logic", "Собрать работающий прототип", "Продумать логику, связать части и проверить, что всё работает.", subjects=((AreaCode.COMPUTER_SCIENCE_DATA, "0.75"), (AreaCode.MATHEMATICS_STATISTICS, "0.25")), activities=((ActivityCode.SOFTWARE_CREATION, "0.55"), (ActivityCode.SYSTEM_DESIGN, "0.30"), (ActivityCode.ANALYTICAL, "0.15"))),
            _option("find_patterns", "Найти закономерность в данных", "Собрать наблюдения, сравнить варианты и объяснить, почему проявился результат.", subjects=((AreaCode.MATHEMATICS_STATISTICS, "0.55"), (AreaCode.COMPUTER_SCIENCE_DATA, "0.25"), (AreaCode.ECONOMICS_FINANCE, "0.20")), activities=((ActivityCode.ANALYTICAL, "0.45"), (ActivityCode.DATA, "0.40"), (ActivityCode.RESEARCH, "0.15"))),
            _option("understand_device", "Разобраться в устройстве механизма", "Понять, как взаимодействуют физические элементы, и предложить улучшение.", subjects=((AreaCode.PHYSICS_ASTRONOMY, "0.60"), (AreaCode.ENGINEERING_TECHNOLOGY, "0.40")), activities=((ActivityCode.PHYSICAL_ENGINEERING, "0.55"), (ActivityCode.SYSTEM_DESIGN, "0.25"), (ActivityCode.RESEARCH, "0.20"))),
            _option("shape_model", "Продумать, как будет работать новая идея", "Соединить потребности людей, ресурсы и понятный план действий.", subjects=((AreaCode.ECONOMICS_FINANCE, "0.50"), (AreaCode.BUSINESS_MANAGEMENT, "0.35"), (AreaCode.SOCIETY_SOCIAL_SCIENCES, "0.15")), activities=((ActivityCode.BUSINESS, "0.45"), (ActivityCode.COMMUNICATION, "0.30"), (ActivityCode.ANALYTICAL, "0.25"))),
            _option("make_visual_language", "Создать визуальный язык проекта", "Выбрать форму, цвет и подачу так, чтобы смысл считывался без лишних слов.", subjects=((AreaCode.ART_DESIGN_MEDIA, "0.70"), (AreaCode.PSYCHOLOGY_COGNITIVE, "0.20"), (AreaCode.COMPUTER_SCIENCE_DATA, "0.10")), activities=((ActivityCode.CREATIVE, "0.60"), (ActivityCode.COMMUNICATION, "0.25"), (ActivityCode.SYSTEM_DESIGN, "0.15"))),
            _option("observe_living_system", "Исследовать, как меняется живая система", "Сформулировать гипотезу, провести наблюдение и аккуратно интерпретировать результат.", subjects=((AreaCode.BIOLOGY_BIOTECHNOLOGY, "0.65"), (AreaCode.MEDICINE_HEALTH, "0.20"), (AreaCode.EARTH_ENVIRONMENT, "0.15")), activities=((ActivityCode.RESEARCH, "0.55"), (ActivityCode.ANALYTICAL, "0.25"), (ActivityCode.DATA, "0.20"))),
        ),
        min_selections=1,
        max_selections=1,
    ),
    Question(
        id="interest_scenario_2",
        block=QuestionBlock.INTERESTS,
        kind=QuestionKind.SINGLE,
        title="Ситуация 2 из 2",
        prompt="В команде нужно выбрать, чем заняться на следующем этапе. Что звучит наиболее увлекательно?",
        helper_text="Здесь нет правильного ответа — важна привлекательность самого процесса.",
        options=(
            _option("map_complexity", "Разложить сложную задачу по шагам", "Найти связи между частями и выделить то, что определяет итог.", subjects=((AreaCode.MATHEMATICS_STATISTICS, "0.45"), (AreaCode.COMPUTER_SCIENCE_DATA, "0.30"), (AreaCode.UNIVERSAL_INTERDISCIPLINARY, "0.25")), activities=((ActivityCode.ANALYTICAL, "0.50"), (ActivityCode.SYSTEM_DESIGN, "0.30"), (ActivityCode.RESEARCH, "0.20"))),
            _option("test_material", "Проверить, как ведёт себя материал или конструкция", "Сравнить условия, провести серию проверок и понять границы надёжности.", subjects=((AreaCode.ENGINEERING_TECHNOLOGY, "0.50"), (AreaCode.PHYSICS_ASTRONOMY, "0.30"), (AreaCode.CHEMISTRY_MATERIALS, "0.20")), activities=((ActivityCode.PHYSICAL_ENGINEERING, "0.55"), (ActivityCode.RESEARCH, "0.30"), (ActivityCode.ANALYTICAL, "0.15"))),
            _option("compare_choices", "Сопоставить варианты и выбрать лучший", "Определить критерии, оценить ограничения и сделать вывод на основе фактов.", subjects=((AreaCode.ECONOMICS_FINANCE, "0.40"), (AreaCode.MATHEMATICS_STATISTICS, "0.35"), (AreaCode.BUSINESS_MANAGEMENT, "0.25")), activities=((ActivityCode.ANALYTICAL, "0.45"), (ActivityCode.DATA, "0.30"), (ActivityCode.BUSINESS, "0.25"))),
            _option("explain_to_people", "Понятно объяснить идею разным людям", "Подобрать примеры, услышать вопросы и изменить подачу, если это необходимо.", subjects=((AreaCode.LANGUAGES_LINGUISTICS_LITERATURE, "0.35"), (AreaCode.SOCIETY_SOCIAL_SCIENCES, "0.25"), (AreaCode.EDUCATION_PEDAGOGY, "0.25"), (AreaCode.ART_DESIGN_MEDIA, "0.15")), activities=((ActivityCode.COMMUNICATION, "0.60"), (ActivityCode.CREATIVE, "0.25"), (ActivityCode.RESEARCH, "0.15"))),
            _option("organize_process", "Настроить процесс, в котором всё движется вовремя", "Согласовать участников, распределить задачи и заранее увидеть узкие места.", subjects=((AreaCode.BUSINESS_MANAGEMENT, "0.50"), (AreaCode.UNIVERSAL_INTERDISCIPLINARY, "0.25"), (AreaCode.ECONOMICS_FINANCE, "0.25")), activities=((ActivityCode.BUSINESS, "0.50"), (ActivityCode.COMMUNICATION, "0.25"), (ActivityCode.SYSTEM_DESIGN, "0.25"))),
        ),
        min_selections=1,
        max_selections=1,
    ),
    Question(
        id="activity_preference_1",
        block=QuestionBlock.ACTIVITY,
        kind=QuestionKind.SINGLE,
        title="Какой процесс ближе?",
        prompt="Когда задача ещё неясна, что ты обычно хочешь сделать первым?",
        helper_text="Это отдельная шкала про способ работы, а не про любимый учебный предмет.",
        options=(
            _option("activity_measure", "Собрать факты и измерения", "Понять, каких данных не хватает, и проверить предположения.", activities=((ActivityCode.ANALYTICAL, "0.40"), (ActivityCode.DATA, "0.35"), (ActivityCode.RESEARCH, "0.25"))),
            _option("activity_architecture", "Набросать устройство системы", "Определить элементы, связи и правила взаимодействия.", activities=((ActivityCode.SYSTEM_DESIGN, "0.50"), (ActivityCode.ANALYTICAL, "0.25"), (ActivityCode.SOFTWARE_CREATION, "0.25"))),
            _option("activity_talk", "Поговорить с теми, для кого это делается", "Уточнить контекст, услышать разные точки зрения и найти общий язык.", activities=((ActivityCode.COMMUNICATION, "0.65"), (ActivityCode.RESEARCH, "0.20"), (ActivityCode.BUSINESS, "0.15"))),
            _option("activity_create", "Сделать несколько неожиданных набросков", "Проверить идеи через форму, образ или быстрый эксперимент.", activities=((ActivityCode.CREATIVE, "0.60"), (ActivityCode.SYSTEM_DESIGN, "0.20"), (ActivityCode.COMMUNICATION, "0.20"))),
            _option("activity_build", "Сразу собрать и проверить физический вариант", "Увидеть результат руками и улучшать его итерациями.", activities=((ActivityCode.PHYSICAL_ENGINEERING, "0.60"), (ActivityCode.SYSTEM_DESIGN, "0.25"), (ActivityCode.RESEARCH, "0.15"))),
        ),
        min_selections=1,
        max_selections=1,
    ),
    Question(
        id="activity_preference_2",
        block=QuestionBlock.ACTIVITY,
        kind=QuestionKind.SINGLE,
        title="Какой результат радует?",
        prompt="После хорошего рабочего дня какой результат кажется самым ценным?",
        helper_text="Выбирай результат, а не красивое название роли.",
        options=(
            _option("result_explanation", "Появилось ясное объяснение", "Теперь можно показать, почему система ведёт себя именно так.", activities=((ActivityCode.RESEARCH, "0.40"), (ActivityCode.ANALYTICAL, "0.40"), (ActivityCode.COMMUNICATION, "0.20"))),
            _option("result_working_thing", "Получилась работающая вещь", "Идея превратилась в инструмент, прототип или конструкцию.", activities=((ActivityCode.SOFTWARE_CREATION, "0.35"), (ActivityCode.PHYSICAL_ENGINEERING, "0.35"), (ActivityCode.SYSTEM_DESIGN, "0.30"))),
            _option("result_decision", "Стало проще принять решение", "Варианты сопоставлены, риски понятны и следующий шаг очевиден.", activities=((ActivityCode.DATA, "0.35"), (ActivityCode.ANALYTICAL, "0.35"), (ActivityCode.BUSINESS, "0.30"))),
            _option("result_shared_meaning", "Люди поняли друг друга", "Сложная мысль стала общей и пригодной для совместного действия.", activities=((ActivityCode.COMMUNICATION, "0.55"), (ActivityCode.CREATIVE, "0.25"), (ActivityCode.BUSINESS, "0.20"))),
        ),
        min_selections=1,
        max_selections=1,
    ),
    Question(
        id="tradeoff_theory_practice",
        block=QuestionBlock.TRADEOFF,
        kind=QuestionKind.SINGLE,
        title="Теория или практика",
        prompt="Если есть время только на один из двух способов разобраться, что выберешь?",
        helper_text="Компромиссный вариант тоже доступен — не нужно выбирать крайность.",
        options=(
            _option("tradeoff_theory", "Вывести общий принцип", "Разобраться в модели и проверить её на нескольких примерах.", activities=((ActivityCode.RESEARCH, "0.45"), (ActivityCode.ANALYTICAL, "0.40"), (ActivityCode.DATA, "0.15"))),
            _option("tradeoff_balance", "Соединить объяснение и пробу", "Коротко понять основу и сразу проверить её на небольшом примере.", activities=((ActivityCode.ANALYTICAL, "0.30"), (ActivityCode.SYSTEM_DESIGN, "0.25"), (ActivityCode.RESEARCH, "0.25"), (ActivityCode.SOFTWARE_CREATION, "0.20"))),
            _option("tradeoff_practice", "Собрать рабочий вариант", "Начать с практического результата и уточнять принцип по ходу.", activities=((ActivityCode.SOFTWARE_CREATION, "0.30"), (ActivityCode.PHYSICAL_ENGINEERING, "0.30"), (ActivityCode.SYSTEM_DESIGN, "0.25"), (ActivityCode.CREATIVE, "0.15"))),
        ),
        min_selections=1,
        max_selections=1,
    ),
    Question(
        id="anti_interest_areas",
        block=QuestionBlock.ANTI_INTERESTS,
        kind=QuestionKind.MULTI_INTENSITY,
        title="Что точно не хочется изучать",
        prompt="Отметь области, большой объём которых может быстро утомить. Для каждой выбранной области укажи силу отторжения.",
        helper_text="Можно ничего не отмечать. Если отмечаешь область, отвечай честно: это отдельный отрицательный вес, а не отсутствие интереса.",
        options=(
            _option("anti_mathematics", "Математика и статистика", "Много формул, доказательств и количественных моделей.", anti_area=AreaCode.MATHEMATICS_STATISTICS, requires_intensity=True),
            _option("anti_computer", "Компьютерные науки и данные", "Код, алгоритмы, базы данных и цифровые системы.", anti_area=AreaCode.COMPUTER_SCIENCE_DATA, requires_intensity=True),
            _option("anti_physics", "Физика и астрономия", "Модели физических процессов, измерения и расчёты.", anti_area=AreaCode.PHYSICS_ASTRONOMY, requires_intensity=True),
            _option("anti_chemistry", "Химия и материалы", "Свойства веществ, реакции и материалы.", anti_area=AreaCode.CHEMISTRY_MATERIALS, requires_intensity=True),
            _option("anti_engineering", "Инженерия и технологии", "Конструкции, приборы, производство и технические системы.", anti_area=AreaCode.ENGINEERING_TECHNOLOGY, requires_intensity=True),
            _option("anti_economics", "Экономика и финансы", "Ресурсы, рынки, деньги и количественные решения.", anti_area=AreaCode.ECONOMICS_FINANCE, requires_intensity=True),
            _option("anti_business", "Бизнес и управление", "Организация, процессы, управление людьми и проектами.", anti_area=AreaCode.BUSINESS_MANAGEMENT, requires_intensity=True),
            _option("anti_languages", "Языки и литература", "Языковые структуры, тексты и коммуникация.", anti_area=AreaCode.LANGUAGES_LINGUISTICS_LITERATURE, requires_intensity=True),
            _option("anti_humanities", "История, философия и гуманитарные науки", "Тексты, идеи, культура и исторический контекст.", anti_area=AreaCode.HISTORY_PHILOSOPHY_HUMANITIES, requires_intensity=True),
            _option("anti_design", "Искусство, дизайн и медиа", "Визуальная форма, творческие практики и медиаконтент.", anti_area=AreaCode.ART_DESIGN_MEDIA, requires_intensity=True),
            _option("anti_biology", "Биология и здоровье", "Живые системы, организм и методы исследования здоровья.", anti_area=AreaCode.BIOLOGY_BIOTECHNOLOGY, requires_intensity=True),
        ),
        min_selections=0,
        max_selections=11,
        required=True,
    ),
)


__all__ = ["BASE_QUESTIONS"]
