from pathlib import Path

import pytest

from bmstu_parser.source_map import SourceMap


ATTACHMENT = Path(
    r"C:\CodexData\codex-remote-attachments\01a07b88-2a5c-7720-b7f9-1f23f222065b\3B848D00-E50F-42E4-AC18-EE21DA8E9754\1-Andromeda_BMSTU_source_map_2026.xlsx"
)


@pytest.mark.skipif(not ATTACHMENT.exists(), reason="исходный Excel не подключён к окружению")
def test_loads_all_source_map_sections() -> None:
    source_map = SourceMap.from_xlsx(ATTACHMENT)
    assert len(source_map.sources) == 19
    assert len(source_map.fields) == 177
    assert len(source_map.pipeline) == 15
    assert source_map.resolve_source_ids("S10") == ("S10",)
    assert source_map.resolve_source_ids("Стоимость высшего образования") == ("S10",)
    # Вычисляемые и системные поля в карте намеренно не имеют внешнего источника.
    assert sum(not field.source_ids and not field.reserve_source_ids for field in source_map.fields) == 16
