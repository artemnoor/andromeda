from __future__ import annotations

import pytest

from andromeda_telegram.clients.backend import BackendResult
from andromeda_telegram.clients.models import Program, ProgramList
from andromeda_telegram.parsing.program_resolver import ProgramResolver, normalize_program_query, split_program_references


def program(code: str, name: str) -> Program:
    return Program(id=f"program:{code}", directionId="direction:09.03.01", code=code, name=name, educationYear=2026, studyPlanUrl="https://example.test/plan", sourceUrl="https://example.test/source")


class Backend:
    async def list_programs(self, *, session_cookie=None):
        return BackendResult(ProgramList(items=[program("09.03.01-01", "Информатика и системы"), program("09.03.01-02", "Информатика и данные")]), None)


@pytest.mark.asyncio
async def test_resolver_uses_live_catalog_and_reports_ambiguity() -> None:
    resolver = ProgramResolver(Backend())
    exact = await resolver.resolve("09.03.01-01")
    ambiguous = await resolver.resolve("информатика")

    assert exact.exact is True
    assert exact.matches[0].id == "program:09.03.01-01"
    assert ambiguous.exact is False
    assert len(ambiguous.matches) == 2


def test_program_query_normalization_and_split() -> None:
    assert normalize_program_query("  Ёлка, ИНФОРМАТИКА! ") == "елка информатика"
    assert split_program_references("сравни ПМИ МГУ и ПМИ ВШЭ") == ("ПМИ МГУ", "ПМИ ВШЭ")
