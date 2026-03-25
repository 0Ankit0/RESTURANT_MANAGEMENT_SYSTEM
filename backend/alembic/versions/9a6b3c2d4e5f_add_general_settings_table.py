"""add_general_settings_table

Revision ID: 9a6b3c2d4e5f
Revises: 7f6c1e8a4b2d
Create Date: 2026-03-17 12:00:00.000000

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from src.apps.core.config import (
    NON_RUNTIME_EDITABLE_SETTING_KEYS,
    get_environment_settings_snapshot,
)


# revision identifiers, used by Alembic.
revision: str = "9a6b3c2d4e5f"
down_revision: Union[str, Sequence[str], None] = "7f6c1e8a4b2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "generalsetting",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("env_value", sa.Text(), nullable=True),
        sa.Column("db_value", sa.Text(), nullable=True),
        sa.Column("use_db_value", sa.Boolean(), nullable=False),
        sa.Column("is_runtime_editable", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("generalsetting", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_generalsetting_key"), ["key"], unique=True)

    generalsetting = sa.table(
        "generalsetting",
        sa.column("key", sa.String),
        sa.column("env_value", sa.Text),
        sa.column("db_value", sa.Text),
        sa.column("use_db_value", sa.Boolean),
        sa.column("is_runtime_editable", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    now = datetime.now()
    seed_rows = [
        {
            "key": key,
            "env_value": value,
            "db_value": None,
            "use_db_value": False,
            "is_runtime_editable": key not in NON_RUNTIME_EDITABLE_SETTING_KEYS,
            "created_at": now,
            "updated_at": now,
        }
        for key, value in get_environment_settings_snapshot().items()
    ]
    op.bulk_insert(generalsetting, seed_rows)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("generalsetting", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_generalsetting_key"))

    op.drop_table("generalsetting")
