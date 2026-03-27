"""add_menu_tax_discount_refund_tables

Revision ID: e2f3a4b5c6d7
Revises: d1b2c3e4f5a6
Create Date: 2026-03-26 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "d1b2c3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "menucategory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("menucategory", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_menucategory_branch_id"), ["branch_id"], unique=False)

    op.create_table(
        "modifiergroup",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("min_select", sa.Integer(), nullable=False),
        sa.Column("max_select", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("modifiergroup", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_modifiergroup_branch_id"), ["branch_id"], unique=False)

    op.create_table(
        "modifieroption",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("modifier_group_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("extra_price", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["modifier_group_id"], ["modifiergroup.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("modifieroption", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_modifieroption_modifier_group_id"), ["modifier_group_id"], unique=False)

    op.create_table(
        "taxrule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("taxrule", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_taxrule_branch_id"), ["branch_id"], unique=False)

    op.create_table(
        "discountapproval",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("requested_by", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("discount_amount", sa.Float(), nullable=False),
        sa.Column("reason", sqlmodel.AutoString(length=300), nullable=False),
        sa.Column("status", sqlmodel.AutoString(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bill_id"], ["bill.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("discountapproval", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_discountapproval_bill_id"), ["bill_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_discountapproval_branch_id"), ["branch_id"], unique=False)

    op.create_table(
        "refund",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("settlement_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("reason", sqlmodel.AutoString(length=300), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bill_id"], ["bill.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.ForeignKeyConstraint(["settlement_id"], ["settlement.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("refund", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_refund_bill_id"), ["bill_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_refund_branch_id"), ["branch_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("refund", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_refund_branch_id"))
        batch_op.drop_index(batch_op.f("ix_refund_bill_id"))
    op.drop_table("refund")

    with op.batch_alter_table("discountapproval", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_discountapproval_branch_id"))
        batch_op.drop_index(batch_op.f("ix_discountapproval_bill_id"))
    op.drop_table("discountapproval")

    with op.batch_alter_table("taxrule", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_taxrule_branch_id"))
    op.drop_table("taxrule")

    with op.batch_alter_table("modifieroption", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_modifieroption_modifier_group_id"))
    op.drop_table("modifieroption")

    with op.batch_alter_table("modifiergroup", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_modifiergroup_branch_id"))
    op.drop_table("modifiergroup")

    with op.batch_alter_table("menucategory", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_menucategory_branch_id"))
    op.drop_table("menucategory")
