"""add_restaurant_ops_tables

Revision ID: c9f4a2d1e8b7
Revises: b7c1d2e3f4a5
Create Date: 2026-03-26 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "c9f4a2d1e8b7"
down_revision: Union[str, Sequence[str], None] = "b7c1d2e3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "servicezone",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("servicezone", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_servicezone_branch_id"), ["branch_id"], unique=False)

    op.create_table(
        "tablegroup",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("table_ids_csv", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("tablegroup", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_tablegroup_branch_id"), ["branch_id"], unique=False)

    op.create_table(
        "attendancerecord",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("staff_user_id", sa.Integer(), nullable=False),
        sa.Column("shift_id", sa.Integer(), nullable=True),
        sa.Column("check_in_at", sa.DateTime(), nullable=False),
        sa.Column("check_out_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sqlmodel.AutoString(length=300), nullable=True),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.ForeignKeyConstraint(["shift_id"], ["shift.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("attendancerecord", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_attendancerecord_branch_id"), ["branch_id"], unique=False)

    op.create_table(
        "dayclose",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("business_date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.Enum("OPEN", "CLOSED", name="dayclosestatus"), nullable=False),
        sa.Column("closed_by", sa.Integer(), nullable=True),
        sa.Column("notes", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("dayclose", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_dayclose_branch_id"), ["branch_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("dayclose", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_dayclose_branch_id"))
    op.drop_table("dayclose")

    with op.batch_alter_table("attendancerecord", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_attendancerecord_branch_id"))
    op.drop_table("attendancerecord")

    with op.batch_alter_table("tablegroup", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_tablegroup_branch_id"))
    op.drop_table("tablegroup")

    with op.batch_alter_table("servicezone", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_servicezone_branch_id"))
    op.drop_table("servicezone")
