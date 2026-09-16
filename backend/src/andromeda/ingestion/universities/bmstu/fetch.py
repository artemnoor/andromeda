from __future__ import annotations

from dataclasses import dataclass
from time import sleep
from typing import Any

import httpx

from .html import extract_text, is_blocked_page, is_js_shell
from .source_models import FetchedResource, utc_now


@dataclass(slots=True)
class FetchConfig:
    timeout_seconds: float = 30.0
    retries: int = 2
    user_agent: str = "Andromeda-BMSTU-Parser/0.1 (+research; contact owner)"
    browser_mode: str = "auto"
    max_body_bytes: int = 30_000_000
    retry_delay_seconds: float = 0.8


class Fetcher:
    def __init__(self, config: FetchConfig | None = None) -> None:
        self.config = config or FetchConfig()
        self.client = httpx.Client(
            follow_redirects=True,
            timeout=self.config.timeout_seconds,
            headers={
                "User-Agent": self.config.user_agent,
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
        )

    def close(self) -> None:
        self.client.close()

    def fetch(self, url: str, force_browser: bool = False) -> FetchedResource:
        direct = self._fetch_http(url)
        should_use_browser = force_browser or self.config.browser_mode == "always" or (
            self.config.browser_mode == "auto"
            and (
                direct.status_code in {401, 403, 429}
                or is_js_shell(extract_text(direct.body), direct.body)
                or is_blocked_page(extract_text(direct.body), direct.body)
            )
        )
        if not should_use_browser:
            return direct

        try:
            from .browser import fetch_with_browser

            browser_result = fetch_with_browser(
                url,
                timeout_seconds=self.config.timeout_seconds,
                max_body_bytes=self.config.max_body_bytes,
            )
            if browser_result.body:
                return browser_result
            direct.error = "; ".join(filter(None, [direct.error, browser_result.error, "browser returned empty body"]))
        except Exception as exc:  # Browser is deliberately optional.
            direct.error = "; ".join(filter(None, [direct.error, f"browser fallback failed: {type(exc).__name__}: {exc}"]))
        return direct

    def fetch_http(self, url: str) -> FetchedResource:
        """Fetch a resource without browser fallback.

        Machine-readable metadata and immutable PDF downloads must not start a
        browser session merely because a CDN response resembles a JS shell.
        """
        return self._fetch_http(url)

    def _fetch_http(self, url: str) -> FetchedResource:
        last_error: str | None = None
        for attempt in range(self.config.retries + 1):
            try:
                response = self.client.get(url)
                body = response.content[: self.config.max_body_bytes]
                blocked = is_blocked_page(self._safe_text(body), body)
                error = None if response.status_code < 400 and not blocked else (
                    f"HTTP {response.status_code}" if response.status_code >= 400 else "blocked/anti-bot page"
                )
                return FetchedResource(
                    requested_url=url,
                    final_url=str(response.url),
                    status_code=response.status_code,
                    content_type=response.headers.get("content-type"),
                    body=body,
                    fetched_at=utc_now(),
                    access_mode="http",
                    encoding=response.encoding,
                    error=error,
                )
            except (httpx.HTTPError, OSError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < self.config.retries:
                    sleep(self.config.retry_delay_seconds * (attempt + 1))
        return FetchedResource(
            requested_url=url,
            final_url=url,
            status_code=None,
            content_type=None,
            body=b"",
            fetched_at=utc_now(),
            access_mode="http",
            error=last_error or "unknown fetch error",
        )

    @staticmethod
    def _safe_text(body: bytes) -> str:
        return body.decode("utf-8", errors="ignore")[:2_000_000]
