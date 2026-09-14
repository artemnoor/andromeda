"""Deterministic identity helpers for dynamically discovered BMSTU profiles."""

from __future__ import annotations

import re
from hashlib import sha256
from collections.abc import Iterable, Mapping

from ..contracts.errors import ContractError, ErrorCode
from ..contracts.raw import RawProgramRecord


_DIRECTION_RE = re.compile(r"\d{2}\.\d{2}\.\d{2}")
_EXPLICIT_PROFILE_RE = re.compile(r"(?P<direction>\d{2}\.\d{2}\.\d{2})[-/]?(?P<suffix>\d{2,3})(?:\s|\(|$)")


def source_identity_key(source_code: str, name: str, study_plan_url: str) -> str:
    return "|".join((normalize_source_code(source_code), normalize_text(name), study_plan_url.strip()))


def normalize_source_code(value: str) -> str:
    return " ".join(value.replace("–", "-").replace("—", "-").split())


def direction_codes(value: str) -> tuple[str, ...]:
    result: list[str] = []
    for match in _DIRECTION_RE.findall(value):
        if match not in result:
            result.append(match)
    return tuple(result)


def canonicalize_program_records(records: Iterable[RawProgramRecord]) -> tuple[RawProgramRecord, ...]:
    """Return stable canonical program codes while preserving source codes.

    BMSTU publishes both profile codes and direction-level codes. A numeric
    profile code is retained when unique; every other profile receives a
    deterministic three-digit suffix derived from source identity.
    """

    values = tuple(records)
    source_keys = [
        source_identity_key(program.source_code or program.code, program.name, str(program.study_plan_url))
        for program in values
    ]
    if len(source_keys) != len(set(source_keys)):
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, "BMSTU detail contains duplicate profile source identities")

    explicit: dict[str, set[str]] = {}
    for program in values:
        source_code = normalize_source_code(program.source_code or program.code)
        match = _EXPLICIT_PROFILE_RE.search(source_code)
        if match:
            base = match.group("direction")
            explicit.setdefault(base, set()).add(f"{base}-{match.group('suffix')}")

    assigned: dict[str, set[str]] = {direction: set(codes) for direction, codes in explicit.items()}
    canonical_by_key: dict[str, str] = {}
    sorted_values = sorted(zip(source_keys, values), key=lambda pair: pair[0])
    for key, program in sorted_values:
        source_code = normalize_source_code(program.source_code or program.code)
        matches = _EXPLICIT_PROFILE_RE.search(source_code)
        source_directions = direction_codes(program.direction_code)
        if not source_directions:
            source_directions = direction_codes(source_code)
        if not source_directions:
            raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Profile has no direction code: {source_code}")
        direction = source_directions[0]
        candidate = f"{direction}-{matches.group('suffix')}" if matches and matches.group("direction") == direction else None
        if candidate is None or candidate in canonical_by_key.values():
            digest = int(sha256(key.encode("utf-8")).hexdigest()[:12], 16)
            suffix = 100 + digest % 900
            candidate = f"{direction}-{suffix}"
            while candidate in assigned.setdefault(direction, set()):
                suffix = 100 + ((suffix - 99) % 900)
                candidate = f"{direction}-{suffix}"
            assigned[direction].add(candidate)
        else:
            assigned.setdefault(direction, set()).add(candidate)
        canonical_by_key[key] = candidate

    return tuple(
        program.model_copy(update={"code": canonical_by_key[key], "source_code": program.source_code or program.code})
        for key, program in zip(source_keys, values)
    )


def map_source_program_code(
    source_code: str,
    source_name: str | None,
    programs: Iterable[RawProgramRecord],
) -> str:
    """Map an admissions/curriculum source code to a canonical raw code."""

    values = tuple(programs)
    normalized = normalize_source_code(source_code)
    named = tuple(
        program
        for program in values
        if normalize_source_code(program.source_code or program.code) == normalized
        and (source_name is None or normalize_text(program.name) == normalize_text(source_name))
    )
    if len(named) == 1:
        return named[0].code
    if len(named) > 1:
        raise ContractError(ErrorCode.SOURCE_CONTRACT_ERROR, f"Ambiguous BMSTU source profile identity: {source_code}")
    directions = direction_codes(normalized)
    return directions[0] if directions else normalized.replace("/", "-").replace(" ", "")


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


__all__ = [
    "canonicalize_program_records",
    "direction_codes",
    "map_source_program_code",
    "normalize_source_code",
    "source_identity_key",
]
