from __future__ import annotations

from datetime import datetime, timezone

import pytest

from andromeda.ingestion.contracts.constraints import http_url
from andromeda.ingestion.universities.bmstu.normalizers.canonical import _append_curriculum_item
from andromeda.ingestion.universities.hse.normalizers.canonical import _append
from andromeda.modules.curricula.domain.entities import CurriculumItem
from andromeda.shared.contracts.enums import SourceKind
from andromeda.shared.contracts.provenance import SourceAttribution


@pytest.mark.parametrize(
    ("append", "university", "source_kind", "source_url"),
    (
        (_append_curriculum_item, "bmstu", SourceKind.BMSTU_CURRICULUM_DOCUMENT, "https://bmstu.ru/plan"),
        (_append, "hse", SourceKind.HSE_CURRICULUM_DOCUMENT, "https://www.hse.ru/plan"),
    ),
)
def test_duplicate_curriculum_rows_merge_unhashable_provenance(
    append,
    university: str,
    source_kind: SourceKind,
    source_url: str,
) -> None:
    captured_at = datetime(2026, 9, 30, tzinfo=timezone.utc)
    first_source = SourceAttribution(
        kind=source_kind,
        url=http_url(f"{source_url}/curriculum.pdf"),
        captured_at=captured_at,
        content_sha256="a" * 64,
    )
    second_source = SourceAttribution(
        kind=source_kind,
        url=http_url(f"{source_url}/metadata"),
        captured_at=captured_at,
        content_sha256="b" * 64,
    )
    discipline_id = "discipline:0123456789abcdef"
    program_code = "09.03.01-02"
    item_id = f"curriculum-item:program:{university}:{program_code}:{discipline_id}:1"
    first = CurriculumItem(
        id=item_id,
        discipline_id=discipline_id,
        source_name="Математический анализ",
        semester=1,
        hours=72,
        provenance=(first_source,),
    )
    repeated = first.model_copy(
        update={"hours": 36, "provenance": (first_source.model_copy(), second_source)}
    )

    items = [first]
    append(items, repeated)

    assert len(items) == 1
    assert items[0].hours == 72
    assert items[0].provenance == (first_source, second_source)
