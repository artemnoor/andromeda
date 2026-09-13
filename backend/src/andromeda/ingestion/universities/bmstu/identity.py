"""Deterministic resolution of BMSTU source identities to public programs."""

from __future__ import annotations

from collections.abc import Sequence

from andromeda.modules.programs.contracts.public import Program
from andromeda.shared.contracts.errors import ContractError, ErrorCode

from .mappings.admissions import normalize_code


def resolve_programs(
    source_code: str,
    *,
    source_name: str | None,
    scope: str,
    programs: Sequence[Program],
) -> tuple[Program, ...]:
    """Resolve exact profile or explicit direction-level source identities.

    Direction-level source facts may be projected to every profile under that
    direction, but only when the source explicitly declares that scope. A
    program-level row with several possible names is rejected rather than
    guessed.
    """
    code = normalize_code(source_code)
    exact = tuple(program for program in programs if normalize_code(program.code) == code)
    if exact:
        return exact

    direction_matches = tuple(
        program for program in programs if normalize_code(program.code).startswith(f"{code}-")
    )
    if scope == "direction" and direction_matches:
        return direction_matches

    if scope == "program" and source_name:
        name = _normalize_name(source_name)
        named = tuple(program for program in direction_matches if _normalize_name(program.name) == name)
        if len(named) == 1:
            return named

    reason = "unknown program identity" if not direction_matches else "ambiguous program identity"
    raise ContractError(
        ErrorCode.SOURCE_CONTRACT_ERROR,
        f"BMSTU admission row has {reason}: {code}",
    )


def _normalize_name(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


__all__ = ["resolve_programs"]
