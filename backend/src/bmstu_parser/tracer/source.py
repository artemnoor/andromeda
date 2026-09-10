from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import cast
from urllib.parse import quote

from bs4 import BeautifulSoup

from ..fetch import FetchConfig, Fetcher
from ..models import FetchedResource
from ..pdf import is_pdf
from ..contracts.errors import ContractError, ErrorCode, ErrorDetail
from ..contracts.constraints import http_url
from ..contracts.raw import JsonObject, JsonValue, RawSourceSnapshot

logger = logging.getLogger("tracer.source.fetch")
selection_logger = logging.getLogger("tracer.source.select")

S01_URL = "https://bmstu.ru/sveden/common/"
S06_CATALOG_URL = "https://bmstu.ru/bachelor/majors"
S06_API_URL = "https://api.www.bmstu.ru/majors/baccalaureate-and-specialty?limit=100&offset=0"
S06_DETAIL_URL = "https://bmstu.ru/bachelor/majors/informatika-i-vycislitelnaa-tehnika-090301"
TARGET_PROGRAM_CODES = ("09.03.01-02", "09.03.01-12")
TARGET_DIRECTION_CODE = "09.03.01"
DEFAULT_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "tracer" / "raw"


@dataclass(frozen=True, slots=True)
class CapturedSources:
    snapshots: tuple[RawSourceSnapshot, ...]

    def by_kind(self, kind: str) -> tuple[RawSourceSnapshot, ...]:
        return tuple(snapshot for snapshot in self.snapshots if snapshot.source_kind == kind)

    def first(self, kind: str) -> RawSourceSnapshot:
        matches = self.by_kind(kind)
        if len(matches) != 1:
            raise ContractError(
                ErrorCode.SOURCE_CONTRACT_ERROR,
                f"Expected exactly one source snapshot for {kind}, found {len(matches)}",
                [ErrorDetail(path="source.snapshots", message=f"invalid count for {kind}", type="source_selection")],
            )
        return matches[0]


def write_fixture(captured: CapturedSources, fixture_dir: Path) -> None:
    """Persist a captured source set with hashes and stable public provenance."""
    fixture_dir.mkdir(parents=True, exist_ok=True)
    snapshots: list[dict[str, object]] = []
    used_names: dict[str, int] = {}
    for snapshot in captured.snapshots:
        base_name = {
            "bmstu_common": "common",
            "bmstu_major_catalog": "catalog",
            "bmstu_major_detail": "detail",
            "bmstu_curriculum_document": "curriculum",
        }.get(snapshot.source_kind, "source")
        index = used_names.get(base_name, 0)
        used_names[base_name] = index + 1
        suffix = f"_{index + 1}" if index else ""
        extension = ".pdf" if is_pdf(snapshot.body) else (".json" if snapshot.content_type and "json" in snapshot.content_type else ".html")
        body_path = f"{base_name}{suffix}{extension}"
        (fixture_dir / body_path).write_bytes(snapshot.body)
        snapshots.append(
            {
                "source_kind": snapshot.source_kind,
                "requested_url": str(snapshot.requested_url),
                "final_url": str(snapshot.requested_url),
                "status_code": snapshot.status_code,
                "content_type": snapshot.content_type,
                "captured_at": snapshot.captured_at.isoformat(),
                "content_sha256": snapshot.content_sha256,
                "body_path": body_path,
            }
        )
    (fixture_dir / "source_manifest.json").write_text(
        json.dumps({"snapshots": snapshots}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class TracerSource:
    def __init__(self, fetcher: Fetcher | None = None) -> None:
        self.fetcher = fetcher or Fetcher(FetchConfig(browser_mode="auto"))
        self._owns_fetcher = fetcher is None

    def close(self) -> None:
        if self._owns_fetcher:
            self.fetcher.close()

    def capture(self, mode: str = "fixture", fixture_dir: Path | None = None) -> CapturedSources:
        logger.info("source_capture_start mode=%s", mode)
        if mode == "fixture":
            captured = self._load_fixture(fixture_dir or DEFAULT_FIXTURE_DIR)
        elif mode == "live":
            captured = self._capture_live()
        else:
            raise ContractError(
                ErrorCode.VALIDATION_ERROR,
                "source mode must be fixture or live",
                [ErrorDetail(path="mode", message="unsupported source mode", type="value_error")],
            )
        logger.info("source_capture_complete snapshot_count=%d", len(captured.snapshots))
        return captured

    def _capture_live(self) -> CapturedSources:
        snapshots: list[RawSourceSnapshot] = []
        snapshots.append(self._fetch_snapshot("bmstu_common", S01_URL))
        snapshots.append(self._fetch_snapshot("bmstu_major_catalog", S06_CATALOG_URL))
        snapshots.append(self._fetch_snapshot("bmstu_major_catalog", S06_API_URL))
        detail = self._fetch_snapshot("bmstu_major_detail", S06_DETAIL_URL)
        snapshots.append(detail)

        plans = _target_plan_urls(detail.body)
        selection_logger.debug("target_plan_candidates count=%d", len(plans))
        if set(plans) != set(TARGET_PROGRAM_CODES):
            missing = sorted(set(TARGET_PROGRAM_CODES) - set(plans))
            raise ContractError(
                ErrorCode.SOURCE_CONTRACT_ERROR,
                "Official detail page did not expose both target study plans",
                [ErrorDetail(path="programs", message=f"missing target codes: {missing}", type="source_selection")],
            )
        for code in TARGET_PROGRAM_CODES:
            snapshots.append(self._fetch_public_document(code, plans[code]))
        return CapturedSources(tuple(snapshots))

    def _fetch_public_document(self, code: str, public_url: str) -> RawSourceSnapshot:
        metadata_url = "https://cloud-api.yandex.net/v1/disk/public/resources?public_key=" + quote(public_url, safe="")
        metadata = self.fetcher.fetch(metadata_url)
        if metadata.error or not metadata.body:
            raise ContractError(
                ErrorCode.SOURCE_CONTRACT_ERROR,
                f"Could not resolve study plan for {code}",
                [ErrorDetail(path=f"programs[{code}].study_plan_url", message="document metadata unavailable", type="source_fetch")],
            )
        payload = _json_object(metadata.body)
        embedded = _object(payload.get("_embedded"))
        items = _list(embedded.get("items")) if embedded else []
        direct_url: str | None = None
        for item in items:
            item_object = _object(item)
            if item_object is None:
                continue
            direct_url = _text(item_object.get("file"))
            if direct_url:
                break
        if not direct_url:
            raise ContractError(
                ErrorCode.SOURCE_CONTRACT_ERROR,
                f"Could not resolve a document file for {code}",
                [ErrorDetail(path=f"programs[{code}].study_plan_url", message="no downloadable document", type="source_shape")],
            )
        resource = self.fetcher.fetch(direct_url)
        return self._snapshot("bmstu_curriculum_document", public_url, resource)

    def _fetch_snapshot(self, kind: str, url: str) -> RawSourceSnapshot:
        resource = self.fetcher.fetch(url)
        return self._snapshot(kind, url, resource)

    @staticmethod
    def _snapshot(kind: str, public_url: str, resource: FetchedResource) -> RawSourceSnapshot:
        if resource.error or resource.status_code is None or not resource.body:
            raise ContractError(
                ErrorCode.SOURCE_CONTRACT_ERROR,
                f"Source fetch failed for {public_url}",
                [ErrorDetail(path="source", message="source returned no valid body", type="source_fetch")],
            )
        digest = sha256(resource.body).hexdigest()
        logger.info(
            "source_fetched kind=%s host_path=%s status=%s bytes=%d sha256=%s access_mode=%s",
            kind,
            public_url.split("?", 1)[0],
            resource.status_code,
            len(resource.body),
            digest,
            resource.access_mode,
        )
        return RawSourceSnapshot(
            source_kind=kind,
            requested_url=http_url(public_url),
            final_url=http_url(resource.final_url or public_url),
            status_code=resource.status_code,
            content_type=resource.content_type,
            captured_at=datetime.fromisoformat(resource.fetched_at),
            content_sha256=digest,
            body=resource.body,
        )

    @staticmethod
    def _load_fixture(fixture_dir: Path) -> CapturedSources:
        manifest_path = fixture_dir / "source_manifest.json"
        if not manifest_path.exists():
            raise ContractError(
                ErrorCode.SOURCE_CONTRACT_ERROR,
                f"Source fixture manifest not found: {manifest_path}",
                [ErrorDetail(path="fixture_dir", message="missing source_manifest.json", type="source_fixture")],
            )
        manifest = _json_object(manifest_path.read_bytes())
        snapshots_value = _list(manifest.get("snapshots"))
        snapshots: list[RawSourceSnapshot] = []
        for index, value in enumerate(snapshots_value):
            item = _object(value)
            if item is None:
                raise ContractError(
                    ErrorCode.SOURCE_CONTRACT_ERROR,
                    "Fixture manifest contains a non-object snapshot",
                    [ErrorDetail(path=f"snapshots[{index}]", message="object expected", type="source_fixture")],
                )
            body_path = _text(item.get("body_path"))
            if not body_path:
                raise ContractError(
                    ErrorCode.SOURCE_CONTRACT_ERROR,
                    "Fixture snapshot has no body path",
                    [ErrorDetail(path=f"snapshots[{index}].body_path", message="required", type="source_fixture")],
                )
            body_file = (fixture_dir / body_path).resolve()
            if fixture_dir.resolve() not in body_file.parents:
                raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Fixture body path escapes fixture directory")
            body = body_file.read_bytes()
            digest = sha256(body).hexdigest()
            expected = _text(item.get("content_sha256"))
            if digest != expected:
                raise ContractError(
                    ErrorCode.SOURCE_CONTRACT_ERROR,
                    "Fixture body hash does not match manifest",
                    [ErrorDetail(path=f"snapshots[{index}].content_sha256", message="hash mismatch", type="source_fixture")],
                )
            snapshots.append(
                RawSourceSnapshot(
                    source_kind=_required_text(item, "source_kind", index),
                    requested_url=http_url(_required_text(item, "requested_url", index)),
                    final_url=http_url(_required_text(item, "final_url", index)),
                    status_code=_required_int(item, "status_code", index),
                    content_type=_text(item.get("content_type")),
                    captured_at=_required_datetime(item, "captured_at", index),
                    content_sha256=digest,
                    body=body,
                )
            )
        return CapturedSources(tuple(snapshots))


def _target_plan_urls(body: bytes) -> dict[str, str]:
    soup = BeautifulSoup(body, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script is None or not script.string:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "S06 detail page has no __NEXT_DATA__")
    root = _json_object(script.string.encode("utf-8"))
    props = _object(root.get("props"))
    initial_state = _object(props.get("initialState")) if props else None
    details = _object(initial_state.get("bachelorMajorsDetails")) if initial_state else None
    data = _object(details.get("data")) if details else None
    chairs = _object(data.get("chairs")) if data else None
    result: dict[str, str] = {}
    for chair_value in _list(chairs.get("items")) if chairs else []:
        chair = _object(chair_value)
        educational = _object(chair.get("educationalProgram")) if chair else None
        for program_value in _list(educational.get("items")) if educational else []:
            program = _object(program_value)
            code = _canonical_code(_text(program.get("code"))) if program else None
            plan = _text(program.get("plan")) if program else None
            if code in TARGET_PROGRAM_CODES and plan:
                if code in result and result[code] != plan:
                    raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Ambiguous plan URL for {code}")
                result[code] = plan
    return result


def _canonical_code(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace("–", "-").replace("—", "-").replace("/", "-").replace(" ", "")


def _json_object(body: bytes) -> JsonObject:
    try:
        value: JsonValue = cast(JsonValue, json.loads(body.decode("utf-8-sig")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Source JSON is malformed") from exc
    result = _object(value)
    if result is None:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Source JSON root must be an object")
    return result


def _object(value: JsonValue | object) -> JsonObject | None:
    return value if isinstance(value, dict) else None


def _list(value: JsonValue | object) -> list[JsonValue]:
    return value if isinstance(value, list) else []


def _text(value: JsonValue | object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _required_text(item: JsonObject, key: str, index: int) -> str:
    value = _text(item.get(key))
    if not value:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Fixture field {key} is missing at index {index}")
    return value


def _required_int(item: JsonObject, key: str, index: int) -> int:
    value = item.get(key)
    if not isinstance(value, int):
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Fixture field {key} must be an integer at index {index}")
    return value


def _required_datetime(item: JsonObject, key: str, index: int) -> datetime:
    value = _required_text(item, key, index)
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Fixture field {key} is not an ISO datetime") from exc
