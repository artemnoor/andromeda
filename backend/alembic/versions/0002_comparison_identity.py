"""Preserve source names and make nullable semester identities explicit."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0002_comparison_identity"
down_revision = "0001_tracer_bullet"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("curriculum_items")}
    check_names = {check["name"] for check in inspector.get_check_constraints("curriculum_items")}
    if "source_name" not in columns:
        op.add_column("curriculum_items", sa.Column("source_name", sa.String(256), nullable=True, server_default=""))
    if "semester_identity" not in columns:
        op.add_column("curriculum_items", sa.Column("semester_identity", sa.String(16), nullable=True, server_default="unassigned"))

    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE curriculum_items "
            "SET source_name = COALESCE((SELECT name FROM disciplines WHERE disciplines.id = curriculum_items.discipline_id), 'legacy') "
            "WHERE source_name IS NULL OR source_name = ''"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE curriculum_items "
            "SET semester_identity = CASE WHEN semester IS NULL THEN 'legacy:' || id ELSE 'semester:' || CAST(semester AS TEXT) END"
        )
    )
    with op.batch_alter_table("curriculum_items", recreate="always") as batch:
        batch.alter_column("source_name", existing_type=sa.String(256), nullable=False, server_default=None)
        batch.alter_column("semester_identity", existing_type=sa.String(16), nullable=False, server_default=None)
        if "ck_item_semester_identity" in check_names:
            batch.drop_constraint("ck_item_semester_identity", type_="check")
        batch.create_check_constraint(
            "ck_item_semester_identity",
            "semester_identity = 'unassigned' OR semester_identity LIKE 'legacy:%' OR semester_identity = 'semester:' || semester",
        )
        batch.drop_constraint("uq_curriculum_item_identity", type_="unique")
        batch.create_unique_constraint("uq_curriculum_item_identity", ["curriculum_id", "discipline_id", "semester_identity"])


def downgrade() -> None:
    with op.batch_alter_table("curriculum_items", recreate="always") as batch:
        batch.drop_constraint("uq_curriculum_item_identity", type_="unique")
        batch.create_unique_constraint("uq_curriculum_item_identity", ["curriculum_id", "discipline_id", "semester"])
        batch.drop_column("semester_identity")
        batch.drop_column("source_name")
