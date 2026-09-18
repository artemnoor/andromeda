"""Operational live-source health check; never used by pull-request CI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from dataclasses import asdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from andromeda.infrastructure.config import Settings, redact_database_url  # noqa: E402
from run_andromeda_ingestion import run_university  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Check live official university sources and fail closed on structural drift")
    parser.add_argument("--database-url")
    parser.add_argument("--min-relative-count", type=float, default=None)
    args = parser.parse_args()
    settings = Settings.from_environment(args.database_url)
    results = []
    for university in ("bmstu", "hse"):
        results.append(
            run_university(
                university=university,
                mode="live",
                fixture_dir=None,
                database_url=settings.database_url,
                program_codes=None,
                minimum_ratio=settings.ingestion_min_relative_count if args.min_relative_count is None else args.min_relative_count,
            )
        )
    print(json.dumps({"databaseTarget": redact_database_url(settings.database_url), "results": [asdict(result) for result in results]}, default=str, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
