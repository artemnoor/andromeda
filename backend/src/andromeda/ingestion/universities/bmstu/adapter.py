from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from bmstu_parser.contracts.raw import RawSourceSnapshot as LegacyRawSourceSnapshot
from bmstu_parser.tracer.normalizer import normalize_bundle as normalize_legacy_bundle
from bmstu_parser.tracer.parser import parse_captured as parse_legacy_captured
from bmstu_parser.tracer.source import CapturedSources as LegacyCapturedSources
from bmstu_parser.tracer.source import TracerSource as LegacyTracerSource

from ...contracts.normalized import CanonicalSnapshot
from ...contracts.raw import RawTracerBundle
from ...contracts.source import CapturedSources, RawSourceSnapshot
from ....modules.disciplines.contracts.public import Discipline
from ....modules.disciplines.services.classifier import RuleBasedDisciplineClassifier
from .selectors import DEFAULT_FIXTURE_DIR, TARGET_PROGRAM_CODES, select_program_codes
from .mappings.discipline_areas import BMSTU_DISCIPLINE_AREA_OVERRIDES


fetch_logger = logging.getLogger("andromeda.ingestion.bmstu.fetch")
select_logger = logging.getLogger("andromeda.ingestion.bmstu.select")
parse_logger = logging.getLogger("andromeda.ingestion.bmstu.parse")
normalize_logger = logging.getLogger("andromeda.ingestion.bmstu.normalize")


class BmstuUniversityAdapter:
    """Typed BMSTU boundary around the existing source/parser implementation.

    The legacy parser is used as a compatibility engine during migration. Its
    output is immediately revalidated into ingestion-owned raw and canonical
    DTOs, so no legacy model escapes this adapter.
    """

    def __init__(self, fetcher: object | None = None) -> None:
        self._source = LegacyTracerSource(fetcher=fetcher)  # type: ignore[arg-type]
        self._classifier = RuleBasedDisciplineClassifier(BMSTU_DISCIPLINE_AREA_OVERRIDES)

    def close(self) -> None:
        self._source.close()

    def capture(self, mode: str = "fixture", fixture_dir: Path | None = None) -> CapturedSources:
        fetch_logger.debug("stage=capture mode=%s", mode)
        legacy_captured = self._source.capture(mode=mode, fixture_dir=fixture_dir or DEFAULT_FIXTURE_DIR)
        snapshots = tuple(RawSourceSnapshot.model_validate(snapshot.model_dump()) for snapshot in legacy_captured.snapshots)
        result = CapturedSources(snapshots=snapshots)
        fetch_logger.info("stage=capture_complete mode=%s snapshots=%d", mode, len(result.snapshots))
        return result

    def parse(
        self,
        captured: CapturedSources,
        program_codes: Sequence[str] = TARGET_PROGRAM_CODES,
    ) -> tuple[RawTracerBundle, CanonicalSnapshot]:
        selected = select_program_codes(tuple(program_codes))
        legacy_snapshots = tuple(LegacyRawSourceSnapshot.model_validate(snapshot.model_dump()) for snapshot in captured.snapshots)
        legacy_captured = LegacyCapturedSources(snapshots=legacy_snapshots)
        select_logger.debug("stage=selected source_snapshots=%d programs=%d", len(legacy_snapshots), len(selected))
        parse_logger.debug("stage=parse source_snapshots=%d programs=%d", len(legacy_snapshots), len(selected))
        legacy_raw = parse_legacy_captured(legacy_captured, program_codes=selected)
        raw = RawTracerBundle.model_validate(legacy_raw.model_dump())
        legacy_canonical = normalize_legacy_bundle(legacy_raw)
        canonical = CanonicalSnapshot.model_validate(legacy_canonical.model_dump())
        classified_disciplines = tuple(
            Discipline.model_validate(
                {
                    **discipline.model_dump(),
                    "area_weights": self._classifier.classify(discipline.name),
                }
            )
            for discipline in canonical.disciplines
        )
        canonical = CanonicalSnapshot.model_validate(
            {**canonical.model_dump(), "disciplines": classified_disciplines}
        )
        area_count = len({weight.area for discipline in canonical.disciplines for weight in discipline.area_weights})
        normalize_logger.info(
            "stage=canonical_complete programs=%d disciplines=%d curricula=%d items=%d areas=%d",
            len(canonical.programs),
            len(canonical.disciplines),
            len(canonical.curricula),
            sum(len(curriculum.items) for curriculum in canonical.curricula),
            area_count,
        )
        return raw, canonical

    def parse_sources(
        self,
        mode: str = "fixture",
        fixture_dir: Path | None = None,
        program_codes: Sequence[str] = TARGET_PROGRAM_CODES,
    ) -> tuple[RawTracerBundle, CanonicalSnapshot]:
        captured = self.capture(mode=mode, fixture_dir=fixture_dir)
        return self.parse(captured, program_codes=program_codes)


__all__ = ["BmstuUniversityAdapter"]
