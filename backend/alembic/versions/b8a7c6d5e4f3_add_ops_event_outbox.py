"""add_ops_event_outbox

Revision ID: b8a7c6d5e4f3
Revises: 8a9b7c6d5e4f
Create Date: 2026-04-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8a7c6d5e4f3"
down_revision: Union[str, Sequence[str], None] = "8a9b7c6d5e4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "opseventoutbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("room", sa.String(length=160), nullable=False),
        sa.Column("event_name", sa.String(length=120), nullable=False),
        sa.Column("severity", sa.String(length=8), nullable=False),
        sa.Column("payload_json", sa.String(length=4000), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
        sa.Column("dead_lettered_at", sa.DateTime(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opseventoutbox_event_id", "opseventoutbox", ["event_id"], unique=False)
    op.create_index("ix_opseventoutbox_branch_id", "opseventoutbox", ["branch_id"], unique=False)
    op.create_index("ix_opseventoutbox_room", "opseventoutbox", ["room"], unique=False)
    op.create_index("ix_opseventoutbox_event_name", "opseventoutbox", ["event_name"], unique=False)
    op.create_index("ix_opseventoutbox_severity", "opseventoutbox", ["severity"], unique=False)
    op.create_index("ix_opseventoutbox_status", "opseventoutbox", ["status"], unique=False)
    op.create_index("ix_opseventoutbox_next_attempt_at", "opseventoutbox", ["next_attempt_at"], unique=False)
    op.create_index("ix_opseventoutbox_dead_lettered_at", "opseventoutbox", ["dead_lettered_at"], unique=False)
    op.create_index("ix_opseventoutbox_occurred_at", "opseventoutbox", ["occurred_at"], unique=False)
    op.create_index("ix_opseventoutbox_sent_at", "opseventoutbox", ["sent_at"], unique=False)
    op.create_index("ix_opseventoutbox_updated_at", "opseventoutbox", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_opseventoutbox_updated_at", table_name="opseventoutbox")
    op.drop_index("ix_opseventoutbox_sent_at", table_name="opseventoutbox")
    op.drop_index("ix_opseventoutbox_occurred_at", table_name="opseventoutbox")
    op.drop_index("ix_opseventoutbox_dead_lettered_at", table_name="opseventoutbox")
    op.drop_index("ix_opseventoutbox_next_attempt_at", table_name="opseventoutbox")
    op.drop_index("ix_opseventoutbox_status", table_name="opseventoutbox")
    op.drop_index("ix_opseventoutbox_severity", table_name="opseventoutbox")
    op.drop_index("ix_opseventoutbox_event_name", table_name="opseventoutbox")
    op.drop_index("ix_opseventoutbox_room", table_name="opseventoutbox")
    op.drop_index("ix_opseventoutbox_branch_id", table_name="opseventoutbox")
    op.drop_index("ix_opseventoutbox_event_id", table_name="opseventoutbox")
    op.drop_table("opseventoutbox")
