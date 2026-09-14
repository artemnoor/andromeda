from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Protocol

from ..domain.areas import AreaVector, DisciplineAreaCode, DisciplineAreaWeight, area_vector, default_area_weights
from ..domain.identity import normalize_discipline_name


logger = logging.getLogger("andromeda.disciplines.classifier")


class DisciplineClassifier(Protocol):
    def classify(self, source_name: str) -> tuple[DisciplineAreaWeight, ...]: ...


class RuleBasedDisciplineClassifier:
    """Classify subject content into the Andromeda multi-area taxonomy.

    The classifier is deliberately transparent and conservative. Source-owned
    mappings may provide an exact vector; generic keyword rules are only a
    fallback for a new university or a newly encountered subject.
    """

    def __init__(self, overrides: Mapping[str, AreaVector] | None = None) -> None:
        self._overrides = dict(overrides or {})

    def classify(self, source_name: str) -> tuple[DisciplineAreaWeight, ...]:
        normalized_name = normalize_discipline_name(source_name)
        vector = self._overrides.get(normalized_name)
        if vector is None:
            vector = self._classify_by_rules(normalized_name)
        if vector is None:
            logger.debug("discipline_classification_fallback area=%s", DisciplineAreaCode.UNIVERSAL_INTERDISCIPLINARY.value)
            return default_area_weights()
        return tuple(DisciplineAreaWeight(area=area, weight=weight) for area, weight in vector)

    @staticmethod
    def _classify_by_rules(normalized_name: str) -> AreaVector | None:
        for keywords, vector in _DEFAULT_RULES:
            if any(keyword in normalized_name for keyword in keywords):
                return vector
        return None


_DEFAULT_RULES: tuple[tuple[tuple[str, ...], AreaVector], ...] = (
    (("биоинформ",), area_vector((DisciplineAreaCode.BIOLOGY_BIOTECHNOLOGY, "0.50"), (DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.40"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.10"))),
    (("эконометр",), area_vector((DisciplineAreaCode.ECONOMICS_FINANCE, "0.55"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.45"))),
    (("машинн", "нейросет", "искусственн интеллект", "глубок обуч"), area_vector((DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.75"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.25"))),
    (("естественн язык", "лингвистическ технолог"), area_vector((DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.65"), (DisciplineAreaCode.LANGUAGES_LINGUISTICS_LITERATURE, "0.25"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.10"))),
    (("ux", "эргоном", "человеко-машин", "конфликтолог"), area_vector((DisciplineAreaCode.PSYCHOLOGY_COGNITIVE, "0.45"), (DisciplineAreaCode.ART_DESIGN_MEDIA, "0.30"), (DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.25"))),
    (("веб-разработ", "web", "программирован", "алгоритм", "информационн систем", "баз данн", "операционн систем", "телекоммуникац", "кибербезопас", "информационн безопас", "данн", "информатик", "нейросет", "робототех"), area_vector((DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.75"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.15"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.10"))),
    (("дифференциальн", "интеграл", "функциональн", "функц комплекс", "функций комплекс", "теори галуа", "теория галуа", "теории галуа", "теори колец", "теория колец", "теории колец", "численн", "стохастическ", "случайн процесс", "теори вероятн", "теория вероятн", "теории вероятн", "теори чисел", "теория чисел", "теории чисел", "комбинатор", "конечн элемент", "конечных элементов", "сеточных метод", "разностн схем", "уравнен", "алгебр", "геометр", "оптимизац", "вариационн", "теори игр", "теория игр", "теории игр", "теори устойчив", "теория устойчив", "теории устойчив", "исследовани операц", "исследование операц", "исследования операц", "марковск", "ряды", "рядов", "теория автомат", "теории автомат", "конечных автомат", "многокритериальн", "системн анализ", "системного анализ", "системный анализ", "теория систем", "теории систем", "динамических систем", "теория динамических", "кватернион", "обратн задач", "обратных задач", "параметрическ идентификац", "параметрической идентификац", "логик", "главы анализа", "анализ проектных решений", "проектных решений", "теории информации", "теория информации", "теория цепей", "теории цепей"), area_vector((DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.85"), (DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.15"))),
    (("компьютер", "программ", "приложен", "компилят", "криптограф", "нейрон", "искусственн интеллект", "машинное обуч", "обучение с подкреплением", "информационн", "информации", "вычисл", "параллельн вычисл", "сетев", "сети", "операционн", "цифров", "системн программ", "сапр", "мультиагент", "интернет-технолог", "инфокоммуникацион", "верификац", "верификация", "оптимального код", "генерация код", "распределенн систем", "распределенные системы", "интеллектуальн", "рекомендательн", "экспертн систем", "системы поддержки", "защищенн компьютер", "обратная разработка", "построение систем с использованием ии", "систем ии", "програмное обеспечение", "erp", "ерp", "ит систем", "открытых источников информац"), area_vector((DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.75"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.15"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.10"))),
    (("защит информац", "защита информац", "защиты информац", "безопасн программ", "безопасн операц", "анализ защищ", "крипт", "кии", "тестировани на проникновен", "тестирование на проникновение", "антивирус", "пентест", "защищенн систем", "защищенного документооборот", "защищенного документоборота"), area_vector((DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.70"), (DisciplineAreaCode.SAFETY_DEFENSE_TRANSPORT, "0.30"))),
    (("теори поля", "динамик", "колебан", "сигнал", "оптическ", "радиофизик", "акустик", "акустическ", "физическ", "квантов", "ядерн", "атомн", "радиацион", "голограф", "относительност"), area_vector((DisciplineAreaCode.PHYSICS_ASTRONOMY, "0.70"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.30"))),
    (("автоматизац", "автоматик", "машиностроен", "мехатрон", "робот", "станк", "свароч", "литьев", "кузнеч", "промышленн", "производственн", "технологическ процесс", "конструкторск", "приборостроен", "метролог", "измерительн", "стандартиз", "сертифиц"), area_vector((DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.85"), (DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.10"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.05"))),
    (("авиац", "ракет", "космическ", "космонавтик", "космос", "спутник", "траектор", "бортов", "аэродинамик", "баллистик", "двигател", "турбин", "газодинамик", "теплотехник", "термодинамик", "гидравлик", "пневматик", "вакуумн", "энергетическ", "энергосбереж", "энергии", "топлив", "нефтегаз", "плазм", "реактор", "яэу", "яэду", "жрд", "горен", "турбулент", "криоген", "холодильн", "вентиляц", "отоплен"), area_vector((DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.70"), (DisciplineAreaCode.PHYSICS_ASTRONOMY, "0.25"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.05"))),
    (("электр", "электрон", "радио", "схемотехник", "микроэлектрон", "микропроцессор", "электроэнерг", "электромехан", "электропривод", "электродинамик", "цифровые устройств", "аналоговые фильтр"), area_vector((DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.75"), (DisciplineAreaCode.PHYSICS_ASTRONOMY, "0.15"), (DisciplineAreaCode.COMPUTER_SCIENCE_DATA, "0.10"))),
    (("материал", "металл", "сплав", "керамик", "композит", "корроз", "покрыт", "полимер", "химмотолог", "водород", "топливн элемент"), area_vector((DisciplineAreaCode.CHEMISTRY_MATERIALS, "0.60"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.40"))),
    (("оптик", "лазер", "фотометр", "колориметр", "акустик", "физическ", "квантов", "ядерн", "атомн", "радиацион"), area_vector((DisciplineAreaCode.PHYSICS_ASTRONOMY, "0.70"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.30"))),
    (("проектирован", "конструирован", "машин", "оборудован", "аппарат", "механическ", "механизм", "моделирован", "инженерн", "расчет", "расчёт", "технологи", "производств", "процессов", "процессы переноса", "техническ", "конструкц", "констурктор", "изготовлен", "обработк", "детал", "узл", "установк", "прибор", "устройств", "датчик", "энергет", "теплов", "гидромашин", "гидропривод", "гидропередач", "трубопровод", "поршнев", "компрессор", "пневмогидрав", "пневматик", "вакуум", "надежн", "эксплуатац", "диагностик", "металлореж", "сварк", "лить", "литейн", "отливк", "прокат", "резан", "термостатирован", "газоснабжен", "газовых смесей", "сжатых газ", "колесн", "летательн", "боеприпас", "прочност", "триботехник", "триболог", "подъемник", "лифты", "манипулятор", "сборк", "формообразован", "оснастк", "штампов", "испытан", "контрол", "эксперимент", "автономн объект", "автономные объекты", "рулев", "гироскоп", "гиростабилиз", "ориентац", "наведен", "локац", "телеметр", "питани", "связи", "телевиден", "помехозащит", "сотов", "антенн", "излучен", "автоматизир", "агрегат", "маневрирован", "орбит", "тепломассо", "тепломассообмен", "теплообмен", "кондиционирован", "кондиционирования", "ожижен", "разделен газов", "рабочего тела", "врд", "сау", "аиус", "пртс", "суом", "точност", "поверхност", "криолог", "естествозн", "оболоч", "упругост", "пластичност", "плаcтичност", "остаточного ресурса", "научно-техническ", "нормативное обеспеч", "норвмативн", "триз", "изобретательск задач", "решения изобретательских", "биофотон", "наносистем", "микросистем", "тепломассообмена", "возмущ", "отрывн течен", "отрывных течений"), area_vector((DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.80"), (DisciplineAreaCode.MATHEMATICS_STATISTICS, "0.15"), (DisciplineAreaCode.PHYSICS_ASTRONOMY, "0.05"))),
    (("оруж", "вооружен", "боев", "поражен", "высокоточн", "экипировк", "боевое применен", "воздушн цел", "обнаружен", "слежени", "сопровожден", "автономн наведен"), area_vector((DisciplineAreaCode.SAFETY_DEFENSE_TRANSPORT, "0.70"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.30"))),
    (("веществ", "диффуз", "хроматограф", "хромотограф", "спектроскоп", "рентгеноструктур", "микроскопическ", "межфазн", "поверхност", "ионно-пучков", "плазмы с веществом", "газовый анализ"), area_vector((DisciplineAreaCode.CHEMISTRY_MATERIALS, "0.65"), (DisciplineAreaCode.PHYSICS_ASTRONOMY, "0.20"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.15"))),
    (("математ", "алгебр", "геометр", "статист", "вероятност", "оптимизац", "исследовани операц", "дифференциальн уравнен"), area_vector((DisciplineAreaCode.MATHEMATICS_STATISTICS, "1.00"))),
    (("физик", "астроном", "оптик", "квантов", "механик"), area_vector((DisciplineAreaCode.PHYSICS_ASTRONOMY, "0.65"), (DisciplineAreaCode.ENGINEERING_TECHNOLOGY, "0.35"))),
    (("хими", "материаловед", "полимер"), area_vector((DisciplineAreaCode.CHEMISTRY_MATERIALS, "1.00"))),
    (("биолог", "биотехнолог", "генетик", "микробиолог", "биохими"), area_vector((DisciplineAreaCode.BIOLOGY_BIOTECHNOLOGY, "1.00"))),
    (("геолог", "географ", "эколог", "климат", "океанолог", "гидролог", "природопользован"), area_vector((DisciplineAreaCode.EARTH_ENVIRONMENT, "1.00"))),
    (("архитектур", "строительств", "градостро", "урбанист", "bim", "здан"), area_vector((DisciplineAreaCode.ARCHITECTURE_CONSTRUCTION, "1.00"))),
    (("агроном", "сельск", "ветеринар", "лесн хозяйств", "животновод"), area_vector((DisciplineAreaCode.AGRICULTURE_VETERINARY, "1.00"))),
    (("медицин", "медиц", "стоматолог", "фармац", "сестрин", "реабилитац", "общественн здоров"), area_vector((DisciplineAreaCode.MEDICINE_HEALTH, "1.00"))),
    (("патолог", "патофизиолог", "патоанатом", "клиническ", "терапи", "хирург"), area_vector((DisciplineAreaCode.MEDICINE_HEALTH, "1.00"))),
    (("психолог", "когнитив", "психодиагност", "самопрезентац", "командн работ", "командной работы", "командообраз"), area_vector((DisciplineAreaCode.PSYCHOLOGY_COGNITIVE, "0.65"), (DisciplineAreaCode.BUSINESS_MANAGEMENT, "0.35"))),
    (("антикорруп", "нормативно-правов", "патент", "правов", "государственн", "политическ", "дипломат", "международн отношен", "криминалист", "криминолог", "судебн", "процессуальн", "трасолог", "экспертиз", "интеллектуальн собственн"), area_vector((DisciplineAreaCode.LAW_POLICY_PUBLIC_ADMINISTRATION, "0.80"), (DisciplineAreaCode.SOCIETY_SOCIAL_SCIENCES, "0.20"))),
    (("социолог", "антрополог", "демограф", "этнограф", "социальн работ"), area_vector((DisciplineAreaCode.SOCIETY_SOCIAL_SCIENCES, "1.00"))),
    (("социальн", "коммуникац", "политическ", "общественн", "межличностн", "социокультурн"), area_vector((DisciplineAreaCode.SOCIETY_SOCIAL_SCIENCES, "0.75"), (DisciplineAreaCode.PSYCHOLOGY_COGNITIVE, "0.25"))),
    (("эконом", "финанс", "инвестиц", "банк", "миров эконом", "рынк", "отраслевых рынк", "ценн бумаг", "бирж", "акции", "облигац", "международн торгов"), area_vector((DisciplineAreaCode.ECONOMICS_FINANCE, "0.80"), (DisciplineAreaCode.BUSINESS_MANAGEMENT, "0.20"))),
    (("менеджмент", "маркетинг", "бухгалтер", "управлен", "предприним", "бизнес-процесс", "hr"), area_vector((DisciplineAreaCode.BUSINESS_MANAGEMENT, "1.00"))),
    (("бизнес", "кадров", "организаци", "планирован", "делов", "управленческ", "предприят", "производственн организац", "бюджет", "рынок", "ценн бумаг", "аудит", "ценообраз", "страхован", "актуариат", "учет", "учёт", "логистик", "лидерств", "инновацион", "командообраз", "erp", "еrp", "поведен потребител", "поведение потребител", "аналитик и прогнозирован", "аналитики и прогнозирован", "устойчивого развит", "международной торгов"), area_vector((DisciplineAreaCode.BUSINESS_MANAGEMENT, "0.75"), (DisciplineAreaCode.ECONOMICS_FINANCE, "0.25"))),
    (("прав", "юридичес", "политолог", "государственн управлен", "дипломат", "международн отношен"), area_vector((DisciplineAreaCode.LAW_POLICY_PUBLIC_ADMINISTRATION, "1.00"))),
    (("язык", "лингвист", "перевод", "филолог", "литератур", "фонетик", "морфолог", "синтаксис", "речевого общения", "дискурс", "аннотирован", "реферирован"), area_vector((DisciplineAreaCode.LANGUAGES_LINGUISTICS_LITERATURE, "1.00"))),
    (("истори", "археолог", "философ", "этик", "религиовед", "культуролог"), area_vector((DisciplineAreaCode.HISTORY_PHILOSOPHY_HUMANITIES, "1.00"))),
    (("искусств", "дизайн", "медиа", "мультимед", "журналист", "реклам", "музык", "театр", "кино", "цветоведен", "скульптур", "композици", "рисунок", "живопис", "макетирован", "копирайтинг", "творческ", "творческих идей"), area_vector((DisciplineAreaCode.ART_DESIGN_MEDIA, "1.00"))),
    (("педагог", "образовательн", "преподаван", "методик обуч", "воспитательн"), area_vector((DisciplineAreaCode.EDUCATION_PEDAGOGY, "1.00"))),
    (("физическ культур", "спорт", "туризм", "гостинич", "ресторан"), area_vector((DisciplineAreaCode.SPORT_TOURISM_HOSPITALITY, "1.00"))),
    (("безопасност", "оборона", "пожарн", "транспорт", "навигац", "защит насел"), area_vector((DisciplineAreaCode.SAFETY_DEFENSE_TRANSPORT, "1.00"))),
    (("практик", "введение в специальност", "введение в професси", "дисциплин по выбору", "дисциплина по выбору", "проектн деятельност", "проектной деятельност", "академическ", "исследовательск", "научн", "междисциплин", "методолог научн", "методология нир", "нир", "публикационн", "подготовка научных публикац", "экспертн", "вкр", "карьерн"), area_vector((DisciplineAreaCode.UNIVERSAL_INTERDISCIPLINARY, "1.00"))),
)


__all__ = ["DisciplineClassifier", "RuleBasedDisciplineClassifier"]
