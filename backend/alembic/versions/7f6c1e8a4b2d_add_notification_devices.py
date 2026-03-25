"""Add notification device registry

Revision ID: 7f6c1e8a4b2d
Revises: 012cc4845c3b
Create Date: 2026-03-16 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "7f6c1e8a4b2d"
down_revision: Union[str, Sequence[str], None] = "012cc4845c3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "notificationdevice",
        sa.Column("provider", sqlmodel.AutoString(length=32), nullable=False),
        sa.Column("platform", sqlmodel.AutoString(length=32), nullable=False),
        sa.Column("token", sqlmodel.AutoString(length=1024), nullable=True),
        sa.Column("endpoint", sqlmodel.AutoString(length=2048), nullable=True),
        sa.Column("p256dh", sqlmodel.AutoString(length=512), nullable=True),
        sa.Column("auth", sqlmodel.AutoString(length=256), nullable=True),
        sa.Column("subscription_id", sqlmodel.AutoString(length=255), nullable=True),
        sa.Column("device_metadata", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("notificationdevice", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_notificationdevice_user_id"),
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("notificationdevice", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_notificationdevice_user_id"))

    op.drop_table("notificationdevice")
