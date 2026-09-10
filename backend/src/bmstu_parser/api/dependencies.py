from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from typing import cast
from sqlalchemy import Engine
from sqlalchemy.orm import Session


def get_engine(request: Request) -> Engine:
    return cast(Engine, request.app.state.engine)


def get_session(request: Request) -> Iterator[Session]:
    engine = get_engine(request)
    with Session(engine, autoflush=False, expire_on_commit=False) as session:
        yield session
