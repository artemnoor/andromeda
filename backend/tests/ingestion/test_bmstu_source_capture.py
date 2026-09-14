from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote, urlparse

from bmstu_parser.models import FetchedResource
from bmstu_parser.tracer.source import TracerSource, _is_supported_download_url, _is_supported_public_plan_url


class _FakeFetcher:
    def __init__(self) -> None:
        self.plan_files = {
            "https://disk.yandex.ru/d/plan-a": "https://storage.yandex.net/plan-a.pdf",
            "https://disk.yandex.ru/d/plan-b": "https://storage.yandex.net/plan-b.pdf",
            "https://disk.yandex.ru/d/plan-empty": None,
        }

    def close(self) -> None:
        return None

    def fetch(self, url: str, force_browser: bool = False) -> FetchedResource:
        del force_browser
        return self._resource(url, b"<html>official BMSTU shell</html>", "text/html")

    def fetch_http(self, url: str) -> FetchedResource:
        if url.startswith("https://api.www.bmstu.ru/majors/baccalaureate-and-specialty?"):
            body = {
                "data": [
                    {"slug": "direction-one"},
                    {"slug": "direction-two"},
                    {"slug": "direction-three"},
                ],
                "meta": {"count": 3},
            }
            return self._resource(url, json.dumps(body).encode(), "application/json")
        if url.startswith("https://api.www.bmstu.ru/majors/"):
            slug = url.rsplit("/", 1)[-1]
            plans = {
                "direction-one": ("09.03.01-01", "Профиль 1", "https://disk.yandex.ru/d/plan-a"),
                "direction-two": ("09.03.01-02", "Профиль 2", "https://clck.ru/plan-b"),
                "direction-three": ("09.03.01-03", "Профиль 3", "https://disk.yandex.ru/d/plan-empty"),
            }
            code, name, plan = plans[slug]
            body = {
                "additional": {"code": "09.03.01", "name": "Информатика"},
                "chairs": {"items": [{"educationalProgram": {"items": [{"code": code, "name": name, "plan": plan}]}}]},
            }
            return self._resource(url, json.dumps(body).encode(), "application/json")
        if url == "https://clck.ru/plan-b":
            return self._resource(url, b"redirect", "text/html", final_url="https://disk.yandex.ru/d/plan-b")
        if url.startswith("https://cloud-api.yandex.net/v1/disk/public/resources?"):
            public_key = unquote(parse_qs(urlparse(url).query)["public_key"][0])
            direct_url = self.plan_files[public_key]
            payload: dict[str, object] = {"type": "file" if direct_url else "dir"}
            if direct_url:
                payload["file"] = direct_url
            return self._resource(url, json.dumps(payload).encode(), "application/json")
        if url.startswith("https://storage.yandex.net/"):
            return self._resource(url, b"%PDF-1.7 synthetic study plan", "application/pdf")
        raise AssertionError(f"unexpected fake fetch: {url}")

    @staticmethod
    def _resource(url: str, body: bytes, content_type: str, *, final_url: str | None = None) -> FetchedResource:
        return FetchedResource(
            requested_url=url,
            final_url=final_url or url,
            status_code=200,
            content_type=content_type,
            body=body,
            fetched_at=datetime(2026, 9, 14, tzinfo=timezone.utc).isoformat(),
        )


def test_live_capture_discovers_details_and_public_plan_variants() -> None:
    source = TracerSource(fetcher=_FakeFetcher())
    try:
        captured = source.capture(mode="live")
    finally:
        source.close()

    details = captured.by_kind("bmstu_major_detail")
    metadata = captured.by_kind("bmstu_curriculum_metadata")
    documents = captured.by_kind("bmstu_curriculum_document")
    assert len(details) == 3
    assert len(metadata) == 3
    assert len(documents) == 2
    assert {str(snapshot.requested_url) for snapshot in details} == {
        "https://api.www.bmstu.ru/majors/direction-one",
        "https://api.www.bmstu.ru/majors/direction-two",
        "https://api.www.bmstu.ru/majors/direction-three",
    }
    assert {str(snapshot.requested_url) for snapshot in documents} == {
        "https://disk.yandex.ru/d/plan-a",
        "https://clck.ru/plan-b",
    }


def test_public_plan_allowlist_is_https_and_official_only() -> None:
    assert _is_supported_public_plan_url("https://disk.yandex.ru/d/plan")
    assert _is_supported_public_plan_url("https://clck.ru/plan")
    assert not _is_supported_public_plan_url("http://disk.yandex.ru/d/plan")
    assert not _is_supported_public_plan_url("https://example.com/plan")
    assert _is_supported_download_url("https://s1.storage.yandex.net/file.pdf")
    assert not _is_supported_download_url("http://s1.storage.yandex.net/file.pdf")
    assert not _is_supported_download_url("https://example.com/file.pdf")
