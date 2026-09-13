"""Storage-independent read ports for recommendation data."""

from __future__ import annotations

from typing import Protocol

from andromeda.modules.proftest.contracts.public import ProgramFingerprint


class ProgramFingerprintReader(Protocol):
    """Read canonical, curriculum-backed fingerprints without storage details."""

    def list_fingerprints(self) -> tuple[ProgramFingerprint, ...]: ...


RecommendationCatalogReader = ProgramFingerprintReader

__all__ = ["ProgramFingerprintReader", "RecommendationCatalogReader"]
