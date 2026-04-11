from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config


@pytest.mark.integration
@pytest.mark.sqlite
def test_restaurant_schema_upgrade_paths(tmp_path):
    db_path = tmp_path / "migrated_restaurant.db"
    alembic_ini = Path(__file__).resolve().parents[3] / "alembic.ini"

    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str((Path(__file__).resolve().parents[3] / "alembic").resolve()))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(cfg, "head")

    engine = sa.create_engine(f"sqlite:///{db_path}")
    metadata = sa.MetaData()
    metadata.reflect(bind=engine)

    required_tables = {
        "reservation",
        "order",
        "kitchenticket",
        "stocktransfer",
        "bill",
        "accountingexport",
        "stockledgerentry",
    }
    assert required_tables.issubset(set(metadata.tables))

    branch = metadata.tables["branch"]
    restaurant_table = metadata.tables["restauranttable"]
    menu_item = metadata.tables["menuitem"]
    ingredient = metadata.tables["ingredient"]
    reservation = metadata.tables["reservation"]
    order = metadata.tables["order"]
    order_item = metadata.tables["orderitem"]
    kitchen_ticket = metadata.tables["kitchenticket"]
    bill = metadata.tables["bill"]
    settlement = metadata.tables["settlement"]
    stock_ledger = metadata.tables["stockledgerentry"]
    stock_transfer = metadata.tables["stocktransfer"]
    accounting_export = metadata.tables["accountingexport"]

    with engine.begin() as conn:
        branch_id = conn.execute(
            branch.insert().values(name="Migration Branch", tax_rate=0.07, service_charge_rate=0.05, is_active=True)
        ).inserted_primary_key[0]

        table_id = conn.execute(
            restaurant_table.insert().values(branch_id=branch_id, code="A1", seats=4, status="available")
        ).inserted_primary_key[0]

        menu_id = conn.execute(
            menu_item.insert().values(branch_id=branch_id, name="Migration Meal", price=12.5, is_available=True)
        ).inserted_primary_key[0]

        ingredient_id = conn.execute(
            ingredient.insert().values(
                branch_id=branch_id,
                name="Migration Ingredient",
                unit="kg",
                quantity_on_hand=10,
                reorder_threshold=2,
                updated_at=sa.func.now(),
            )
        ).inserted_primary_key[0]

        reservation_id = conn.execute(
            reservation.insert().values(
                branch_id=branch_id,
                guest_name="Guest",
                guest_phone="+15550000",
                party_size=2,
                reservation_time=sa.func.now(),
                table_id=table_id,
                status="confirmed",
                notes="schema check",
                created_at=sa.func.now(),
            )
        ).inserted_primary_key[0]

        order_id = conn.execute(
            order.insert().values(
                branch_id=branch_id,
                table_id=table_id,
                waiter_id=1,
                order_source="dine_in",
                status="submitted",
                created_at=sa.func.now(),
                updated_at=sa.func.now(),
            )
        ).inserted_primary_key[0]

        order_item_id = conn.execute(
            order_item.insert().values(order_id=order_id, menu_item_id=menu_id, quantity=2, course_no=1, line_total=25)
        ).inserted_primary_key[0]

        conn.execute(
            kitchen_ticket.insert().values(
                order_item_id=order_item_id,
                station="main",
                status="queued",
                priority=0,
                updated_at=sa.func.now(),
            )
        )

        bill_id = conn.execute(
            bill.insert().values(
                order_id=order_id,
                subtotal=25,
                tax_amount=2.5,
                service_charge=1.0,
                total_amount=28.5,
                paid_amount=28.5,
                status="paid",
            )
        ).inserted_primary_key[0]

        conn.execute(
            settlement.insert().values(bill_id=bill_id, payment_method="cash", amount=28.5, cashier_id=9, created_at=sa.func.now())
        )

        conn.execute(
            stock_ledger.insert().values(
                ingredient_id=ingredient_id,
                change_qty=-1,
                reason="usage",
                reference_type="order",
                reference_id=order_id,
                created_at=sa.func.now(),
            )
        )

        conn.execute(
            stock_transfer.insert().values(
                from_branch_id=branch_id,
                to_branch_id=branch_id,
                from_ingredient_id=ingredient_id,
                to_ingredient_id=ingredient_id,
                quantity=1,
                shipped_qty=1,
                received_qty=1,
                discrepancy_notes=None,
                status="received",
                approved_by=1,
                created_at=sa.func.now(),
            )
        )

        conn.execute(
            accounting_export.insert().values(
                branch_id=branch_id,
                business_date=sa.func.now(),
                payload_json="{}",
                status="generated",
                created_at=sa.func.now(),
            )
        )

        assert conn.scalar(sa.select(sa.func.count()).select_from(reservation).where(reservation.c.id == reservation_id)) == 1
        assert conn.scalar(sa.select(sa.func.count()).select_from(order).where(order.c.id == order_id)) == 1
        assert conn.scalar(sa.select(sa.func.count()).select_from(kitchen_ticket)) == 1
        assert conn.scalar(sa.select(sa.func.count()).select_from(stock_transfer)) == 1
        assert conn.scalar(sa.select(sa.func.count()).select_from(bill)) == 1
        assert conn.scalar(sa.select(sa.func.count()).select_from(accounting_export)) == 1
