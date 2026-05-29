from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlmodel import select

from src.apps.core.security import get_password_hash
from src.apps.finance.models.payment import PaymentProvider, PaymentStatus, PaymentTransaction
from src.apps.iam.models.role import Role, UserRole
from src.apps.iam.models.user import User, UserProfile
from src.apps.multitenancy.models.tenant import Tenant, TenantMember, TenantRole
from src.apps.notification.models.notification import Notification, NotificationType
from src.apps.restaurant.models import (
    Bill,
    BillStatus,
    Branch,
    BranchPaymentMethod,
    Ingredient,
    KitchenTicket,
    KitchenTicketStatus,
    MenuItem,
    Order,
    OrderItem,
    OrderSource,
    OrderStatus,
    Reservation,
    ReservationStatus,
    RestaurantTable,
    Settlement,
    TableStatus,
    WaitlistEntry,
    WaitlistStatus,
)
from src.db.session import async_session_factory, init_db


DEFAULT_PASSWORD = "QaPass1234"


async def _get_one_or_none(session, model, **filters):
    stmt = select(model)
    for field, value in filters.items():
        stmt = stmt.where(getattr(model, field) == value)
    result = await session.execute(stmt)
    return result.scalars().first()


async def _upsert_user(
    session,
    *,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    is_superuser: bool = False,
) -> User:
    user = await _get_one_or_none(session, User, username=username)
    hashed = get_password_hash(DEFAULT_PASSWORD)

    if user is None:
        user = User(
            username=username,
            email=email,
            hashed_password=hashed,
            is_active=True,
            is_confirmed=True,
            is_superuser=is_superuser,
        )
        session.add(user)
        await session.flush()
    else:
        user.email = email
        user.hashed_password = hashed
        user.is_active = True
        user.is_confirmed = True
        user.is_superuser = is_superuser

    profile = await _get_one_or_none(session, UserProfile, user_id=user.id)
    if profile is None:
        profile = UserProfile(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            phone="+15550000000",
            bio="QA seed account",
        )
        session.add(profile)
    else:
        profile.first_name = first_name
        profile.last_name = last_name

    return user


async def _ensure_role(session, name: str, description: str) -> Role:
    role = await _get_one_or_none(session, Role, name=name)
    if role is None:
        role = Role(name=name, description=description)
        session.add(role)
        await session.flush()
    return role


async def _ensure_user_role(session, user_id: int, role_id: int) -> None:
    existing = await _get_one_or_none(session, UserRole, user_id=user_id, role_id=role_id)
    if existing is None:
        session.add(UserRole(user_id=user_id, role_id=role_id))


async def seed() -> None:
    await init_db()

    async with async_session_factory() as session:
        # Users for role-based QA coverage.
        users = {
            "qaadmin": await _upsert_user(
                session,
                username="qaadmin",
                email="qaadmin@example.com",
                first_name="QA",
                last_name="Admin",
                is_superuser=True,
            ),
            "qamanager": await _upsert_user(
                session,
                username="qamanager",
                email="qamanager@example.com",
                first_name="QA",
                last_name="Manager",
            ),
            "qahost": await _upsert_user(
                session,
                username="qahost",
                email="qahost@example.com",
                first_name="QA",
                last_name="Host",
            ),
            "qawaiter": await _upsert_user(
                session,
                username="qawaiter",
                email="qawaiter@example.com",
                first_name="QA",
                last_name="Waiter",
            ),
            "qachef": await _upsert_user(
                session,
                username="qachef",
                email="qachef@example.com",
                first_name="QA",
                last_name="Chef",
            ),
            "qacashier": await _upsert_user(
                session,
                username="qacashier",
                email="qacashier@example.com",
                first_name="QA",
                last_name="Cashier",
            ),
        }

        role_specs = {
            "admin": "Global admin role",
            "branch_manager": "Branch manager role",
            "host": "Host role",
            "waiter": "Waiter role",
            "chef": "Kitchen role",
            "cashier": "Cashier role",
        }
        roles = {}
        for name, description in role_specs.items():
            roles[name] = await _ensure_role(session, name, description)

        await _ensure_user_role(session, users["qaadmin"].id, roles["admin"].id)
        await _ensure_user_role(session, users["qamanager"].id, roles["branch_manager"].id)
        await _ensure_user_role(session, users["qahost"].id, roles["host"].id)
        await _ensure_user_role(session, users["qawaiter"].id, roles["waiter"].id)
        await _ensure_user_role(session, users["qachef"].id, roles["chef"].id)
        await _ensure_user_role(session, users["qacashier"].id, roles["cashier"].id)

        tenant = await _get_one_or_none(session, Tenant, slug="qa-tenant")
        if tenant is None:
            tenant = Tenant(
                name="QA Tenant",
                slug="qa-tenant",
                description="Tenant used for repeatable manual QA",
                owner_id=users["qaadmin"].id,
            )
            session.add(tenant)
            await session.flush()
        else:
            tenant.owner_id = users["qaadmin"].id
            tenant.is_active = True

        membership_plan = {
            "qaadmin": TenantRole.OWNER,
            "qamanager": TenantRole.ADMIN,
            "qahost": TenantRole.MEMBER,
            "qawaiter": TenantRole.MEMBER,
            "qachef": TenantRole.MEMBER,
            "qacashier": TenantRole.MEMBER,
        }

        for username, member_role in membership_plan.items():
            existing = await _get_one_or_none(
                session,
                TenantMember,
                tenant_id=tenant.id,
                user_id=users[username].id,
            )
            if existing is None:
                session.add(
                    TenantMember(
                        tenant_id=tenant.id,
                        user_id=users[username].id,
                        role=member_role,
                        is_active=True,
                    )
                )
            else:
                existing.role = member_role
                existing.is_active = True

        branch = await _get_one_or_none(session, Branch, name="QA Downtown")
        if branch is None:
            branch = Branch(name="QA Downtown", tax_rate=0.1, service_charge_rate=0.05, is_active=True)
            session.add(branch)
            await session.flush()

        second_branch = await _get_one_or_none(session, Branch, name="QA Uptown")
        if second_branch is None:
            second_branch = Branch(name="QA Uptown", tax_rate=0.08, service_charge_rate=0.03, is_active=True)
            session.add(second_branch)
            await session.flush()

        for code, name in (("cash", "Cash"), ("card", "Card"), ("wallet", "Wallet")):
            method = await _get_one_or_none(session, BranchPaymentMethod, branch_id=branch.id, code=code)
            if method is None:
                session.add(BranchPaymentMethod(branch_id=branch.id, code=code, display_name=name, is_active=True))

        table_specs = [("QA-T1", 2, TableStatus.AVAILABLE), ("QA-T2", 4, TableStatus.OCCUPIED), ("QA-T3", 6, TableStatus.RESERVED)]
        tables = {}
        for code, seats, status in table_specs:
            table = await _get_one_or_none(session, RestaurantTable, branch_id=branch.id, code=code)
            if table is None:
                table = RestaurantTable(branch_id=branch.id, code=code, seats=seats, status=status)
                session.add(table)
                await session.flush()
            else:
                table.seats = seats
                table.status = status
            tables[code] = table

        menu_specs = [("QA Burger", 9.99), ("QA Pasta", 12.49), ("QA Lemonade", 3.50)]
        menu_items = {}
        for name, price in menu_specs:
            item = await _get_one_or_none(session, MenuItem, branch_id=branch.id, name=name)
            if item is None:
                item = MenuItem(branch_id=branch.id, name=name, price=price, is_available=True)
                session.add(item)
                await session.flush()
            else:
                item.price = price
                item.is_available = True
            menu_items[name] = item

        for name, unit, quantity, threshold in (
            ("QA Bun", "pcs", 120, 40),
            ("QA Patty", "pcs", 80, 20),
            ("QA Pasta", "kg", 24, 6),
        ):
            ingredient = await _get_one_or_none(session, Ingredient, branch_id=branch.id, name=name)
            if ingredient is None:
                session.add(
                    Ingredient(
                        branch_id=branch.id,
                        name=name,
                        unit=unit,
                        quantity_on_hand=quantity,
                        reorder_threshold=threshold,
                    )
                )
            else:
                ingredient.unit = unit
                ingredient.quantity_on_hand = quantity
                ingredient.reorder_threshold = threshold

        reservation = await _get_one_or_none(session, Reservation, branch_id=branch.id, guest_phone="+15550111111")
        if reservation is None:
            reservation = Reservation(
                branch_id=branch.id,
                guest_name="QA Guest",
                guest_phone="+15550111111",
                party_size=2,
                reservation_time=datetime.now(UTC) + timedelta(hours=2),
                table_id=tables["QA-T3"].id,
                status=ReservationStatus.CONFIRMED,
                notes="Seed reservation",
            )
            session.add(reservation)
        else:
            reservation.status = ReservationStatus.CONFIRMED
            reservation.table_id = tables["QA-T3"].id

        waitlist = await _get_one_or_none(session, WaitlistEntry, branch_id=branch.id, guest_phone="+15550222222")
        if waitlist is None:
            waitlist = WaitlistEntry(
                branch_id=branch.id,
                guest_name="Walk-in QA",
                guest_phone="+15550222222",
                party_size=3,
                status=WaitlistStatus.WAITING,
                notes="Seed waitlist entry",
            )
            session.add(waitlist)

        order = await _get_one_or_none(session, Order, branch_id=branch.id, waiter_id=users["qawaiter"].id)
        if order is None:
            order = Order(
                branch_id=branch.id,
                table_id=tables["QA-T2"].id,
                waiter_id=users["qawaiter"].id,
                order_source=OrderSource.DINE_IN,
                status=OrderStatus.SUBMITTED,
            )
            session.add(order)
            await session.flush()

        order_item = await _get_one_or_none(session, OrderItem, order_id=order.id)
        line_total = 2 * menu_items["QA Burger"].price
        if order_item is None:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=menu_items["QA Burger"].id,
                quantity=2,
                course_no=1,
                line_total=line_total,
            )
            session.add(order_item)
            await session.flush()
        else:
            order_item.menu_item_id = menu_items["QA Burger"].id
            order_item.quantity = 2
            order_item.line_total = line_total

        ticket = await _get_one_or_none(session, KitchenTicket, order_item_id=order_item.id)
        if ticket is None:
            session.add(
                KitchenTicket(
                    order_item_id=order_item.id,
                    station="grill",
                    status=KitchenTicketStatus.IN_PREPARATION,
                    priority=1,
                )
            )

        subtotal = round(line_total, 2)
        tax_amount = round(subtotal * branch.tax_rate, 2)
        service_charge = round(subtotal * branch.service_charge_rate, 2)
        total_amount = round(subtotal + tax_amount + service_charge, 2)

        bill = await _get_one_or_none(session, Bill, order_id=order.id)
        if bill is None:
            bill = Bill(
                order_id=order.id,
                subtotal=subtotal,
                tax_amount=tax_amount,
                service_charge=service_charge,
                total_amount=total_amount,
                paid_amount=round(total_amount / 2, 2),
                status=BillStatus.PARTIALLY_PAID,
            )
            session.add(bill)
            await session.flush()
        else:
            bill.subtotal = subtotal
            bill.tax_amount = tax_amount
            bill.service_charge = service_charge
            bill.total_amount = total_amount
            bill.paid_amount = round(total_amount / 2, 2)
            bill.status = BillStatus.PARTIALLY_PAID

        settlement = await _get_one_or_none(session, Settlement, bill_id=bill.id)
        if settlement is None:
            session.add(
                Settlement(
                    bill_id=bill.id,
                    payment_method="cash",
                    amount=round(total_amount / 2, 2),
                    cashier_id=users["qacashier"].id,
                )
            )

        payment = await _get_one_or_none(session, PaymentTransaction, purchase_order_id="QA-ORDER-001")
        if payment is None:
            payment = PaymentTransaction(
                provider=PaymentProvider.KHALTI,
                amount=2500,
                currency="NPR",
                status=PaymentStatus.COMPLETED,
                purchase_order_id="QA-ORDER-001",
                purchase_order_name="QA Seed Payment",
                provider_transaction_id="qa-khalti-001",
                provider_pidx="qa-pidx-001",
                return_url="http://localhost:3000/payment-callback",
                website_url="http://localhost:3000",
                user_id=users["qaadmin"].id,
                extra_data='{"seed": true}',
            )
            session.add(payment)

        for username, title, body, n_type in (
            ("qaadmin", "QA Seed Ready", "QA environment has been seeded successfully.", NotificationType.SUCCESS),
            ("qamanager", "Day Close Pending", "Please review open day-close blockers.", NotificationType.WARNING),
            ("qacashier", "Settlement Alert", "One bill remains partially paid.", NotificationType.PAYMENT),
        ):
            existing_notification = await _get_one_or_none(
                session,
                Notification,
                user_id=users[username].id,
                title=title,
            )
            if existing_notification is None:
                session.add(
                    Notification(
                        user_id=users[username].id,
                        title=title,
                        body=body,
                        type=n_type,
                        is_read=False,
                        extra_data={"seed": True},
                    )
                )

        await session.commit()

    print("QA seed completed.")
    print("Credentials (all users):")
    print(f"  password={DEFAULT_PASSWORD}")
    print("  qaadmin / qamanager / qahost / qawaiter / qachef / qacashier")


if __name__ == "__main__":
    asyncio.run(seed())
