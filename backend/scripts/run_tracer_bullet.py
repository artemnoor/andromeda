"""Run the contract-first BMSTU tracer bullet ingestion."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from alembic import command
from alembic.config import Config

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT / "src"))

from andromeda.ingestion.universities.bmstu import DEFAULT_FIXTURE_DIR, BmstuUniversityAdapter
from andromeda.infrastructure.database import create_engine_for_url
from andromeda.infrastructure.repositories.ingestion import SqlAlchemyIngestionRepository

DEFAULT_PROGRAM_CODES = ("09.03.01-02", "09.03.01-12")
logger = logging.getLogger("tracer.runner")
_CONFIGURED_LOG_LEVEL = logging.INFO


@dataclass(frozen=True, slots=True)
class TracerRunResult:
    run_id: str
    program_ids: tuple[str, ...]
    curriculum_item_count: int
    source_count: int
    source_hashes: tuple[str, ...]


def configure_logging(log_level: str) -> None:
    global _CONFIGURED_LOG_LEVEL
    selected_level = os.environ.get("LOG_LEVEL", log_level).upper()
    _CONFIGURED_LOG_LEVEL = getattr(logging, selected_level, logging.INFO)
    logging.basicConfig(level=_CONFIGURED_LOG_LEVEL, format="%(levelname)s %(name)s %(message)s")
    _restore_tracer_loggers()


def _restore_tracer_loggers() -> None:
    """Alembic's fileConfig disables existing loggers; keep tracer diagnostics live."""
    logging.getLogger().setLevel(_CONFIGURED_LOG_LEVEL)
    for name, candidate in logging.Logger.manager.loggerDict.items():
        if name == "tracer" or name.startswith("tracer."):
            if isinstance(candidate, logging.Logger):
                candidate.disabled = False


def selected_program_codes(program_codes: Sequence[str] | None, program_ids: Sequence[str] | None) -> tuple[str, ...]:
    if program_codes and program_ids:
        raise ValueError("use --program-code or --program-id, not both")
    if program_ids:
        return tuple(value.removeprefix("program:") for value in program_ids)
    return tuple(program_codes) if program_codes else DEFAULT_PROGRAM_CODES


def run_ingest(
    *,
    mode: str,
    fixture_dir: Path,
    database_url: str,
    program_codes: Sequence[str],
) -> TracerRunResult:
    """Run source capture, contract parsing, migration, and domain ingestion once."""
    if database_url.startswith("sqlite:///") and ":memory:" not in database_url:
        database_path = Path(database_url.removeprefix("sqlite:///"))
        database_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("ingest_start mode=%s programs=%s database=%s", mode, ",".join(program_codes), database_url)
    engine = create_engine_for_url(database_url)
    try:
        migration_config = Config(str(BACKEND_ROOT / "alembic.ini"))
        migration_config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
        migration_config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
        command.upgrade(migration_config, "head")
        _restore_tracer_loggers()

        source = BmstuUniversityAdapter()
        try:
            raw, normalized = source.parse_sources(
                mode=mode,
                fixture_dir=fixture_dir,
                program_codes=program_codes,
            )
        finally:
            source.close()

        run_id = SqlAlchemyIngestionRepository(engine).ingest(raw, normalized)
        result = TracerRunResult(
            run_id=run_id,
            program_ids=tuple(program.id for program in normalized.programs),
            curriculum_item_count=sum(len(curriculum.items) for curriculum in normalized.curricula),
            source_count=len(normalized.sources),
            source_hashes=tuple(source.content_sha256 for source in normalized.sources),
        )
        logger.info(
            "ingest_complete run_id=%s programs=%d curriculum_items=%d sources=%d",
            result.run_id,
            len(result.program_ids),
            result.curriculum_item_count,
            result.source_count,
        )
        return result
    finally:
        engine.dispose()


def result_payload(result: TracerRunResult, database_url: str) -> dict[str, object]:
    return {
        "runId": result.run_id,
        "programIds": list(result.program_ids),
        "curriculumItemCount": result.curriculum_item_count,
        "sourceCount": result.source_count,
        "sourceHashes": list(result.source_hashes),
        "databaseUrl": database_url,
        "api": {
            "docs": "/docs",
            "openapi": "/openapi.json",
            "program": "/programs/{id}",
            "curriculum": "/programs/{id}/curriculum",
            "compare": "/compare?programIds=program:09.03.01-02,program:09.03.01-12",
        },
        "frontend": "http://localhost:5173/",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest official BMSTU data through the tracer bullet contracts")
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    parser.add_argument("--database-url", default="sqlite:///./data/tracer.db")
    parser.add_argument("--program-code", action="append", dest="program_codes")
    parser.add_argument("--program-id", action="append", dest="program_ids")
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)
    try:
        program_codes = selected_program_codes(args.program_codes, args.program_ids)
    except ValueError as exc:
        parser.error(str(exc))
    result = run_ingest(
        mode=args.mode,
        fixture_dir=args.fixture_dir,
        database_url=args.database_url,
        program_codes=program_codes,
    )
    print(json.dumps(result_payload(result, args.database_url), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
