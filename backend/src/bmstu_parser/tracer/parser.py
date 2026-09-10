from __future__ import annotations

import logging
import re
from html import unescape
from pathlib import Path
from collections.abc import Mapping
from typing import cast

from bs4 import BeautifulSoup
from pydantic import ValidationError

from ..adapters.bmstu import _study_plan_records
from ..contracts.errors import ContractError, ErrorCode, ErrorDetail, details_from_validation
from ..contracts.constraints import http_url
from ..contracts.raw import (
    RawCurriculumRow,
    RawDirectionRecord,
    RawProgramRecord,
    RawTracerBundle,
    RawUniversityRecord,
    SourceLocator,
)
from ..models import FetchedResource, SourceDefinition
from ..html import parse_page
from ..contracts.domain import NormalizedTracerSnapshot
from .source import CapturedSources, TARGET_DIRECTION_CODE, TARGET_PROGRAM_CODES, TracerSource, _json_object
from .normalizer import normalize_bundle

logger = logging.getLogger("tracer.parser")


def parse_sources(
    source: TracerSource,
    mode: str = "fixture",
    fixture_dir: Path | None = None,
    program_codes: tuple[str, ...] = TARGET_PROGRAM_CODES,
) -> tuple[RawTracerBundle, NormalizedTracerSnapshot]:
    captured = source.capture(mode=mode, fixture_dir=fixture_dir)
    try:
        raw_bundle = parse_captured(captured, program_codes=program_codes)
    except ValidationError as exc:
        raise ContractError(
            ErrorCode.SOURCE_CONTRACT_ERROR,
            "Raw source data does not satisfy the parser contract",
            details_from_validation(exc.errors()),
        ) from exc
    logger.debug("parser_stage raw_dto_validated programs=%d curriculum_rows=%d", len(raw_bundle.programs), len(raw_bundle.curriculum_rows))
    try:
        normalized = normalize_bundle(raw_bundle)
    except ValidationError as exc:
        raise ContractError(
            ErrorCode.SOURCE_CONTRACT_ERROR,
            "Normalized domain data does not satisfy the domain contract",
            details_from_validation(exc.errors()),
        ) from exc
    logger.debug("parser_stage normalized programs=%d curricula=%d", len(normalized.programs), len(normalized.curricula))
    return raw_bundle, normalized


def parse_captured(captured: CapturedSources, program_codes: tuple[str, ...] = TARGET_PROGRAM_CODES) -> RawTracerBundle:
    university = _parse_university(captured.first("bmstu_common"))
    direction, programs = _parse_detail(captured.first("bmstu_major_detail"), program_codes)
    if direction.code != TARGET_DIRECTION_CODE:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Unexpected direction code in S06 detail")
    rows: list[RawCurriculumRow] = []
    for code in program_codes:
        document = _document_for_program(captured, code)
        rows.extend(_parse_curriculum(document, code))
    if set(program.code for program in programs) != set(program_codes):
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "Selected programs are incomplete")
    return RawTracerBundle(
        snapshots=captured.snapshots,
        university=university,
        direction=direction,
        programs=tuple(programs),
        curriculum_rows=tuple(rows),
    )


def _parse_university(snapshot: object) -> RawUniversityRecord:
    from ..contracts.raw import RawSourceSnapshot

    typed = cast(RawSourceSnapshot, snapshot)
    page = parse_page(typed.body, str(typed.final_url))
    soup = page.soup
    labels = page.labels
    name = _first_label(labels, "наимен", "полное") or _first_label(labels, "наимен") or _title(soup)
    if name and "Полное наименование на русском языке:" in name:
        match = re.search(
            r"Полное наименование на русском языке:\s*(.+?)(?=\s+Сокращенное наименование)",
            name,
        )
        name = match.group(1).strip() if match else name
    address = _first_label(labels, "местонахождение") or _first_label(labels, "адрес")
    city = _city(address)
    if not name or not address or not city:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "S01 university page does not contain required identity fields")
    return RawUniversityRecord(
        name=name,
        city=city,
        address=address,
        official_site=http_url("https://bmstu.ru/"),
        locator=SourceLocator(source_url=typed.requested_url),
    )


def _parse_detail(snapshot: object, program_codes: tuple[str, ...]) -> tuple[RawDirectionRecord, list[RawProgramRecord]]:
    from ..contracts.raw import RawSourceSnapshot, JsonObject
    typed = cast(RawSourceSnapshot, snapshot)
    soup = BeautifulSoup(typed.body, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script is None or not script.string:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "S06 detail page has no __NEXT_DATA__")
    root: JsonObject = _json_object(script.string.encode("utf-8"))
    data = _next_details(root)
    additional = _obj(data.get("additional"))
    direction_code = _text(additional.get("code"))
    direction_name = _text(additional.get("name"))
    if not direction_code or not direction_name:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "S06 detail has no direction identity")
    direction = RawDirectionRecord(
        code=direction_code,
        name=direction_name,
        education_level="бакалавриат",
        locator=SourceLocator(source_url=typed.requested_url),
    )
    chairs = _obj(data.get("chairs"))
    records: list[RawProgramRecord] = []
    for chair_value in _list(chairs.get("items")):
        chair = _obj(chair_value)
        educational = _obj(chair.get("educationalProgram"))
        for program_value in _list(educational.get("items")):
            program = _obj(program_value)
            code = _canonical_code(_text(program.get("code")))
            name = _text(program.get("name"))
            plan = _text(program.get("plan"))
            if code not in program_codes:
                continue
            if not name or not plan:
                raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Target program {code} is missing name or plan")
            records.append(
                RawProgramRecord(
                    code=code,
                    name=unescape(name),
                    direction_code=direction_code,
                    education_level="бакалавриат",
                    education_year=_education_year(data),
                    study_plan_url=http_url(plan),
                    source_url=typed.requested_url,
                    locator=SourceLocator(source_url=typed.requested_url),
                )
            )
    if len(records) != len(program_codes):
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "S06 detail did not contain exactly the selected programs")
    return direction, records


def _parse_curriculum(snapshot: object, program_code: str) -> list[RawCurriculumRow]:
    from ..contracts.raw import RawSourceSnapshot

    typed = cast(RawSourceSnapshot, snapshot)
    source_definition = SourceDefinition(id="S06", name="BMSTU curriculum", url=str(typed.requested_url))
    resource = FetchedResource(
        requested_url=str(typed.requested_url),
        final_url=str(typed.final_url),
        status_code=typed.status_code,
        content_type=typed.content_type,
        body=typed.body,
        fetched_at=typed.captured_at.isoformat(),
    )
    records = _study_plan_records(
        source_definition,
        resource,
        typed.captured_at.isoformat(),
        context={"program_profile_code": program_code, "study_plan_url": str(typed.requested_url)},
    )
    result: list[RawCurriculumRow] = []
    for value in records:
        if value.get("record_type") != "StudyPlan":
            continue
        record = cast(Mapping[str, object], value)
        discipline = _object_text(record.get("discipline"))
        semester = _object_int(record.get("semester"))
        hours = _object_int(record.get("hours"))
        credit_value = record.get("credits")
        credits = credit_value if isinstance(credit_value, (str, int, float)) else None
        if not discipline or hours is None:
            raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Curriculum row for {program_code} is incomplete")
        result.append(
            RawCurriculumRow(
                program_code=_object_text(record.get("program_profile_code")) or program_code,
                discipline=discipline,
                semester=semester,
                hours=hours,
                credits=credits,
                assessment=_object_text(record.get("assessment_type")),
                subject_group=_object_text(record.get("subject_group")),
                source_position=semester and (_object_int(record.get("row_no")) or None),
                source_url=typed.requested_url,
                locator=SourceLocator(source_url=typed.requested_url, row=_object_int(record.get("row_no"))),
            )
        )
    if not result:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Curriculum document for {program_code} produced no rows")
    logger.debug("parser_stage curriculum_raw program=%s rows=%d", program_code, len(result))
    return result


def _document_for_program(captured: CapturedSources, code: str) -> object:
    matches = tuple(snapshot for snapshot in captured.by_kind("bmstu_curriculum_document") if code in str(snapshot.requested_url) or code in str(snapshot.final_url) or _contains_plan_name(snapshot.body, code))
    if len(matches) == 1:
        return matches[0]
    documents = captured.by_kind("bmstu_curriculum_document")
    if len(documents) == len(TARGET_PROGRAM_CODES):
        index = TARGET_PROGRAM_CODES.index(code)
        return documents[index]
    raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Could not select curriculum document for {code}")


def _contains_plan_name(body: bytes, code: str) -> bool:
    return code in body.decode("utf-8", errors="ignore")


def _next_details(root: Mapping[str, object]) -> dict[str, object]:
    props = _obj(root.get("props"))
    initial = _obj(props.get("initialState"))
    details = _obj(initial.get("bachelorMajorsDetails"))
    return _obj(details.get("data"))


def _labels(soup: BeautifulSoup) -> dict[str, str]:
    labels: dict[str, str] = {}
    for element in soup.find_all(["dt", "dd"]):
        if element.name != "dt":
            continue
        sibling = element.find_next_sibling("dd")
        if sibling:
            key = _clean(element.get_text(" ", strip=True)).rstrip(":")
            value = _clean(sibling.get_text(" ", strip=True))
            if key and value:
                labels[key] = value
    return labels


def _first_label(labels: dict[str, str], *fragments: str) -> str | None:
    for key, value in labels.items():
        lowered = key.casefold()
        if all(fragment.casefold() in lowered for fragment in fragments):
            return value
    return None


def _title(soup: BeautifulSoup) -> str | None:
    node = soup.find("h1") or soup.find("title")
    return _clean(node.get_text(" ", strip=True)) if node else None


def _city(address: str | None) -> str | None:
    if not address:
        return None
    match = re.search(r"(?:г\.|город)\s*([^,]+)", address, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _education_year(data: dict[str, object]) -> int:
    text = _text(data.get("description")) or ""
    match = re.search(r"20\d{2}", text)
    return int(match.group(0)) if match else 2026


def _canonical_code(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace("–", "-").replace("—", "-").replace("/", "-").replace(" ", "")


def _clean(value: str) -> str:
    return " ".join(unescape(value).replace("\xa0", " ").split())


def _obj(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _object_text(value: object) -> str | None:
    return _text(value)


def _object_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
