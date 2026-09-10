from __future__ import annotations

from pathlib import Path

import pytest

from bmstu_parser.contracts.errors import ContractError
from bmstu_parser.tracer import TracerSource
from bmstu_parser.tracer.parser import parse_captured


def test_missing_selected_curriculum_fails_closed() -> None:
    fixture_dir = Path(__file__).parents[1] / "fixtures" / "tracer" / "raw"
    captured = TracerSource().capture(mode="fixture", fixture_dir=fixture_dir)
    without_second_document = tuple(snapshot for snapshot in captured.snapshots if "mwXCgDtAGpDWdA" not in str(snapshot.requested_url))

    with pytest.raises(ContractError, match="Could not select curriculum document"):
        parse_captured(type(captured)(without_second_document))


def test_duplicate_selected_curriculum_fails_closed() -> None:
    fixture_dir = Path(__file__).parents[1] / "fixtures" / "tracer" / "raw"
    captured = TracerSource().capture(mode="fixture", fixture_dir=fixture_dir)
    duplicate = captured.snapshots + (captured.snapshots[-1],)

    with pytest.raises(ContractError, match="Could not select curriculum document"):
        parse_captured(type(captured)(duplicate))
