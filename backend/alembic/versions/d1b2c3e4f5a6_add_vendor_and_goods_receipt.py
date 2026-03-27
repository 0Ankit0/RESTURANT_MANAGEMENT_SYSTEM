"""add_vendor_and_goods_receipt

Revision ID: d1b2c3e4f5a6
Revises: c9f4a2d1e8b7
Create Date: 2026-03-26 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "d1b2c3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "c9f4a2d1e8b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vendor",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("contact_name", sqlmodel.AutoString(length=120), nullable=True),
        sa.Column("phone", sqlmodel.AutoString(length=40), nullable=True),
        sa.Column("email", sqlmodel.AutoString(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("vendor", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_vendor_branch_id"), ["branch_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_vendor_name"), ["name"], unique=False)

    op.create_table(
        "goodsreceipt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=True),
        sa.Column("vendor_id", sa.Integer(), nullable=True),
        sa.Column("notes", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchaseorder.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendor.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("goodsreceipt", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_goodsreceipt_branch_id"), ["branch_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("goodsreceipt", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_goodsreceipt_branch_id"))
    op.drop_table("goodsreceipt")

    with op.batch_alter_table("vendor", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_vendor_name"))
        batch_op.drop_index(batch_op.f("ix_vendor_branch_id"))
    op.drop_table("vendor")
