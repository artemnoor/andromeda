from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def content_hash(body: bytes) -> str:
    return sha256(body).hexdigest()


@dataclass(slots=True)
class SourceDefinition:
    id: str
    name: str
    url: str
    officiality: str | None = None
    scope: str | None = None
    format: str | None = None
    availability: str | None = None
    method: str | None = None
    data_description: str | None = None
    history: str | None = None
    refresh: str | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FieldDefinition:
    id: int
    block: str
    name: str
    entity: str
    acquisition_status: str
    primary_source: str | None
    url: str | None
    extraction_target: str | None
    format: str | None
    recommended_method: str | None
    coverage: str | None
    reserve: str | None
    reserve_url: str | None
    history: str | None
    refresh: str | None
    reliability: str | None
    priority: str | None
    limitation: str | None
    source_ids: tuple[str, ...] = ()
    reserve_source_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_ids"] = list(self.source_ids)
        value["reserve_source_ids"] = list(self.reserve_source_ids)
        return value


@dataclass(slots=True)
class PipelineStep:
    order: int
    module: str
    sources: str | None
    output: str | None
    technology: str | None
    depends_on: str | None
    frequency: str | None
    fail_safe: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FetchedResource:
    requested_url: str
    final_url: str
    status_code: int | None
    content_type: str | None
    body: bytes
    fetched_at: str
    access_mode: str = "http"
    encoding: str | None = None
    network_payloads: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    @property
    def content_hash(self) -> str:
        return content_hash(self.body)

    @property
    def ok(self) -> bool:
        return bool(self.body) and self.status_code is not None and 200 <= self.status_code < 400 and not self.error

    def snapshot_dict(self, path: str | None = None) -> dict[str, Any]:
        return {
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "fetched_at": self.fetched_at,
            "access_mode": self.access_mode,
            "encoding": self.encoding,
            "content_hash": self.content_hash if self.body else None,
            "bytes": len(self.body),
            "path": path,
            "network_payload_count": len(self.network_payloads),
            "error": self.error,
        }


@dataclass(slots=True)
class ExtractionResult:
    source_id: str
    source_url: str
    parser: str
    captured_at: str
    records: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    links: list[dict[str, str]] = field(default_factory=list)
    text: str = ""
    network_payloads: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self, include_text: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source_id": self.source_id,
            "source_url": self.source_url,
            "parser": self.parser,
            "captured_at": self.captured_at,
            "record_count": len(self.records),
            "table_count": len(self.tables),
            "link_count": len(self.links),
            "network_payload_count": len(self.network_payloads),
            "warnings": self.warnings,
        }
        if include_text:
            data["text"] = self.text
        return data
