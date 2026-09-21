"""Validation of typed analytics queries against the metric allow-list."""

from __future__ import annotations

from pydantic import TypeAdapter, ValidationError

from andromeda.shared.contracts.errors import ContractError, ErrorCode
from andromeda.shared.contracts.ids import DirectionId, ProgramId, UniversityId

from ..contracts.metrics import MetricEntityType
from ..contracts.query import FilterKind, QueryScope, QuerySpec
from .metric_registry import MetricRegistry


def validate_query_spec(spec: QuerySpec, registry: MetricRegistry | None = None) -> QuerySpec:
    selected = registry or MetricRegistry()
    try:
        for metric in spec.metrics:
            selected.get(metric, entity_type=spec.entity, aggregation=spec.aggregation)
        if spec.sort is not None:
            selected.get(spec.sort.metric_code or "", entity_type=spec.entity)
        for query_filter in spec.filters:
            _validate_filter(query_filter, selected, spec.entity)
        _validate_scope_ids(spec)
    except ContractError:
        raise
    except (ValidationError, ValueError) as exc:
        raise ContractError(ErrorCode.INVALID_QUERY, "Analytics query does not satisfy typed bounds") from exc
    return spec


def _validate_scope_ids(spec: QuerySpec) -> None:
    if spec.scope is QueryScope.ALL and spec.scope_ids:
        raise ContractError(ErrorCode.INVALID_QUERY, "all scope cannot contain scope ids")
    if spec.scope is QueryScope.UNIVERSITY:
        _validate_ids(spec.scope_ids, UniversityId)
    elif spec.scope is QueryScope.DIRECTION:
        _validate_ids(spec.scope_ids, DirectionId)
    elif spec.scope is QueryScope.PROGRAM:
        _validate_ids(spec.scope_ids, ProgramId)


def _validate_filter(query_filter, registry: MetricRegistry, entity: MetricEntityType) -> None:
    if query_filter.kind is FilterKind.UNIVERSITY:
        _validate_ids(query_filter.ids, UniversityId)
    elif query_filter.kind is FilterKind.DIRECTION:
        _validate_ids(query_filter.ids, DirectionId)
    elif query_filter.kind is FilterKind.PROGRAM:
        _validate_ids(query_filter.ids, ProgramId)
    elif query_filter.kind is FilterKind.METRIC_THRESHOLD:
        registry.get(query_filter.metric_code or "", entity_type=entity)
    elif query_filter.kind is FilterKind.SEMANTIC_THRESHOLD:
        code = query_filter.feature_code or ""
        if not code.replace("_", "").isalnum() or not code[0].islower():
            raise ContractError(ErrorCode.INVALID_QUERY, "semantic threshold feature code is malformed")


def _validate_ids(values: tuple[str, ...], annotation) -> None:
    adapter = TypeAdapter(annotation)
    for value in values:
        try:
            adapter.validate_python(value, strict=True)
        except ValidationError as exc:
            raise ContractError(ErrorCode.INVALID_QUERY, "query ids must be canonical") from exc


__all__ = ["validate_query_spec"]
