from __future__ import annotations

import logging
from dataclasses import dataclass
from time import sleep

import httpx

from .source_models import FetchedResource, utc_now


logger = logging.getLogger("andromeda.ingestion.hse.fetch")


@dataclass(slots=True)
class FetchConfig:
    timeout_seconds: float = 10.0
    retries: int = 0
    retry_delay_seconds: float = 0.8
    max_body_bytes: int = 40_000_000
    user_agent: str = "Andromeda-HSE-Parser/1.0 (+official-public-sources)"


class Fetcher:
    def __init__(self, config: FetchConfig | None = None) -> None:
        self.config = config or FetchConfig()
        self.client = httpx.Client(
            follow_redirects=True,
            timeout=self.config.timeout_seconds,
            headers={"User-Agent": self.config.user_agent, "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"},
        )

    def close(self) -> None:
        self.client.close()

    def fetch_http(self, url: str) -> FetchedResource:
        last_error: str | None = None
        for attempt in range(self.config.retries + 1):
            try:
                response = self.client.get(url)
                body = response.content[: self.config.max_body_bytes]
                error = None if 200 <= response.status_code < 400 and body else f"HTTP {response.status_code} or empty body"
                return FetchedResource(
                    requested_url=url,
                    final_url=str(response.url),
                    status_code=response.status_code,
                    content_type=response.headers.get("content-type"),
                    body=body,
                    fetched_at=utc_now(),
                    error=error,
                )
            except (httpx.HTTPError, OSError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < self.config.retries:
                    sleep(self.config.retry_delay_seconds * (attempt + 1))
        return FetchedResource(url, url, None, None, b"", utc_now(), error=last_error or "unknown fetch error")

    fetch = fetch_http


__all__ = ["FetchConfig", "Fetcher", "FetchedResource"]
