"""fix_casbin_table_name

Revision ID: 181485a25604
Revises: eec72f00ab92
Create Date: 2026-02-24 18:57:06.426252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '181485a25604'
down_revision: Union[str, Sequence[str], None] = 'eec72f00ab92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename casbinrule → casbin_rule to match what casbin-async-sqlalchemy-adapter expects."""
    # Drop indexes on the wrongly-named table first (SQLite requires this before rename)
    with op.batch_alter_table('casbinrule', schema=None) as batch_op:
        batch_op.drop_index('ix_casbinrule_ptype')
        batch_op.drop_index('ix_casbinrule_v0')
        batch_op.drop_index('ix_casbinrule_v1')
        batch_op.drop_index('ix_casbinrule_v2')

    op.rename_table('casbinrule', 'casbin_rule')

    # Re-create indexes under the correct table name
    with op.batch_alter_table('casbin_rule', schema=None) as batch_op:
        batch_op.create_index('ix_casbin_rule_ptype', ['ptype'], unique=False)
        batch_op.create_index('ix_casbin_rule_v0', ['v0'], unique=False)
        batch_op.create_index('ix_casbin_rule_v1', ['v1'], unique=False)
        batch_op.create_index('ix_casbin_rule_v2', ['v2'], unique=False)


def downgrade() -> None:
    """Rename casbin_rule → casbinrule (reverses the fix)."""
    with op.batch_alter_table('casbin_rule', schema=None) as batch_op:
        batch_op.drop_index('ix_casbin_rule_ptype')
        batch_op.drop_index('ix_casbin_rule_v0')
        batch_op.drop_index('ix_casbin_rule_v1')
        batch_op.drop_index('ix_casbin_rule_v2')

    op.rename_table('casbin_rule', 'casbinrule')

    with op.batch_alter_table('casbinrule', schema=None) as batch_op:
        batch_op.create_index('ix_casbinrule_ptype', ['ptype'], unique=False)
        batch_op.create_index('ix_casbinrule_v0', ['v0'], unique=False)
        batch_op.create_index('ix_casbinrule_v1', ['v1'], unique=False)
        batch_op.create_index('ix_casbinrule_v2', ['v2'], unique=False)
