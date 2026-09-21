"""The bot output policy is explicit and testable."""

IMAGE_TEMPLATES = frozenset({"catalog", "program", "compare", "shortlist", "chances", "radar", "curriculum", "digest", "analytics"})


def requires_image(template: str) -> bool:
    return template in IMAGE_TEMPLATES


__all__ = ["IMAGE_TEMPLATES", "requires_image"]
