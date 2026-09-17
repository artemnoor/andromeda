"""SQLAlchemy adapter for owner-scoped decision analytics."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from andromeda.modules.decision.contracts.public import DecisionAnalyticsEvent, DecisionAnalyticsWriter
from andromeda.modules.proftest.contracts.public import ProfileScope

from ..database.models import DecisionAnalyticsEventModel


logger = logging.getLogger("andromeda.infrastructure.repositories.decision_analytics")


class SqlAlchemyDecisionAnalyticsRepository(DecisionAnalyticsWriter):
    """Append-only analytics writer with TTL cleanup and per-owner dedupe."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, scope: ProfileScope, events: tuple[DecisionAnalyticsEvent, ...]) -> int:
        if not events:
            return 0
        now = _now()
        purge_result = self._session.execute(
            delete(DecisionAnalyticsEventModel).where(DecisionAnalyticsEventModel.expires_at <= now)
        )
        purged = int(getattr(purge_result, "rowcount", 0) or 0)
        if purged:
            logger.info("decision_analytics_retention_purged count=%d", purged)

        inserted = 0
        for event in events:
            if event.expires_at <= now:
                continue
            identity = (scope.owner_key, event.event_id)
            if self._session.get(DecisionAnalyticsEventModel, identity) is not None:
                continue
            model = DecisionAnalyticsEventModel(
                owner_key=scope.owner_key,
                event_id=event.event_id,
                session_key_hash=scope.session_key_hash if scope.account_id is None else None,
                account_id=scope.account_id,
                event_type=event.event_type.value,
                payload_json=event.payload.model_dump(mode="json", exclude_none=True),
                occurred_at=_utc(event.occurred_at),
                created_at=now,
                expires_at=_utc(event.expires_at),
            )
            try:
                # A savepoint makes a concurrent duplicate harmless without
                # rolling back unrelated rows in the caller's transaction.
                with self._session.begin_nested():
                    self._session.add(model)
                    self._session.flush()
                inserted += 1
            except IntegrityError:
                logger.info("decision_analytics_append_deduplicated outcome=concurrent")
        self._session.commit()
        logger.info(
            "decision_analytics_append_complete owner_kind=%s inserted=%d deduplicated=%d",
            scope.owner_kind,
            inserted,
            len(events) - inserted,
        )
        return inserted


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


__all__ = ["SqlAlchemyDecisionAnalyticsRepository"]
