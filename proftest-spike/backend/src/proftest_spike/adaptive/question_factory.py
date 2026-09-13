"""Create neutral adaptive questions from selected dimensions."""

from __future__ import annotations

from decimal import Decimal

from .entities import AdaptiveOption, AdaptiveQuestion, AdaptiveSelection


class AdaptiveQuestionFactory:
    def create(self, selection: AdaptiveSelection) -> AdaptiveQuestion | None:
        if selection.status != "ready" or len(selection.dimensions) != 2:
            return None
        first, second = selection.dimensions
        return AdaptiveQuestion(
            id=f"adaptive:{first.code}:{second.code}",
            prompt=f"Что тебе ближе по содержанию и способу работы: {first.label} или {second.label}?",
            helper_text="Это уточнение сравнивает направления, которые сильнее всего различаются среди найденных программ.",
            first_dimension=first,
            second_dimension=second,
            options=(
                AdaptiveOption(id="more_first", label=f"Скорее {first.label.lower()}", description="Первое направление заметно привлекательнее.", first_weight=Decimal("1"), second_weight=Decimal("0")),
                AdaptiveOption(id="balanced", label="Примерно поровну", description="Оба направления интересны примерно одинаково.", first_weight=Decimal("0.5"), second_weight=Decimal("0.5")),
                AdaptiveOption(id="more_second", label=f"Скорее {second.label.lower()}", description="Второе направление заметно привлекательнее.", first_weight=Decimal("0"), second_weight=Decimal("1")),
            ),
        )


__all__ = ["AdaptiveQuestionFactory"]
