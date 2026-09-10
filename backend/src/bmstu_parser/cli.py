from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .pipeline import ParserConfig, run_parser
from .report import merge_runs
from .source_map import SourceMap


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Парсер source map МГТУ им. Н.Э. Баумана для Andromeda")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser("inspect-map", help="Проверить Excel-схему и вывести её сводку")
    inspect.add_argument("--map", required=True, dest="source_map", type=Path)

    run = subparsers.add_parser("run", help="Запустить сбор источников и сформировать JSONL-выгрузку")
    run.add_argument("--map", required=True, dest="source_map", type=Path)
    run.add_argument("--out", required=True, dest="output_dir", type=Path)
    run.add_argument(
        "--source",
        action="append",
        default=[],
        help="ID/название источника; можно указать несколько раз или передать S01,S10",
    )
    run.add_argument("--browser", choices=("never", "auto", "always"), default="auto")
    run.add_argument("--timeout", type=float, default=30.0, dest="timeout_seconds")
    run.add_argument("--retries", type=int, default=2)
    run.add_argument("--max-body-mb", type=int, default=30)
    run.add_argument(
        "--download-documents",
        action="store_true",
        help="Скачать найденные JSON/PDF/DOC-документы и разобрать PDF; ограничивается --max-followups",
    )
    run.add_argument("--max-followups", type=int, default=500)
    run.add_argument("--followup-depth", type=int, default=4)
    run.add_argument(
        "--priority-pdf",
        action="append",
        default=[],
        type=Path,
        help="Официальный PDF с приоритетными данными приёма; можно указать несколько раз",
    )

    merge = subparsers.add_parser("merge", help="Объединить несколько запусков в одну выгрузку")
    merge.add_argument("--run", action="append", required=True, dest="run_dirs", type=Path)
    merge.add_argument("--out", required=True, dest="output_dir", type=Path)
    merge.add_argument(
        "--priority-pdf",
        action="append",
        default=[],
        type=Path,
        help="Добавить приоритетный PDF поверх объединённых запусков",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "inspect-map":
        source_map = SourceMap.from_xlsx(args.source_map)
        print(json.dumps(source_map.summary(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "merge":
        summary = merge_runs(args.run_dirs, args.output_dir, priority_pdfs=args.priority_pdf)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    requested_sources = tuple(
        token.strip()
        for item in args.source
        for token in item.split(",")
        if token.strip()
    )
    summary = run_parser(
        ParserConfig(
            source_map=args.source_map,
            output_dir=args.output_dir,
            sources=requested_sources,
            browser_mode=args.browser,
            timeout_seconds=args.timeout_seconds,
            retries=max(0, args.retries),
            max_body_bytes=max(1, args.max_body_mb) * 1_000_000,
            download_documents=args.download_documents,
            max_followups=max(0, args.max_followups),
            followup_depth=max(1, args.followup_depth),
            priority_pdfs=tuple(args.priority_pdf),
        )
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0
