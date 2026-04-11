"""backfill_restaurant_core_schema

Revision ID: 8a9b7c6d5e4f
Revises: 4f9a7b6c5d4e
Create Date: 2026-04-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "8a9b7c6d5e4f"
down_revision: Union[str, Sequence[str], None] = "4f9a7b6c5d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "branch",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("tax_rate", sa.Float(), nullable=False),
        sa.Column("service_charge_rate", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_branch_name", "branch", ["name"], unique=False)

    op.create_table(
        "restauranttable",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("code", sqlmodel.AutoString(length=32), nullable=False),
        sa.Column("seats", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("available", "occupied", "reserved", "out_of_service", name="tablestatus"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_restauranttable_branch_id", "restauranttable", ["branch_id"], unique=False)
    op.create_index("ix_restauranttable_code", "restauranttable", ["code"], unique=False)

    op.create_table(
        "reservation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("guest_name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("guest_phone", sqlmodel.AutoString(length=40), nullable=False),
        sa.Column("party_size", sa.Integer(), nullable=False),
        sa.Column("reservation_time", sa.DateTime(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.Enum("pending", "confirmed", "seated", "cancelled", name="reservationstatus"), nullable=False),
        sa.Column("notes", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.ForeignKeyConstraint(["table_id"], ["restauranttable.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reservation_branch_id", "reservation", ["branch_id"], unique=False)

    op.create_table(
        "menuitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_menuitem_branch_id", "menuitem", ["branch_id"], unique=False)
    op.create_index("ix_menuitem_name", "menuitem", ["name"], unique=False)

    op.create_table(
        "ingredient",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("unit", sqlmodel.AutoString(length=20), nullable=False),
        sa.Column("quantity_on_hand", sa.Float(), nullable=False),
        sa.Column("reorder_threshold", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingredient_branch_id", "ingredient", ["branch_id"], unique=False)
    op.create_index("ix_ingredient_name", "ingredient", ["name"], unique=False)

    op.create_table(
        "order",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=True),
        sa.Column("waiter_id", sa.Integer(), nullable=True),
        sa.Column("order_source", sa.Enum("dine_in", "takeaway", "delivery", name="ordersource"), nullable=False),
        sa.Column("status", sa.Enum("draft", "submitted", "in_progress", "ready", "served", "cancelled", name="orderstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.ForeignKeyConstraint(["table_id"], ["restauranttable.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_branch_id", "order", ["branch_id"], unique=False)

    op.create_table(
        "orderitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("course_no", sa.Integer(), nullable=False),
        sa.Column("notes", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("line_total", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menuitem.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orderitem_order_id", "orderitem", ["order_id"], unique=False)
    op.create_index("ix_orderitem_menu_item_id", "orderitem", ["menu_item_id"], unique=False)

    op.create_table(
        "kitchenticket",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_item_id", sa.Integer(), nullable=False),
        sa.Column("station", sqlmodel.AutoString(length=60), nullable=False),
        sa.Column("status", sa.Enum("queued", "in_preparation", "ready", "served", "delayed", "voided", name="kitchenticketstatus"), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_item_id"], ["orderitem.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_kitchenticket_order_item_id", "kitchenticket", ["order_item_id"], unique=False)

    op.create_table(
        "stockledgerentry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("change_qty", sa.Float(), nullable=False),
        sa.Column("reason", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("reference_type", sqlmodel.AutoString(length=80), nullable=False),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredient.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stockledgerentry_ingredient_id", "stockledgerentry", ["ingredient_id"], unique=False)

    op.create_table(
        "purchaseorder",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("open", "partial", "received", name="purchaseorderstatus"), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchaseorder_branch_id", "purchaseorder", ["branch_id"], unique=False)

    op.create_table(
        "purchaseorderline",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("ordered_qty", sa.Float(), nullable=False),
        sa.Column("received_qty", sa.Float(), nullable=False),
        sa.Column("unit_cost", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredient.id"]),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchaseorder.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchaseorderline_purchase_order_id", "purchaseorderline", ["purchase_order_id"], unique=False)

    op.create_table(
        "bill",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.Column("tax_amount", sa.Float(), nullable=False),
        sa.Column("service_charge", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("paid_amount", sa.Float(), nullable=False),
        sa.Column("status", sa.Enum("open", "partially_paid", "paid", name="billstatus"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )
    op.create_index("ix_bill_order_id", "bill", ["order_id"], unique=True)

    op.create_table(
        "settlement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("payment_method", sqlmodel.AutoString(length=32), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("cashier_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bill_id"], ["bill.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_settlement_bill_id", "settlement", ["bill_id"], unique=False)

    op.create_table(
        "cashdrawersession",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("cashier_id", sa.Integer(), nullable=True),
        sa.Column("opening_balance", sa.Float(), nullable=False),
        sa.Column("closing_balance", sa.Float(), nullable=True),
        sa.Column("status", sa.Enum("open", "closed", name="drawerstatus"), nullable=False),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cashdrawersession_branch_id", "cashdrawersession", ["branch_id"], unique=False)

    op.create_table(
        "shift",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("staff_user_id", sa.Integer(), nullable=False),
        sa.Column("role", sqlmodel.AutoString(length=64), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.Enum("scheduled", "started", "closed", name="shiftstatus"), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shift_branch_id", "shift", ["branch_id"], unique=False)

    op.create_table(
        "branchpolicy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("key", sqlmodel.AutoString(length=80), nullable=False),
        sa.Column("value", sqlmodel.AutoString(length=500), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_branchpolicy_branch_id", "branchpolicy", ["branch_id"], unique=False)
    op.create_index("ix_branchpolicy_key", "branchpolicy", ["key"], unique=False)

    op.create_table(
        "operationaleventlog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("event_name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("severity", sa.Enum("info", "warning", "critical", name="operationalseverity"), nullable=False),
        sa.Column("source", sqlmodel.AutoString(length=80), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("payload_json", sqlmodel.AutoString(length=3000), nullable=True),
        sa.Column("is_operational_exception", sa.Boolean(), nullable=False),
        sa.Column("retention_until", sa.DateTime(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operationaleventlog_branch_id", "operationaleventlog", ["branch_id"], unique=False)
    op.create_index("ix_operationaleventlog_event_name", "operationaleventlog", ["event_name"], unique=False)
    op.create_index("ix_operationaleventlog_severity", "operationaleventlog", ["severity"], unique=False)
    op.create_index("ix_operationaleventlog_source", "operationaleventlog", ["source"], unique=False)
    op.create_index("ix_operationaleventlog_actor_user_id", "operationaleventlog", ["actor_user_id"], unique=False)
    op.create_index("ix_operationaleventlog_is_operational_exception", "operationaleventlog", ["is_operational_exception"], unique=False)
    op.create_index("ix_operationaleventlog_retention_until", "operationaleventlog", ["retention_until"], unique=False)
    op.create_index("ix_operationaleventlog_occurred_at", "operationaleventlog", ["occurred_at"], unique=False)

    op.create_table(
        "waitlistentry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("guest_name", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("guest_phone", sqlmodel.AutoString(length=40), nullable=False),
        sa.Column("party_size", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("waiting", "seated", "cancelled", name="waitliststatus"), nullable=False),
        sa.Column("notes", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_waitlistentry_branch_id", "waitlistentry", ["branch_id"], unique=False)

    op.create_table(
        "accountingexport",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("business_date", sa.DateTime(), nullable=False),
        sa.Column("payload_json", sqlmodel.AutoString(length=4000), nullable=False),
        sa.Column("status", sa.Enum("generated", "sent", name="accountingexportstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accountingexport_branch_id", "accountingexport", ["branch_id"], unique=False)

    op.create_table(
        "idempotencyrecord",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("endpoint", sqlmodel.AutoString(length=200), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_json", sqlmodel.AutoString(length=12000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_idempotencyrecord_key", "idempotencyrecord", ["key"], unique=False)
    op.create_index("ix_idempotencyrecord_endpoint", "idempotencyrecord", ["endpoint"], unique=False)

    op.create_table(
        "stockcountsession",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("draft", "submitted", "approved", "rejected", name="stockcountsessionstatus"), nullable=False),
        sa.Column("opened_by", sa.Integer(), nullable=True),
        sa.Column("submitted_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sqlmodel.AutoString(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stockcountsession_branch_id", "stockcountsession", ["branch_id"], unique=False)

    op.create_table(
        "stockcountline",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("expected_qty", sa.Float(), nullable=False),
        sa.Column("counted_qty", sa.Float(), nullable=False),
        sa.Column("variance_qty", sa.Float(), nullable=False),
        sa.Column("notes", sqlmodel.AutoString(length=300), nullable=True),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredient.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["stockcountsession.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stockcountline_session_id", "stockcountline", ["session_id"], unique=False)
    op.create_index("ix_stockcountline_ingredient_id", "stockcountline", ["ingredient_id"], unique=False)

    op.create_table(
        "dayclosechecklistitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("day_close_id", sa.Integer(), nullable=False),
        sa.Column("item_key", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_checked", sa.Boolean(), nullable=False),
        sa.Column("checked_by", sa.Integer(), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["day_close_id"], ["dayclose.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dayclosechecklistitem_day_close_id", "dayclosechecklistitem", ["day_close_id"], unique=False)

    op.create_table(
        "accountingexportretry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("accounting_export_id", sa.Integer(), nullable=False),
        sa.Column("requested_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.Enum("queued", "completed", "failed", name="accountingexportretrystatus"), nullable=False),
        sa.Column("message", sqlmodel.AutoString(length=400), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["accounting_export_id"], ["accountingexport.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accountingexportretry_accounting_export_id", "accountingexportretry", ["accounting_export_id"], unique=False)

    op.create_table(
        "kitchenticketevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.Enum("queued", "in_preparation", "ready", "served", "delayed", "voided", name="kitchenticketstatus"), nullable=False),
        sa.Column("to_status", sa.Enum("queued", "in_preparation", "ready", "served", "delayed", "voided", name="kitchenticketstatus"), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("pass_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["kitchenticket.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_kitchenticketevent_ticket_id", "kitchenticketevent", ["ticket_id"], unique=False)

    op.create_table(
        "ordereditapproval",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("requested_by", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("reason", sqlmodel.AutoString(length=300), nullable=False),
        sa.Column("status", sqlmodel.AutoString(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ordereditapproval_order_id", "ordereditapproval", ["order_id"], unique=False)

    with op.batch_alter_table("privilegedactionaudit", schema=None) as batch_op:
        batch_op.add_column(sa.Column("compliance_tag", sqlmodel.AutoString(length=80), nullable=False, server_default="privileged_action"))
        batch_op.add_column(sa.Column("retention_until", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("is_operational_exception", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_index(batch_op.f("ix_privilegedactionaudit_retention_until"), ["retention_until"], unique=False)
        batch_op.create_index(batch_op.f("ix_privilegedactionaudit_is_operational_exception"), ["is_operational_exception"], unique=False)

    with op.batch_alter_table("stocktransfer", schema=None) as batch_op:
        batch_op.add_column(sa.Column("shipped_qty", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("received_qty", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("discrepancy_notes", sqlmodel.AutoString(length=400), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("stocktransfer", schema=None) as batch_op:
        batch_op.drop_column("discrepancy_notes")
        batch_op.drop_column("received_qty")
        batch_op.drop_column("shipped_qty")

    with op.batch_alter_table("privilegedactionaudit", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_privilegedactionaudit_is_operational_exception"))
        batch_op.drop_index(batch_op.f("ix_privilegedactionaudit_retention_until"))
        batch_op.drop_column("is_operational_exception")
        batch_op.drop_column("retention_until")
        batch_op.drop_column("compliance_tag")

    op.drop_index("ix_ordereditapproval_order_id", table_name="ordereditapproval")
    op.drop_table("ordereditapproval")

    op.drop_index("ix_kitchenticketevent_ticket_id", table_name="kitchenticketevent")
    op.drop_table("kitchenticketevent")

    op.drop_index("ix_accountingexportretry_accounting_export_id", table_name="accountingexportretry")
    op.drop_table("accountingexportretry")

    op.drop_index("ix_dayclosechecklistitem_day_close_id", table_name="dayclosechecklistitem")
    op.drop_table("dayclosechecklistitem")

    op.drop_index("ix_stockcountline_ingredient_id", table_name="stockcountline")
    op.drop_index("ix_stockcountline_session_id", table_name="stockcountline")
    op.drop_table("stockcountline")

    op.drop_index("ix_stockcountsession_branch_id", table_name="stockcountsession")
    op.drop_table("stockcountsession")

    op.drop_index("ix_idempotencyrecord_endpoint", table_name="idempotencyrecord")
    op.drop_index("ix_idempotencyrecord_key", table_name="idempotencyrecord")
    op.drop_table("idempotencyrecord")

    op.drop_index("ix_accountingexport_branch_id", table_name="accountingexport")
    op.drop_table("accountingexport")

    op.drop_index("ix_waitlistentry_branch_id", table_name="waitlistentry")
    op.drop_table("waitlistentry")

    op.drop_index("ix_operationaleventlog_occurred_at", table_name="operationaleventlog")
    op.drop_index("ix_operationaleventlog_retention_until", table_name="operationaleventlog")
    op.drop_index("ix_operationaleventlog_is_operational_exception", table_name="operationaleventlog")
    op.drop_index("ix_operationaleventlog_actor_user_id", table_name="operationaleventlog")
    op.drop_index("ix_operationaleventlog_source", table_name="operationaleventlog")
    op.drop_index("ix_operationaleventlog_severity", table_name="operationaleventlog")
    op.drop_index("ix_operationaleventlog_event_name", table_name="operationaleventlog")
    op.drop_index("ix_operationaleventlog_branch_id", table_name="operationaleventlog")
    op.drop_table("operationaleventlog")

    op.drop_index("ix_branchpolicy_key", table_name="branchpolicy")
    op.drop_index("ix_branchpolicy_branch_id", table_name="branchpolicy")
    op.drop_table("branchpolicy")

    op.drop_index("ix_shift_branch_id", table_name="shift")
    op.drop_table("shift")

    op.drop_index("ix_cashdrawersession_branch_id", table_name="cashdrawersession")
    op.drop_table("cashdrawersession")

    op.drop_index("ix_settlement_bill_id", table_name="settlement")
    op.drop_table("settlement")

    op.drop_index("ix_bill_order_id", table_name="bill")
    op.drop_table("bill")

    op.drop_index("ix_purchaseorderline_purchase_order_id", table_name="purchaseorderline")
    op.drop_table("purchaseorderline")

    op.drop_index("ix_purchaseorder_branch_id", table_name="purchaseorder")
    op.drop_table("purchaseorder")

    op.drop_index("ix_stockledgerentry_ingredient_id", table_name="stockledgerentry")
    op.drop_table("stockledgerentry")

    op.drop_index("ix_kitchenticket_order_item_id", table_name="kitchenticket")
    op.drop_table("kitchenticket")

    op.drop_index("ix_orderitem_menu_item_id", table_name="orderitem")
    op.drop_index("ix_orderitem_order_id", table_name="orderitem")
    op.drop_table("orderitem")

    op.drop_index("ix_order_branch_id", table_name="order")
    op.drop_table("order")

    op.drop_index("ix_ingredient_name", table_name="ingredient")
    op.drop_index("ix_ingredient_branch_id", table_name="ingredient")
    op.drop_table("ingredient")

    op.drop_index("ix_menuitem_name", table_name="menuitem")
    op.drop_index("ix_menuitem_branch_id", table_name="menuitem")
    op.drop_table("menuitem")

    op.drop_index("ix_reservation_branch_id", table_name="reservation")
    op.drop_table("reservation")

    op.drop_index("ix_restauranttable_code", table_name="restauranttable")
    op.drop_index("ix_restauranttable_branch_id", table_name="restauranttable")
    op.drop_table("restauranttable")

    op.drop_index("ix_branch_name", table_name="branch")
    op.drop_table("branch")
