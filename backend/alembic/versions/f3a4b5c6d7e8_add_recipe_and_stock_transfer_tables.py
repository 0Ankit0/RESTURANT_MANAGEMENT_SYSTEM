"""add_recipe_and_stock_transfer_tables

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-03-26 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a4b5c6d7e8"
down_revision: Union[str, Sequence[str], None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recipe",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recipe_branch_id", "recipe", ["branch_id"], unique=False)

    op.create_table(
        "recipeitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredient.id"]),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipe.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recipeitem_recipe_id", "recipeitem", ["recipe_id"], unique=False)
    op.create_index("ix_recipeitem_ingredient_id", "recipeitem", ["ingredient_id"], unique=False)

    op.create_table(
        "stocktransfer",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("from_branch_id", sa.Integer(), nullable=False),
        sa.Column("to_branch_id", sa.Integer(), nullable=False),
        sa.Column("from_ingredient_id", sa.Integer(), nullable=False),
        sa.Column("to_ingredient_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["from_branch_id"], ["branch.id"]),
        sa.ForeignKeyConstraint(["to_branch_id"], ["branch.id"]),
        sa.ForeignKeyConstraint(["from_ingredient_id"], ["ingredient.id"]),
        sa.ForeignKeyConstraint(["to_ingredient_id"], ["ingredient.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stocktransfer_from_branch_id", "stocktransfer", ["from_branch_id"], unique=False)
    op.create_index("ix_stocktransfer_to_branch_id", "stocktransfer", ["to_branch_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_stocktransfer_to_branch_id", table_name="stocktransfer")
    op.drop_index("ix_stocktransfer_from_branch_id", table_name="stocktransfer")
    op.drop_table("stocktransfer")

    op.drop_index("ix_recipeitem_ingredient_id", table_name="recipeitem")
    op.drop_index("ix_recipeitem_recipe_id", table_name="recipeitem")
    op.drop_table("recipeitem")

    op.drop_index("ix_recipe_branch_id", table_name="recipe")
    op.drop_table("recipe")
