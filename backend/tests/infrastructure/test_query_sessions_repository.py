from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from andromeda.infrastructure.database import Base, create_engine_for_url
from andromeda.infrastructure.repositories.query_sessions import (
    SqlAlchemyQuerySessionRepository,
)
from andromeda.modules.conversation.contracts.public import QuerySession
from andromeda.modules.conversation.services.engine import ConversationEngine
from andromeda.modules.proftest.contracts.public import ProfileScope
from andromeda.shared.contracts.errors import ConflictError
from sqlalchemy.orm import Session

NOW = datetime.now(UTC) - timedelta(minutes=1)


def _session(scope: ProfileScope) -> QuerySession:
    return QuerySession(
        session_id="query-session:" + "e" * 32,
        owner_scope=scope,
        created_at=NOW,
        updated_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )


def test_query_session_repository_is_owner_bound_revisioned_and_bindable(tmp_path: Path) -> None:
    engine = create_engine_for_url(f"sqlite:///{(tmp_path / 'query-sessions.db').as_posix()}")
    Base.metadata.create_all(engine)
    anonymous = ProfileScope(session_key_hash="f" * 64)
    other = ProfileScope(session_key_hash="0" * 64)
    try:
        with Session(engine) as database_session:
            repository = SqlAlchemyQuerySessionRepository(database_session)
            created = repository.save(_session(anonymous))
            assert repository.get(created.session_id, owner_scope=other) is None
            assert repository.get(created.session_id, owner_scope=anonymous) is not None

            updated = ConversationEngine().apply(created, "Куда я прохожу с 270?", now=NOW + timedelta(seconds=1))
            repository.save(updated, expected_revision=1)
            with pytest.raises(ConflictError):
                repository.save(updated, expected_revision=1)

            bound = repository.bind_anonymous_to_account(
                updated.session_id,
                anonymous_scope=anonymous,
                account_id="account:" + "1" * 32,
            )
            assert bound.owner_scope.account_id == "account:" + "1" * 32
            assert repository.get(bound.session_id, owner_scope=anonymous) is None
            assert repository.get(bound.session_id, owner_scope=bound.owner_scope) is not None
    finally:
        engine.dispose()
