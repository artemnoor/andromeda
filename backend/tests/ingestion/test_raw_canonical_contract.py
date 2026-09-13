from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256

import pytest
from pydantic import ValidationError

from andromeda.ingestion.contracts.raw import RawCampusPointRecord, RawSourceSnapshot, SourceLocator


def test_raw_source_contract_rejects_extra_fields_and_preserves_provenance() -> None:
    body = b"fixture"
    snapshot = RawSourceSnapshot(
        source_kind="bmstu_common",
        requested_url="https://bmstu.ru/sveden/common/",
        final_url="https://bmstu.ru/sveden/common/",
        status_code=200,
        captured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        content_sha256=sha256(body).hexdigest(),
        body=body,
    )
    assert snapshot.final_url == snapshot.requested_url

    with pytest.raises(ValidationError):
        RawSourceSnapshot.model_validate({**snapshot.model_dump(), "unexpected": True})


def test_locator_is_typed_and_explicitly_nullable() -> None:
    locator = SourceLocator(source_url="https://bmstu.ru/", page=None, row=2, field=None)
    assert locator.page is None
    assert locator.row == 2


def test_raw_campus_point_contract_rejects_partial_coordinates() -> None:
    with pytest.raises(ValidationError, match="provided together"):
        RawCampusPointRecord(
            external_key="main-campus",
            point_type="building",
            name="Главный корпус",
            latitude=Decimal("55.7666"),
            longitude=None,
            university_ids=("university:bmstu",),
            source_kind="bmstu_campus_points",
            source_url="https://bmstu.ru/campus/points",
            locator=SourceLocator(source_url="https://bmstu.ru/campus/points", row=1),
        )
