from __future__ import annotations

from andromeda_telegram.flows.policy import IMAGE_TEMPLATES, requires_image


def test_structured_templates_are_image_first() -> None:
    assert {"compare", "shortlist", "chances", "radar", "curriculum", "digest", "analytics"}.issubset(IMAGE_TEMPLATES)
    assert all(requires_image(template) for template in IMAGE_TEMPLATES)
    assert not requires_image("confirmation")
