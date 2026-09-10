from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

import pytest
from pydantic import ValidationError

from andromeda.ingestion.contracts.raw import RawSourceSnapshot, SourceLocator


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
