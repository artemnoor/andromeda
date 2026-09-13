"""FastAPI dependency accessors for the composed Spike services."""

from __future__ import annotations

from typing import cast

from fastapi import Request

from proftest_spike.catalog.service import CatalogService
from proftest_spike.composition.container import Container


def get_container(request: Request) -> Container:
    return cast(Container, request.app.state.container)


def get_catalog_service(request: Request) -> CatalogService:
    return get_container(request).catalog


__all__ = ["get_catalog_service", "get_container"]
