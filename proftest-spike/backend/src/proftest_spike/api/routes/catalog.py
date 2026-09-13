"""Catalog endpoint backed by the Spike application service."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from proftest_spike.api.dependencies import get_catalog_service
from proftest_spike.api.schemas.catalog import CatalogResponse, catalog_response
from proftest_spike.catalog.service import CatalogService

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/catalog", response_model=CatalogResponse)
async def get_catalog(catalog: CatalogService = Depends(get_catalog_service)) -> CatalogResponse:
    snapshot = await catalog.get_catalog()
    return catalog_response(snapshot)


__all__ = ["router"]
