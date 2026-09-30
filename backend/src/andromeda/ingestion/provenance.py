"""Helpers for retaining stable source attribution during normalization."""

from __future__ import annotations

import json
from collections.abc import Iterable

from andromeda.shared.contracts.provenance import SourceAttribution


def merge_source_attributions(*groups: Iterable[SourceAttribution]) -> tuple[SourceAttribution, ...]:
    """Merge provenance in encounter order, deduplicating by its full JSON value.

    SourceAttribution is a Pydantic contract and is intentionally not hashable,
    so it must never be used directly as a dict/set key.
    """

    unique: dict[str, SourceAttribution] = {}
    for group in groups:
        for attribution in group:
            key = json.dumps(attribution.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
            unique.setdefault(key, attribution)
    return tuple(unique.values())


__all__ = ["merge_source_attributions"]
