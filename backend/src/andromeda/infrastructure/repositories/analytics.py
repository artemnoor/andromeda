"""Batch SQLAlchemy adapter for rebuildable analytical projections."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from hashlib import sha256

from sqlalchemy import delete, insert, select

from andromeda.modules.admissions.contracts.public import AdmissionOffering
from andromeda.modules.analytics.contracts.public import (
    ProgramProjection,
    ProjectionBuild,
    ProjectionDataQuality,
    ProjectionDataQualityStatus,
    ProjectionMetric,
    ProjectionMetricEvidence,
    ProjectionTimeline,
    WorkloadSummary,
)
from andromeda.modules.analytics.domain.basis import MetricBasis
from andromeda.modules.analytics.repository.ports import (
    ProgramProjectionReader,
    ProgramProjectionStore,
)
from andromeda.modules.analytics.repository.queries import ProjectionQueryReader
from andromeda.modules.semantic.contracts.public import (
    SemanticClassificationEvidence,
)
from andromeda.shared.contracts.provenance import SourceAttribution, SourceGapReference

from ..database.models import (
    ProgramMetricEvidenceModel,
    ProgramMetricModel,
    ProgramProjectionModel,
)
from ..database.session import session_factory


class SqlAlchemyProgramProjectionRepository(ProgramProjectionStore, ProgramProjectionReader, ProjectionQueryReader):
    def __init__(self, engine) -> None:
        self._factory = session_factory(engine)

    def save(self, builds: Iterable[ProjectionBuild]) -> None:
        builds_tuple = tuple(builds)
        if not builds_tuple:
            return
        program_ids = tuple(build.projection.program_id for build in builds_tuple)
        with self._factory() as session, session.begin():
            session.execute(delete(ProgramMetricEvidenceModel).where(ProgramMetricEvidenceModel.program_id.in_(program_ids)))
            session.execute(delete(ProgramMetricModel).where(ProgramMetricModel.program_id.in_(program_ids)))
            session.execute(delete(ProgramProjectionModel).where(ProgramProjectionModel.program_id.in_(program_ids)))
            session.execute(insert(ProgramProjectionModel), [_projection_mapping(build.projection) for build in builds_tuple])
            metric_rows = [
                _metric_mapping(build.projection.program_id, build.projection, metric)
                for build in builds_tuple
                for metric in build.projection.semantic_features.values()
            ]
            if metric_rows:
                session.execute(insert(ProgramMetricModel), metric_rows)
            evidence_rows = [
                _evidence_mapping(build, evidence)
                for build in builds_tuple
                for evidence in build.evidence
            ]
            if evidence_rows:
                session.execute(insert(ProgramMetricEvidenceModel), evidence_rows)

    def get(self, program_id: str) -> ProgramProjection | None:
        return next(iter(self.list(program_ids=(program_id,))), None)

    def list(self, *, program_ids: tuple[str, ...] = ()) -> tuple[ProgramProjection, ...]:
        with self._factory() as session:
            query = select(ProgramProjectionModel)
            if program_ids:
                query = query.where(ProgramProjectionModel.program_id.in_(program_ids))
            projection_rows = session.scalars(query.order_by(ProgramProjectionModel.program_code)).all()
            if not projection_rows:
                return ()
            ids = tuple(row.program_id for row in projection_rows)
            metric_rows = session.scalars(select(ProgramMetricModel).where(ProgramMetricModel.program_id.in_(ids))).all()
        metrics_by_program: dict[str, list[ProgramMetricModel]] = defaultdict(list)
        for row in metric_rows:
            metrics_by_program[row.program_id].append(row)
        return tuple(_to_projection(row, metrics_by_program.get(row.program_id, ())) for row in projection_rows)

    def evidence(
        self,
        program_ids: tuple[str, ...],
        *,
        metric_codes: tuple[str, ...],
        schema_version: str,
    ):
        if not program_ids or not metric_codes:
            return ()
        with self._factory() as session:
            rows = session.scalars(
                select(ProgramMetricEvidenceModel).where(
                    ProgramMetricEvidenceModel.program_id.in_(program_ids),
                    ProgramMetricEvidenceModel.metric_code.in_(metric_codes),
                    ProgramMetricEvidenceModel.schema_version == schema_version,
                )
            ).all()
        return tuple(_to_evidence(row) for row in rows)


def _projection_mapping(projection: ProgramProjection) -> dict[str, object]:
    quality = projection.quality
    return {
        "program_id": projection.program_id,
        "university_id": projection.university_id,
        "direction_id": projection.direction_id,
        "program_code": projection.program_code,
        "program_name": projection.program_name,
        "schema_version": projection.schema_version,
        "basis": projection.workload.basis.value,
        "total_hours": projection.workload.total_hours,
        "total_credits": projection.workload.total_credits,
        "total_workload": projection.workload.total_workload,
        "academic_areas_json": _dump(projection.academic_areas),
        "timeline_json": _dump(projection.timeline),
        "activity_signals_json": _dump(projection.activity_signals),
        "assessment_json": _dump(projection.assessment),
        "admission_offerings_json": _dump(projection.admission_offerings),
        "distinctive_subjects_json": _dump(projection.distinctive_subjects),
        "quality_status": quality.status.value,
        "coverage": quality.coverage,
        "confidence": quality.confidence,
        "freshness_at": quality.freshness_at or datetime.now(UTC),
        "semantic_version": quality.semantic_version,
        "classifier_version": quality.classifier_version,
        "ingest_run_id": projection.ingest_run_id,
        "provenance_json": _dump(projection.provenance),
        "source_gaps_json": _dump(projection.source_gaps),
        "built_at": datetime.now(UTC),
    }


def _metric_mapping(program_id: str, projection: ProgramProjection, metric: ProjectionMetric) -> dict[str, object]:
    return {
        "program_id": program_id,
        "metric_code": metric.code,
        "schema_version": projection.schema_version,
        "value": metric.value,
        "unit": metric.unit,
        "basis": metric.basis.value if metric.basis else None,
        "coverage": metric.coverage,
        "confidence": metric.confidence,
        "status": metric.status.value,
        "semantic_version": projection.quality.semantic_version,
        "classifier_version": projection.quality.classifier_version,
        "provenance_json": _dump(metric.provenance),
        "source_gaps_json": _dump(metric.source_gaps),
        "built_at": datetime.now(UTC),
    }


def _evidence_mapping(build: ProjectionBuild, evidence) -> dict[str, object]:
    key = f"{build.projection.program_id}:{evidence.metric_code}:{evidence.curriculum_item_id}:{evidence.feature_id}:{evidence.schema_version}"
    return {
        "id": f"projection-evidence:{sha256(key.encode('utf-8')).hexdigest()[:32]}",
        "program_id": evidence.program_id,
        "metric_code": evidence.metric_code,
        "schema_version": evidence.schema_version,
        "curriculum_item_id": evidence.curriculum_item_id,
        "feature_id": evidence.feature_id,
        "contribution": evidence.contribution,
        "source_hash": evidence.source_hash,
        "evidence_json": _dump(evidence.evidence),
        "provenance_json": _dump(evidence.provenance),
    }


def _to_projection(row: ProgramProjectionModel, metrics: Iterable[ProgramMetricModel]) -> ProgramProjection:
    metric_values = {
        metric.metric_code: ProjectionMetric(
            code=metric.metric_code,
            value=metric.value,
            unit=metric.unit,
            basis=MetricBasis(metric.basis) if metric.basis else None,
            coverage=metric.coverage,
            confidence=metric.confidence,
            status=ProjectionDataQualityStatus(metric.status),
            provenance=tuple(SourceAttribution.model_validate(item, strict=False) for item in _load_list(metric.provenance_json)),
            source_gaps=tuple(SourceGapReference.model_validate(item, strict=False) for item in _load_list(metric.source_gaps_json)),
        )
        for metric in metrics
    }
    return ProgramProjection.model_validate(
        {
            "schema_version": row.schema_version,
            "program_id": row.program_id,
            "university_id": row.university_id,
            "direction_id": row.direction_id,
            "program_code": row.program_code,
            "program_name": row.program_name,
            "workload": WorkloadSummary(
                total_hours=row.total_hours,
                total_credits=row.total_credits,
                total_workload=row.total_workload,
                basis=MetricBasis(row.basis),
            ),
            "academic_areas": json.loads(row.academic_areas_json),
            "semantic_features": metric_values,
            "timeline": ProjectionTimeline.model_validate(json.loads(row.timeline_json), strict=False),
            "activity_signals": json.loads(row.activity_signals_json),
            "assessment": json.loads(row.assessment_json),
            "admission_offerings": tuple(
                AdmissionOffering.model_validate(item, strict=False)
                for item in _load_list(row.admission_offerings_json)
            ),
            "distinctive_subjects": tuple(_load_list(row.distinctive_subjects_json)),
            "quality": ProjectionDataQuality(
                status=ProjectionDataQualityStatus(row.quality_status),
                coverage=row.coverage,
                confidence=row.confidence,
                freshness_at=row.freshness_at,
                semantic_version=row.semantic_version,
                classifier_version=row.classifier_version,
            ),
            "provenance": tuple(SourceAttribution.model_validate(item, strict=False) for item in _load_list(row.provenance_json)),
            "source_gaps": tuple(SourceGapReference.model_validate(item, strict=False) for item in _load_list(row.source_gaps_json)),
            "ingest_run_id": row.ingest_run_id,
        },
        strict=False,
    )


def _to_evidence(row: ProgramMetricEvidenceModel):
    evidence = json.loads(row.evidence_json)
    provenance = json.loads(row.provenance_json)
    return ProjectionMetricEvidence(
        program_id=row.program_id,
        metric_code=row.metric_code,
        schema_version=row.schema_version,
        curriculum_item_id=row.curriculum_item_id,
        feature_id=row.feature_id,
        contribution=row.contribution,
        source_hash=row.source_hash,
        evidence=tuple(SemanticClassificationEvidence.model_validate(item, strict=False) for item in evidence),
        provenance=tuple(SourceAttribution.model_validate(item, strict=False) for item in provenance),
    )


def _dump(value: object) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    elif isinstance(value, tuple):
        value = [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in value]
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _load_list(value: str) -> list:
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError("projection JSON value must be a list")
    return parsed


__all__ = ["SqlAlchemyProgramProjectionRepository"]
