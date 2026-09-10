"""Dependency composition for the stateless Spike runtime."""

from __future__ import annotations

from dataclasses import dataclass

from proftest_spike.api_client.client import AndromedaApiClient
from proftest_spike.catalog.service import CatalogService
from proftest_spike.profiling.profile_builder import UserProfileBuilder
from proftest_spike.questions.service import QuestionService

from .settings import Settings


@dataclass(slots=True)
class Container:
    settings: Settings
    andromeda: AndromedaApiClient
    catalog: CatalogService
    questions: QuestionService
    profile_builder: UserProfileBuilder

    async def close(self) -> None:
        await self.andromeda.aclose()


def build_container(settings: Settings | None = None) -> Container:
    resolved = settings or Settings.from_environment()
    andromeda = AndromedaApiClient(
            resolved.andromeda_api_base_url,
            timeout_seconds=resolved.http_timeout_seconds,
            max_programs=resolved.max_programs,
        )
    return Container(
        settings=resolved,
        andromeda=andromeda,
        catalog=CatalogService(andromeda, ttl_seconds=resolved.catalog_cache_ttl_seconds),
        questions=QuestionService(),
        profile_builder=UserProfileBuilder(QuestionService().list_base()),
    )


__all__ = ["Container", "build_container"]
