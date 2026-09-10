"""create contract-first tracer bullet schema

Revision ID: 0001_tracer_bullet
Revises:
"""

from __future__ import annotations

from alembic import op

from bmstu_parser.db.base import Base
from bmstu_parser.db import models as _models

revision = "0001_tracer_bullet"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
