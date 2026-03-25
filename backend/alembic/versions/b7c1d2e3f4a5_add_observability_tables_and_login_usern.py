"""add_observability_tables_and_login_username

Revision ID: b7c1d2e3f4a5
Revises: 9a6b3c2d4e5f
Create Date: 2026-03-17 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "b7c1d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "9a6b3c2d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("loginattempt", schema=None) as batch_op:
        batch_op.add_column(sa.Column("attempted_username", sqlmodel.AutoString(length=150), nullable=False, server_default=""))

    op.create_table(
        "observabilitylogentry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sqlmodel.AutoString(length=16), nullable=False),
        sa.Column("logger_name", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("source", sqlmodel.AutoString(length=64), nullable=False),
        sa.Column("message", sqlmodel.AutoString(length=1024), nullable=False),
        sa.Column("event_code", sqlmodel.AutoString(length=128), nullable=False),
        sa.Column("request_id", sqlmodel.AutoString(length=64), nullable=False),
        sa.Column("method", sqlmodel.AutoString(length=16), nullable=False),
        sa.Column("path", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sqlmodel.AutoString(length=45), nullable=False),
        sa.Column("user_agent", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("observabilitylogentry", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_event_code"), ["event_code"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_ip_address"), ["ip_address"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_level"), ["level"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_logger_name"), ["logger_name"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_method"), ["method"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_path"), ["path"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_request_id"), ["request_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_source"), ["source"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_status_code"), ["status_code"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_timestamp"), ["timestamp"], unique=False)
        batch_op.create_index(batch_op.f("ix_observabilitylogentry_user_id"), ["user_id"], unique=False)

    op.create_table(
        "securityincident",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("signal_type", sqlmodel.AutoString(length=128), nullable=False),
        sa.Column("severity", sqlmodel.AutoString(length=16), nullable=False),
        sa.Column("status", sqlmodel.AutoString(length=16), nullable=False),
        sa.Column("title", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("summary", sqlmodel.AutoString(length=1024), nullable=False),
        sa.Column("fingerprint", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("occurrence_count", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("subject_user_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sqlmodel.AutoString(length=45), nullable=False),
        sa.Column("related_log_id", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("review_notes", sqlmodel.AutoString(length=2048), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["related_log_id"], ["observabilitylogentry.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["subject_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("securityincident", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_securityincident_actor_user_id"), ["actor_user_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_fingerprint"), ["fingerprint"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_first_seen_at"), ["first_seen_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_ip_address"), ["ip_address"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_last_seen_at"), ["last_seen_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_related_log_id"), ["related_log_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_reviewed_by"), ["reviewed_by"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_severity"), ["severity"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_signal_type"), ["signal_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_securityincident_subject_user_id"), ["subject_user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("securityincident", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_securityincident_subject_user_id"))
        batch_op.drop_index(batch_op.f("ix_securityincident_status"))
        batch_op.drop_index(batch_op.f("ix_securityincident_signal_type"))
        batch_op.drop_index(batch_op.f("ix_securityincident_severity"))
        batch_op.drop_index(batch_op.f("ix_securityincident_reviewed_by"))
        batch_op.drop_index(batch_op.f("ix_securityincident_related_log_id"))
        batch_op.drop_index(batch_op.f("ix_securityincident_last_seen_at"))
        batch_op.drop_index(batch_op.f("ix_securityincident_ip_address"))
        batch_op.drop_index(batch_op.f("ix_securityincident_id"))
        batch_op.drop_index(batch_op.f("ix_securityincident_first_seen_at"))
        batch_op.drop_index(batch_op.f("ix_securityincident_fingerprint"))
        batch_op.drop_index(batch_op.f("ix_securityincident_actor_user_id"))

    op.drop_table("securityincident")

    with op.batch_alter_table("observabilitylogentry", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_user_id"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_timestamp"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_status_code"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_source"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_request_id"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_path"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_method"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_logger_name"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_level"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_ip_address"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_id"))
        batch_op.drop_index(batch_op.f("ix_observabilitylogentry_event_code"))

    op.drop_table("observabilitylogentry")

    with op.batch_alter_table("loginattempt", schema=None) as batch_op:
        batch_op.drop_column("attempted_username")
