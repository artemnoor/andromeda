from __future__ import annotations

from typing import Any

from .source_models import FetchedResource, utc_now


def fetch_with_browser(url: str, timeout_seconds: float = 30.0, max_body_bytes: int = 30_000_000) -> FetchedResource:
    """Рендерит JS-страницу и сохраняет JSON-ответы, если Playwright установлен."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Playwright не установлен. Выполните: pip install -e .[browser] && playwright install chromium") from exc

    payloads: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Andromeda-BMSTU-Parser/0.1 (browser mode)",
            locale="ru-RU",
            viewport={"width": 1440, "height": 1100},
        )

        def capture(response: Any) -> None:
            content_type = response.headers.get("content-type", "")
            if "json" not in content_type.lower():
                return
            try:
                body = response.body()
                if len(body) > 5_000_000:
                    return
                payloads.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "content_type": content_type,
                        "body": body.decode("utf-8", errors="replace"),
                    }
                )
            except Exception:
                return

        page.on("response", capture)
        response = page.goto(url, wait_until="domcontentloaded", timeout=int(timeout_seconds * 1000))
        try:
            page.wait_for_load_state("networkidle", timeout=int(timeout_seconds * 1000))
        except Exception:
            pass
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        html = page.content().encode("utf-8")[:max_body_bytes]
        final_url = page.url
        status_code = response.status if response is not None else 200
        browser.close()
    return FetchedResource(
        requested_url=url,
        final_url=final_url,
        status_code=status_code,
        content_type="text/html; charset=utf-8",
        body=html,
        fetched_at=utc_now(),
        access_mode="browser",
        encoding="utf-8",
        network_payloads=payloads,
        error=None,
    )
