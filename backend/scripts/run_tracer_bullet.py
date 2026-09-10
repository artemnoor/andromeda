"""Run the contract-first BMSTU tracer bullet ingestion."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

from alembic import command
from alembic.config import Config

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT / "src"))

from bmstu_parser.db.base import create_engine_for_url
from bmstu_parser.tracer import DEFAULT_FIXTURE_DIR, TracerSource, parse_sources
from bmstu_parser.tracer.ingest import TracerIngestService


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
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s %(name)s %(message)s")
    if args.program_codes and args.program_ids:
        parser.error("use --program-code or --program-id, not both")
    if args.program_ids:
        program_codes = tuple(value.removeprefix("program:") for value in args.program_ids)
    else:
        program_codes = tuple(args.program_codes) if args.program_codes else ("09.03.01-02", "09.03.01-12")
    if args.database_url.startswith("sqlite:///") and ":memory:" not in args.database_url:
        database_path = Path(args.database_url.removeprefix("sqlite:///"))
        database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine_for_url(args.database_url)
    migration_config = Config(str(BACKEND_ROOT / "alembic.ini"))
    migration_config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    migration_config.set_main_option("sqlalchemy.url", args.database_url.replace("%", "%%"))
    command.upgrade(migration_config, "head")
    raw, normalized = parse_sources(
        TracerSource(),
        mode=args.mode,
        fixture_dir=args.fixture_dir,
        program_codes=program_codes,
    )
    run_id = TracerIngestService(engine).ingest(raw, normalized)
    print(
        json.dumps(
            {
                "runId": run_id,
                "programIds": [program.id for program in normalized.programs],
                "curriculumItemCount": sum(len(curriculum.items) for curriculum in normalized.curricula),
                "sourceCount": len(normalized.sources),
                "sourceHashes": [source.content_sha256 for source in normalized.sources],
                "databaseUrl": args.database_url,
                "api": {
                    "docs": "/docs",
                    "openapi": "/openapi.json",
                    "program": "/programs/{id}",
                    "curriculum": "/programs/{id}/curriculum",
                    "compare": "/compare?programIds=program:09.03.01-02,program:09.03.01-12",
                },
                "frontend": "http://localhost:5173/",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
