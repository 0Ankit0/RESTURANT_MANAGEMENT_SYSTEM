"""add_branch_bootstrap_and_audit_tables

Revision ID: 4f9a7b6c5d4e
Revises: f3a4b5c6d7e8
Create Date: 2026-04-09 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f9a7b6c5d4e"
down_revision: Union[str, Sequence[str], None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "branchpaymentmethod",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_branchpaymentmethod_branch_id", "branchpaymentmethod", ["branch_id"], unique=False)

    op.create_table(
        "branchprinter",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("target", sa.String(length=200), nullable=False),
        sa.Column("zone", sa.String(length=80), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_branchprinter_branch_id", "branchprinter", ["branch_id"], unique=False)

    op.create_table(
        "kitchenstation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("is_expo", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_kitchenstation_branch_id", "kitchenstation", ["branch_id"], unique=False)

    op.create_table(
        "privilegedactionaudit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("payload_json", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_privilegedactionaudit_branch_id", "privilegedactionaudit", ["branch_id"], unique=False)
    op.create_index("ix_privilegedactionaudit_action", "privilegedactionaudit", ["action"], unique=False)
    op.create_index("ix_privilegedactionaudit_actor_user_id", "privilegedactionaudit", ["actor_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_privilegedactionaudit_actor_user_id", table_name="privilegedactionaudit")
    op.drop_index("ix_privilegedactionaudit_action", table_name="privilegedactionaudit")
    op.drop_index("ix_privilegedactionaudit_branch_id", table_name="privilegedactionaudit")
    op.drop_table("privilegedactionaudit")

    op.drop_index("ix_kitchenstation_branch_id", table_name="kitchenstation")
    op.drop_table("kitchenstation")

    op.drop_index("ix_branchprinter_branch_id", table_name="branchprinter")
    op.drop_table("branchprinter")

    op.drop_index("ix_branchpaymentmethod_branch_id", table_name="branchpaymentmethod")
    op.drop_table("branchpaymentmethod")
