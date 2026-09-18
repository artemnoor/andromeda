"""HMAC-authenticated client for Next server-only OG routes."""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import httpx

from .cache import RenderCache
from ..clients.errors import RenderError


logger = logging.getLogger("andromeda_telegram.render")
SUPPORTED_TEMPLATES = {"program", "compare", "shortlist", "chances", "radar", "curriculum", "digest", "catalog"}


class RendererClient:
    def __init__(self, base_url: str, secret: str, *, timeout_seconds: float = 20.0, cache: RenderCache | None = None, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._secret = secret.encode("utf-8")
        self._timeout = timeout_seconds
        self._cache = cache or RenderCache()
        self._client = client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def render(self, template: str, params: dict[str, str], *, session_cookie: str | None = None, revision: str = "0") -> bytes:
        if template not in SUPPORTED_TEMPLATES:
            raise RenderError("unsupported render template")
        normalized = _normalize_params(params)
        scope = hashlib.sha256(session_cookie.encode("utf-8")).hexdigest()[:16] if session_cookie else "anonymous"
        key = f"v1|{template}|{normalized}|{scope}|{revision}"
        cached = self._cache.get(key)
        if cached is not None:
            logger.debug("render_cache_hit template=%s", template)
            return cached

        path = f"/og/{template}"
        timestamp = str(int(time.time()))
        signature = _signature(self._secret, "GET", path, normalized, timestamp)
        headers = {
            "X-Andromeda-Render-Timestamp": timestamp,
            "X-Andromeda-Render-Signature": signature,
        }
        if session_cookie:
            headers["Cookie"] = f"andromeda_profile_session={session_cookie}"
        try:
            if self._client is not None:
                response = await self._client.get(f"{self._base_url}{path}?{normalized}", headers=headers, timeout=self._timeout)
            else:
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.get(f"{self._base_url}{path}?{normalized}", headers=headers, timeout=self._timeout)
        except httpx.HTTPError as exc:
            raise RenderError("renderer is unavailable") from exc
        if response.status_code >= 400 or response.headers.get("content-type", "").split(";")[0].lower() != "image/png":
            raise RenderError("renderer returned an invalid image response")
        if not response.content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RenderError("renderer returned an invalid PNG")
        self._cache.put(key, response.content)
        logger.info("render_complete template=%s bytes=%d", template, len(response.content))
        return response.content


def _normalize_params(params: dict[str, str]) -> str:
    return urlencode(sorted((key, value) for key, value in params.items() if value != ""), doseq=True)


def _signature(secret: bytes, method: str, path: str, query: str, timestamp: str) -> str:
    message = f"{method}\n{path}\n{query}\n{timestamp}".encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


__all__ = ["RendererClient", "_normalize_params", "_signature"]
