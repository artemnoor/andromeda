from __future__ import annotations

from dataclasses import dataclass

from ...shared.contracts.errors import ContractError, ErrorCode, ErrorDetail
from .raw import RawSourceSnapshot


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
                "Expected exactly one source snapshot",
                (ErrorDetail(path="source.snapshots", message=f"invalid count for {kind}", type="source_selection"),),
            )
        return matches[0]


__all__ = ["CapturedSources", "RawSourceSnapshot"]
