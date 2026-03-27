from datetime import datetime

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, func, select

from src.apps.iam.api.deps import get_db
from src.apps.restaurant.access import require_restaurant_access
from src.apps.restaurant.models import (
    AccountingExport,
    AccountingExportStatus,
    AttendanceRecord,
    Bill,
    BillStatus,
    Branch,
    BranchPolicy,
    CashDrawerSession,
    DayClose,
    DayCloseStatus,
    DiscountApproval,
    DrawerStatus,
    GoodsReceipt,
    Ingredient,
    IdempotencyRecord,
    KitchenTicket,
    KitchenTicketStatus,
    MenuItem,
    MenuCategory,
    ModifierGroup,
    ModifierOption,
    Order,
    OrderItem,
    OrderStatus,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    Recipe,
    RecipeItem,
    Reservation,
    ReservationStatus,
    Refund,
    RestaurantTable,
    ServiceZone,
    Settlement,
    Shift,
    StockLedgerEntry,
    TableStatus,
    TableGroup,
    TaxRule,
    StockTransfer,
    Vendor,
    WaitlistEntry,
    WaitlistStatus,
)
from src.apps.restaurant.schemas.operations import (
    AccountingExportCreate,
    AccountingExportRead,
    AttendanceCheckout,
    AttendanceCreate,
    AttendanceRead,
    BillRead,
    BillSettlementCreate,
    BranchCreate,
    BranchPolicyCreate,
    BranchPolicyPatch,
    BranchRead,
    DayCloseCreate,
    DayCloseFinalize,
    DayCloseRead,
    DiscountApprovalAction,
    DiscountApprovalCreate,
    DiscountApprovalRead,
    DrawerCloseRequest,
    DrawerSessionCreate,
    DrawerSessionRead,
    IngredientCreate,
    IngredientRead,
    InventoryAdjustmentCreate,
    KitchenTicketPatch,
    KitchenTicketRead,
    MenuItemCreate,
    MenuCategoryCreate,
    MenuCategoryRead,
    MenuItemRead,
    ModifierGroupCreate,
    ModifierGroupRead,
    ModifierOptionCreate,
    ModifierOptionRead,
    OrderCreate,
    OrderPatch,
    OrderRead,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseReceiptCreate,
    RecipeCreate,
    RecipeRead,
    ReservationCreate,
    ReservationRead,
    ReservationUpdate,
    SeatTableRequest,
    ServiceZoneCreate,
    ServiceZoneRead,
    ShiftCreate,
    ShiftStatusPatch,
    StockTransferAction,
    StockTransferCreate,
    StockTransferRead,
    TableCreate,
    TableGroupCreate,
    TableGroupRead,
    TableRead,
    TaxRuleCreate,
    TaxRuleRead,
    VendorCreate,
    VendorRead,
    GoodsReceiptCreate,
    GoodsReceiptRead,
    RefundCreate,
    RefundRead,
    WaitlistCreate,
    WaitlistCursorPage,
    WaitlistRead,
    OrderCursorPage,
    KitchenTicketCursorPage,
)

router = APIRouter(dependencies=[Depends(require_restaurant_access)])


async def _get_branch_or_404(branch_id: int, db: AsyncSession) -> Branch:
    branch = await db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch


async def _validate_table_for_branch(table_id: int, branch_id: int, db: AsyncSession) -> RestaurantTable:
    table = await db.get(RestaurantTable, table_id)
    if not table or table.branch_id != branch_id:
        raise HTTPException(status_code=404, detail="Table not found for branch")
    return table


async def _idempotency_replay(request: Request, db: AsyncSession) -> JSONResponse | None:
    key = request.headers.get("Idempotency-Key")
    if not key:
        return None
    endpoint = f"{request.method}:{request.url.path}"
    record = (
        await db.execute(
            select(IdempotencyRecord).where(IdempotencyRecord.key == key, IdempotencyRecord.endpoint == endpoint)
        )
    ).scalars().first()
    if not record:
        return None
    return JSONResponse(
        status_code=record.status_code,
        content=json.loads(record.response_json),
        headers={"X-Idempotent-Replay": "true"},
    )


async def _store_idempotency(request: Request, db: AsyncSession, status_code: int, payload: dict) -> None:
    key = request.headers.get("Idempotency-Key")
    if not key:
        return
    endpoint = f"{request.method}:{request.url.path}"
    existing = (
        await db.execute(
            select(IdempotencyRecord).where(IdempotencyRecord.key == key, IdempotencyRecord.endpoint == endpoint)
        )
    ).scalars().first()
    if existing:
        return
    db.add(
        IdempotencyRecord(
            key=key,
            endpoint=endpoint,
            status_code=status_code,
            response_json=json.dumps(payload, default=str),
        )
    )


def _cursor_result(items: list, limit: int) -> dict:
    next_cursor = items[-1].id if len(items) == limit and getattr(items[-1], "id", None) else None
    return {"items": items, "next_cursor": next_cursor}


@router.get("/branches", response_model=list[BranchRead])
async def list_branches(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Branch).where(Branch.is_active == True).order_by(Branch.id.asc()))).scalars().all()


@router.post("/branches", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
async def create_branch(payload: BranchCreate, db: AsyncSession = Depends(get_db)):
    branch = Branch(**payload.model_dump())
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return branch


@router.post("/branches/{branch_id}/tables", response_model=TableRead, status_code=status.HTTP_201_CREATED)
async def create_table(branch_id: int, payload: TableCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    duplicate = (
        await db.execute(
            select(RestaurantTable).where(RestaurantTable.branch_id == branch_id, RestaurantTable.code == payload.code)
        )
    ).scalars().first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Table code already exists in branch")

    table = RestaurantTable(branch_id=branch_id, **payload.model_dump())
    db.add(table)
    await db.commit()
    await db.refresh(table)
    return table




@router.get("/branches/{branch_id}/tables", response_model=list[TableRead])
async def list_tables(branch_id: int, status_filter: TableStatus | None = None, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    statement = select(RestaurantTable).where(RestaurantTable.branch_id == branch_id)
    if status_filter is not None:
        statement = statement.where(RestaurantTable.status == status_filter)
    return (await db.execute(statement.order_by(RestaurantTable.id.asc()))).scalars().all()


@router.post("/branches/{branch_id}/service-zones", response_model=ServiceZoneRead, status_code=status.HTTP_201_CREATED)
async def create_service_zone(branch_id: int, payload: ServiceZoneCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    zone = ServiceZone(branch_id=branch_id, **payload.model_dump())
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone


@router.get("/branches/{branch_id}/service-zones", response_model=list[ServiceZoneRead])
async def list_service_zones(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (await db.execute(select(ServiceZone).where(ServiceZone.branch_id == branch_id).order_by(ServiceZone.id.asc()))).scalars().all()


@router.post("/branches/{branch_id}/table-groups", response_model=TableGroupRead, status_code=status.HTTP_201_CREATED)
async def create_table_group(branch_id: int, payload: TableGroupCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    if payload.table_ids:
        tables = (
            await db.execute(select(RestaurantTable).where(RestaurantTable.branch_id == branch_id, RestaurantTable.id.in_(payload.table_ids)))
        ).scalars().all()
        if len(tables) != len(set(payload.table_ids)):
            raise HTTPException(status_code=400, detail="Table group includes invalid branch table IDs")
    group = TableGroup(branch_id=branch_id, name=payload.name, table_ids_csv=",".join(str(item) for item in payload.table_ids))
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.get("/branches/{branch_id}/table-groups", response_model=list[TableGroupRead])
async def list_table_groups(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (await db.execute(select(TableGroup).where(TableGroup.branch_id == branch_id).order_by(TableGroup.id.asc()))).scalars().all()


@router.post("/branches/{branch_id}/menu-items", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
async def create_menu_item(branch_id: int, payload: MenuItemCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    item = MenuItem(branch_id=branch_id, **payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/branches/{branch_id}/menu-categories", response_model=MenuCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_menu_category(branch_id: int, payload: MenuCategoryCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    category = MenuCategory(branch_id=branch_id, **payload.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/branches/{branch_id}/menu-categories", response_model=list[MenuCategoryRead])
async def list_menu_categories(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(select(MenuCategory).where(MenuCategory.branch_id == branch_id).order_by(MenuCategory.display_order.asc()))
    ).scalars().all()


@router.post("/branches/{branch_id}/modifier-groups", response_model=ModifierGroupRead, status_code=status.HTTP_201_CREATED)
async def create_modifier_group(branch_id: int, payload: ModifierGroupCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    group = ModifierGroup(branch_id=branch_id, **payload.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.post("/modifier-groups/{group_id}/options", response_model=ModifierOptionRead, status_code=status.HTTP_201_CREATED)
async def create_modifier_option(group_id: int, payload: ModifierOptionCreate, db: AsyncSession = Depends(get_db)):
    group = await db.get(ModifierGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Modifier group not found")
    option = ModifierOption(modifier_group_id=group_id, **payload.model_dump())
    db.add(option)
    await db.commit()
    await db.refresh(option)
    return option


@router.get("/modifier-groups/{group_id}/options", response_model=list[ModifierOptionRead])
async def list_modifier_options(group_id: int, db: AsyncSession = Depends(get_db)):
    return (
        await db.execute(
            select(ModifierOption).where(ModifierOption.modifier_group_id == group_id).order_by(ModifierOption.id.asc())
        )
    ).scalars().all()


@router.post("/tax-rules", response_model=TaxRuleRead, status_code=status.HTTP_201_CREATED)
async def create_tax_rule(payload: TaxRuleCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)
    latest = (
        await db.execute(
            select(TaxRule)
            .where(TaxRule.branch_id == payload.branch_id, TaxRule.name == payload.name)
            .order_by(TaxRule.version.desc())
        )
    ).scalars().first()
    next_version = (latest.version + 1) if latest else 1
    if latest:
        latest.is_active = False
        db.add(latest)
    rule = TaxRule(
        branch_id=payload.branch_id,
        name=payload.name,
        rate=payload.rate,
        version=next_version,
        is_active=True,
        effective_from=payload.effective_from or datetime.utcnow(),
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/tax-rules", response_model=list[TaxRuleRead])
async def list_tax_rules(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(select(TaxRule).where(TaxRule.branch_id == branch_id).order_by(TaxRule.name.asc(), TaxRule.version.desc()))
    ).scalars().all()


@router.post("/branches/{branch_id}/ingredients", response_model=IngredientRead, status_code=status.HTTP_201_CREATED)
async def create_ingredient(branch_id: int, payload: IngredientCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    ingredient = Ingredient(branch_id=branch_id, **payload.model_dump())
    db.add(ingredient)
    await db.commit()
    await db.refresh(ingredient)
    return ingredient


@router.post("/branches/{branch_id}/vendors", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
async def create_vendor(branch_id: int, payload: VendorCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    vendor = Vendor(branch_id=branch_id, **payload.model_dump())
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor


@router.get("/branches/{branch_id}/vendors", response_model=list[VendorRead])
async def list_vendors(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (await db.execute(select(Vendor).where(Vendor.branch_id == branch_id).order_by(Vendor.id.asc()))).scalars().all()


@router.post("/branches/{branch_id}/drawer-sessions", response_model=DrawerSessionRead, status_code=status.HTTP_201_CREATED)
async def open_drawer_session(branch_id: int, payload: DrawerSessionCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    session = CashDrawerSession(branch_id=branch_id, **payload.model_dump())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/branches/{branch_id}/policies", status_code=status.HTTP_201_CREATED)
async def create_branch_policy(branch_id: int, payload: BranchPolicyCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    existing = (
        await db.execute(
            select(BranchPolicy).where(BranchPolicy.branch_id == branch_id, BranchPolicy.key == payload.key)
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="Branch policy key already exists")

    policy = BranchPolicy(branch_id=branch_id, **payload.model_dump())
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.post("/reservations", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
async def create_reservation(payload: ReservationCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)
    reservation = Reservation(**payload.model_dump(), status=ReservationStatus.CONFIRMED)
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)
    return reservation






@router.get("/menu-items", response_model=list[MenuItemRead])
async def list_menu_items(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(select(MenuItem).where(MenuItem.branch_id == branch_id).order_by(MenuItem.id.asc()))
    ).scalars().all()


@router.get("/reservations", response_model=list[ReservationRead])
async def list_reservations(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(select(Reservation).where(Reservation.branch_id == branch_id).order_by(Reservation.id.desc()))
    ).scalars().all()




@router.get("/reservations/{reservation_id}", response_model=ReservationRead)
async def get_reservation(reservation_id: int, db: AsyncSession = Depends(get_db)):
    reservation = await db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationRead)
async def cancel_reservation(reservation_id: int, db: AsyncSession = Depends(get_db)):
    reservation = await db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    reservation.status = ReservationStatus.CANCELLED
    await db.commit()
    await db.refresh(reservation)
    return reservation


@router.patch("/reservations/{reservation_id}", response_model=ReservationRead)
async def patch_reservation(reservation_id: int, payload: ReservationUpdate, db: AsyncSession = Depends(get_db)):
    reservation = await db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if payload.status is not None:
        reservation.status = payload.status
    if payload.notes is not None:
        reservation.notes = payload.notes
    if payload.table_id is not None:
        table = await _validate_table_for_branch(payload.table_id, reservation.branch_id, db)
        reservation.table_id = table.id
    await db.commit()
    await db.refresh(reservation)
    return reservation


@router.post("/tables/{table_id}/seat")
async def seat_party(table_id: int, payload: SeatTableRequest, db: AsyncSession = Depends(get_db)):
    table = await db.get(RestaurantTable, table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    if table.status == TableStatus.OCCUPIED:
        raise HTTPException(status_code=409, detail="Table already occupied")
    if payload.party_size > table.seats:
        raise HTTPException(status_code=400, detail="Party size exceeds table capacity")

    table.status = TableStatus.OCCUPIED
    if payload.reservation_id:
        reservation = await db.get(Reservation, payload.reservation_id)
        if not reservation or reservation.branch_id != table.branch_id:
            raise HTTPException(status_code=404, detail="Reservation not found")
        reservation.status = ReservationStatus.SEATED
        reservation.table_id = table.id

    await db.commit()
    return {"table_id": table.id, "status": table.status, "party_size": payload.party_size}


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, request: Request, db: AsyncSession = Depends(get_db)):
    replay = await _idempotency_replay(request, db)
    if replay:
        return replay
    await _get_branch_or_404(payload.branch_id, db)
    if payload.table_id is not None:
        await _validate_table_for_branch(payload.table_id, payload.branch_id, db)

    if not payload.items:
        raise HTTPException(status_code=400, detail="At least one order item is required")

    menu_items = {
        item.id: item
        for item in (
            await db.execute(
                select(MenuItem).where(
                    MenuItem.branch_id == payload.branch_id,
                    MenuItem.id.in_([row.menu_item_id for row in payload.items]),
                )
            )
        ).scalars().all()
    }
    if len(menu_items) != len({i.menu_item_id for i in payload.items}):
        raise HTTPException(status_code=400, detail="One or more menu items do not belong to this branch")

    unavailable = [item.id for item in menu_items.values() if not item.is_available]
    if unavailable:
        raise HTTPException(status_code=400, detail=f"Menu items unavailable: {unavailable}")

    order = Order(
        branch_id=payload.branch_id,
        table_id=payload.table_id,
        waiter_id=payload.waiter_id,
        order_source=payload.order_source,
        status=OrderStatus.SUBMITTED,
    )
    db.add(order)
    await db.flush()

    subtotal = 0.0
    for item_payload in payload.items:
        menu_item = menu_items[item_payload.menu_item_id]
        line_total = round(menu_item.price * item_payload.quantity, 2)
        subtotal += line_total
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item_payload.menu_item_id,
            quantity=item_payload.quantity,
            course_no=item_payload.course_no,
            notes=item_payload.notes,
            line_total=line_total,
        )
        db.add(order_item)
        await db.flush()
        db.add(KitchenTicket(order_item_id=order_item.id, status=KitchenTicketStatus.QUEUED))

    branch = await _get_branch_or_404(payload.branch_id, db)
    tax_amount = round(subtotal * branch.tax_rate, 2)
    service_charge = round(subtotal * branch.service_charge_rate, 2)

    bill = Bill(
        order_id=order.id,
        subtotal=round(subtotal, 2),
        tax_amount=tax_amount,
        service_charge=service_charge,
        total_amount=round(subtotal + tax_amount + service_charge, 2),
    )
    db.add(bill)
    await db.commit()
    await db.refresh(order)
    await db.refresh(bill)

    payload_out = {"order": order.model_dump(), "bill": bill.model_dump()}
    await _store_idempotency(request, db, status.HTTP_201_CREATED, payload_out)
    await db.commit()
    return payload_out


@router.patch("/orders/{order_id}", response_model=OrderRead)
async def patch_order(order_id: int, payload: OrderPatch, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if payload.status is not None:
        order.status = payload.status

    if payload.items is not None:
        await db.execute(delete(OrderItem).where(OrderItem.order_id == order.id))
        subtotal = 0.0
        for item_payload in payload.items:
            menu_item = await db.get(MenuItem, item_payload.menu_item_id)
            if not menu_item or menu_item.branch_id != order.branch_id:
                raise HTTPException(status_code=400, detail=f"Invalid menu item {item_payload.menu_item_id}")
            line_total = round(menu_item.price * item_payload.quantity, 2)
            subtotal += line_total
            db.add(
                OrderItem(
                    order_id=order.id,
                    menu_item_id=item_payload.menu_item_id,
                    quantity=item_payload.quantity,
                    course_no=item_payload.course_no,
                    notes=item_payload.notes,
                    line_total=line_total,
                )
            )

        bill = (
            await db.execute(select(Bill).where(Bill.order_id == order.id))
        ).scalars().first()
        if bill:
            branch = await _get_branch_or_404(order.branch_id, db)
            bill.subtotal = round(subtotal, 2)
            bill.tax_amount = round(subtotal * branch.tax_rate, 2)
            bill.service_charge = round(subtotal * branch.service_charge_rate, 2)
            bill.total_amount = round(bill.subtotal + bill.tax_amount + bill.service_charge, 2)
            if bill.paid_amount == 0:
                bill.status = BillStatus.OPEN
            elif bill.paid_amount < bill.total_amount:
                bill.status = BillStatus.PARTIALLY_PAID
            else:
                bill.status = BillStatus.PAID

    order.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/kitchen/tickets", response_model=KitchenTicketCursorPage)
async def list_kitchen_tickets(
    status_filter: KitchenTicketStatus | None = None,
    cursor: int | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    statement = select(KitchenTicket)
    if status_filter is not None:
        statement = statement.where(KitchenTicket.status == status_filter)
    if cursor:
        statement = statement.where(KitchenTicket.id < cursor)
    tickets = (
        await db.execute(statement.order_by(KitchenTicket.id.desc()).limit(limit))
    ).scalars().all()
    return _cursor_result(tickets, limit)


@router.patch("/kitchen/tickets/{ticket_id}", response_model=KitchenTicketRead)
async def patch_kitchen_ticket(ticket_id: int, payload: KitchenTicketPatch, db: AsyncSession = Depends(get_db)):
    ticket = await db.get(KitchenTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = payload.status
    ticket.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/inventory/ingredients", response_model=list[IngredientRead])
async def list_ingredients(branch_id: int | None = None, db: AsyncSession = Depends(get_db)):
    statement = select(Ingredient)
    if branch_id is not None:
        statement = statement.where(Ingredient.branch_id == branch_id)
    return (await db.execute(statement.order_by(Ingredient.id.desc()))).scalars().all()


@router.post("/inventory/adjustments", status_code=status.HTTP_201_CREATED)
async def adjust_inventory(payload: InventoryAdjustmentCreate, db: AsyncSession = Depends(get_db)):
    ingredient = await db.get(Ingredient, payload.ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    if ingredient.quantity_on_hand + payload.change_qty < 0:
        raise HTTPException(status_code=400, detail="Adjustment would produce negative stock")

    ingredient.quantity_on_hand = round(ingredient.quantity_on_hand + payload.change_qty, 3)
    ingredient.updated_at = datetime.utcnow()
    ledger = StockLedgerEntry(
        ingredient_id=ingredient.id,
        change_qty=payload.change_qty,
        reason=payload.reason,
        reference_type="manual_adjustment",
    )
    db.add(ledger)
    await db.commit()
    await db.refresh(ingredient)
    return {"ingredient": ingredient, "ledger_entry": ledger}


@router.post("/recipes", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def create_recipe(payload: RecipeCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)
    if not payload.items:
        raise HTTPException(status_code=400, detail="Recipe items are required")
    ingredient_ids = [item.ingredient_id for item in payload.items]
    ingredients = (
        await db.execute(select(Ingredient).where(Ingredient.branch_id == payload.branch_id, Ingredient.id.in_(ingredient_ids)))
    ).scalars().all()
    if len(ingredients) != len(set(ingredient_ids)):
        raise HTTPException(status_code=400, detail="Recipe includes ingredients outside the branch")

    latest = (
        await db.execute(
            select(Recipe).where(Recipe.branch_id == payload.branch_id, Recipe.name == payload.name).order_by(Recipe.version.desc())
        )
    ).scalars().first()
    next_version = (latest.version + 1) if latest else 1
    if latest:
        latest.is_active = False
        db.add(latest)
    recipe = Recipe(branch_id=payload.branch_id, name=payload.name, version=next_version, is_active=True)
    db.add(recipe)
    await db.flush()
    for item in payload.items:
        db.add(RecipeItem(recipe_id=recipe.id, ingredient_id=item.ingredient_id, quantity=item.quantity))
    await db.commit()
    await db.refresh(recipe)
    return recipe


@router.get("/recipes", response_model=list[RecipeRead])
async def list_recipes(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(select(Recipe).where(Recipe.branch_id == branch_id).order_by(Recipe.name.asc(), Recipe.version.desc()))
    ).scalars().all()


@router.post("/stock-transfers", response_model=StockTransferRead, status_code=status.HTTP_201_CREATED)
async def create_stock_transfer(payload: StockTransferCreate, db: AsyncSession = Depends(get_db)):
    from_ingredient = await db.get(Ingredient, payload.from_ingredient_id)
    to_ingredient = await db.get(Ingredient, payload.to_ingredient_id)
    if not from_ingredient or from_ingredient.branch_id != payload.from_branch_id:
        raise HTTPException(status_code=400, detail="From ingredient does not belong to from_branch")
    if not to_ingredient or to_ingredient.branch_id != payload.to_branch_id:
        raise HTTPException(status_code=400, detail="To ingredient does not belong to to_branch")
    transfer = StockTransfer(**payload.model_dump(), status="pending")
    db.add(transfer)
    await db.commit()
    await db.refresh(transfer)
    return transfer


@router.patch("/stock-transfers/{transfer_id}", response_model=StockTransferRead)
async def action_stock_transfer(transfer_id: int, payload: StockTransferAction, db: AsyncSession = Depends(get_db)):
    transfer = await db.get(StockTransfer, transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Stock transfer not found")
    if transfer.status != "pending":
        raise HTTPException(status_code=409, detail="Stock transfer already resolved")
    transfer.status = payload.status
    transfer.approved_by = payload.approved_by
    if payload.status == "approved":
        from_ingredient = await db.get(Ingredient, transfer.from_ingredient_id)
        to_ingredient = await db.get(Ingredient, transfer.to_ingredient_id)
        if not from_ingredient or not to_ingredient:
            raise HTTPException(status_code=400, detail="Transfer ingredients are missing")
        if from_ingredient.quantity_on_hand < transfer.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock for transfer")
        from_ingredient.quantity_on_hand -= transfer.quantity
        to_ingredient.quantity_on_hand += transfer.quantity
        from_ingredient.updated_at = datetime.utcnow()
        to_ingredient.updated_at = datetime.utcnow()
        db.add(from_ingredient)
        db.add(to_ingredient)
    db.add(transfer)
    await db.commit()
    await db.refresh(transfer)
    return transfer


@router.get("/stock-transfers", response_model=list[StockTransferRead])
async def list_stock_transfers(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(
            select(StockTransfer)
            .where((StockTransfer.from_branch_id == branch_id) | (StockTransfer.to_branch_id == branch_id))
            .order_by(StockTransfer.id.desc())
        )
    ).scalars().all()


@router.post("/purchase-orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(payload: PurchaseOrderCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)

    ingredient_ids = [line.ingredient_id for line in payload.lines]
    ingredients = (
        await db.execute(
            select(Ingredient).where(Ingredient.branch_id == payload.branch_id, Ingredient.id.in_(ingredient_ids))
        )
    ).scalars().all()
    if len(ingredients) != len(set(ingredient_ids)):
        raise HTTPException(status_code=400, detail="Purchase lines include ingredients outside the branch")

    po = PurchaseOrder(branch_id=payload.branch_id, created_by=payload.created_by)
    db.add(po)
    await db.flush()
    for line in payload.lines:
        db.add(PurchaseOrderLine(purchase_order_id=po.id, **line.model_dump()))
    await db.commit()
    await db.refresh(po)
    return po


@router.post("/purchase-orders/{po_id}/receipts")
async def receive_purchase_order(po_id: int, payload: PurchaseReceiptCreate, request: Request, db: AsyncSession = Depends(get_db)):
    replay = await _idempotency_replay(request, db)
    if replay:
        return replay
    po = await db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    for incoming in payload.lines:
        line = await db.get(PurchaseOrderLine, incoming.line_id)
        if not line or line.purchase_order_id != po.id:
            raise HTTPException(status_code=400, detail=f"Invalid purchase line {incoming.line_id}")

        remaining_qty = line.ordered_qty - line.received_qty
        if incoming.received_qty > remaining_qty:
            raise HTTPException(status_code=400, detail=f"Receipt exceeds outstanding quantity for line {line.id}")

        line.received_qty += incoming.received_qty
        ingredient = await db.get(Ingredient, line.ingredient_id)
        if ingredient:
            ingredient.quantity_on_hand += incoming.received_qty
            ingredient.updated_at = datetime.utcnow()
            db.add(
                StockLedgerEntry(
                    ingredient_id=ingredient.id,
                    change_qty=incoming.received_qty,
                    reason="goods_receipt",
                    reference_type="purchase_order",
                    reference_id=po.id,
                )
            )

    lines = (
        await db.execute(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id == po.id))
    ).scalars().all()
    po.status = (
        PurchaseOrderStatus.RECEIVED
        if all(line.received_qty >= line.ordered_qty for line in lines)
        else PurchaseOrderStatus.PARTIAL
    )

    await db.commit()
    await db.refresh(po)
    payload_out = {"purchase_order_id": po.id, "status": po.status}
    await _store_idempotency(request, db, status.HTTP_200_OK, payload_out)
    await db.commit()
    return payload_out


@router.post("/goods-receipts", response_model=GoodsReceiptRead, status_code=status.HTTP_201_CREATED)
async def create_goods_receipt(payload: GoodsReceiptCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)
    if payload.purchase_order_id is not None:
        purchase_order = await db.get(PurchaseOrder, payload.purchase_order_id)
        if not purchase_order or purchase_order.branch_id != payload.branch_id:
            raise HTTPException(status_code=400, detail="Purchase order not found for branch")
    if payload.vendor_id is not None:
        vendor = await db.get(Vendor, payload.vendor_id)
        if not vendor or vendor.branch_id != payload.branch_id:
            raise HTTPException(status_code=400, detail="Vendor not found for branch")

    receipt = GoodsReceipt(**payload.model_dump(), received_at=datetime.utcnow())
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


@router.get("/goods-receipts", response_model=list[GoodsReceiptRead])
async def list_goods_receipts(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(
            select(GoodsReceipt).where(GoodsReceipt.branch_id == branch_id).order_by(GoodsReceipt.received_at.desc())
        )
    ).scalars().all()


@router.post("/bills/{bill_id}/settlements", response_model=BillRead)
async def settle_bill(bill_id: int, payload: BillSettlementCreate, request: Request, db: AsyncSession = Depends(get_db)):
    replay = await _idempotency_replay(request, db)
    if replay:
        return replay
    bill = await db.get(Bill, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    total_new = round(sum(item.amount for item in payload.settlements), 2)
    if bill.paid_amount + total_new > bill.total_amount:
        raise HTTPException(status_code=400, detail="Settlement exceeds outstanding bill amount")

    for settlement_data in payload.settlements:
        db.add(Settlement(bill_id=bill.id, cashier_id=payload.cashier_id, **settlement_data.model_dump()))

    bill.paid_amount = round(bill.paid_amount + total_new, 2)
    bill.status = BillStatus.PAID if bill.paid_amount == bill.total_amount else BillStatus.PARTIALLY_PAID

    await db.commit()
    await db.refresh(bill)
    payload_out = bill.model_dump()
    await _store_idempotency(request, db, status.HTTP_200_OK, payload_out)
    await db.commit()
    return payload_out


@router.post("/discount-approvals", response_model=DiscountApprovalRead, status_code=status.HTTP_201_CREATED)
async def create_discount_approval(payload: DiscountApprovalCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)
    bill = await db.get(Bill, payload.bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    approval = DiscountApproval(**payload.model_dump(), status="pending")
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    return approval


@router.patch("/discount-approvals/{approval_id}", response_model=DiscountApprovalRead)
async def action_discount_approval(approval_id: int, payload: DiscountApprovalAction, db: AsyncSession = Depends(get_db)):
    approval = await db.get(DiscountApproval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Discount approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail="Discount approval already resolved")
    approval.status = payload.status
    approval.approved_by = payload.approved_by
    if payload.status == "approved":
        bill = await db.get(Bill, approval.bill_id)
        if bill:
            bill.total_amount = max(0.0, round(bill.total_amount - approval.discount_amount, 2))
            if bill.paid_amount > bill.total_amount:
                bill.paid_amount = bill.total_amount
            bill.status = BillStatus.PAID if bill.paid_amount == bill.total_amount else BillStatus.PARTIALLY_PAID
            db.add(bill)
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    return approval


@router.post("/refunds", response_model=RefundRead, status_code=status.HTTP_201_CREATED)
async def create_refund(payload: RefundCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)
    bill = await db.get(Bill, payload.bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    if payload.amount > bill.paid_amount:
        raise HTTPException(status_code=400, detail="Refund exceeds paid amount")

    refund = Refund(**payload.model_dump(), created_at=datetime.utcnow())
    bill.paid_amount = round(bill.paid_amount - payload.amount, 2)
    bill.status = BillStatus.PAID if bill.paid_amount == bill.total_amount else BillStatus.PARTIALLY_PAID
    db.add(refund)
    db.add(bill)
    await db.commit()
    await db.refresh(refund)
    return refund


@router.get("/refunds", response_model=list[RefundRead])
async def list_refunds(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (await db.execute(select(Refund).where(Refund.branch_id == branch_id).order_by(Refund.id.desc()))).scalars().all()


@router.post("/drawer-sessions/{session_id}/close", response_model=DrawerSessionRead)
async def close_drawer_session(session_id: int, payload: DrawerCloseRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(CashDrawerSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Drawer session not found")
    if session.status == DrawerStatus.CLOSED:
        raise HTTPException(status_code=409, detail="Drawer session already closed")

    session.status = DrawerStatus.CLOSED
    session.closing_balance = payload.closing_balance
    session.closed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/shifts", status_code=status.HTTP_201_CREATED)
async def create_shift(payload: ShiftCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=400, detail="Shift end time must be after start time")

    shift = Shift(**payload.model_dump())
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    return shift


@router.post("/attendance", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
async def create_attendance(payload: AttendanceCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)
    if payload.shift_id is not None:
        shift = await db.get(Shift, payload.shift_id)
        if not shift or shift.branch_id != payload.branch_id:
            raise HTTPException(status_code=400, detail="Shift not found for branch")

    attendance = AttendanceRecord(**payload.model_dump(), check_in_at=datetime.utcnow())
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.patch("/attendance/{attendance_id}/checkout", response_model=AttendanceRead)
async def checkout_attendance(attendance_id: int, payload: AttendanceCheckout, db: AsyncSession = Depends(get_db)):
    attendance = await db.get(AttendanceRecord, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    if attendance.check_out_at is not None:
        raise HTTPException(status_code=409, detail="Attendance already checked out")

    attendance.check_out_at = datetime.utcnow()
    if payload.notes is not None:
        attendance.notes = payload.notes
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.get("/attendance", response_model=list[AttendanceRead])
async def list_attendance(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(
            select(AttendanceRecord).where(AttendanceRecord.branch_id == branch_id).order_by(AttendanceRecord.check_in_at.desc())
        )
    ).scalars().all()




@router.post("/waitlist", response_model=WaitlistRead, status_code=status.HTTP_201_CREATED)
async def create_waitlist_entry(payload: WaitlistCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)
    entry = WaitlistEntry(**payload.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/waitlist", response_model=WaitlistCursorPage)
async def list_waitlist(branch_id: int, cursor: int | None = None, limit: int = 50, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    statement = select(WaitlistEntry).where(WaitlistEntry.branch_id == branch_id)
    if cursor:
        statement = statement.where(WaitlistEntry.id > cursor)
    rows = (
        await db.execute(statement.order_by(WaitlistEntry.id.asc()).limit(limit))
    ).scalars().all()
    next_cursor = rows[-1].id if len(rows) == limit and rows[-1].id else None
    return {"items": rows, "next_cursor": next_cursor}


@router.patch("/waitlist/{waitlist_id}/promote", response_model=WaitlistRead)
async def promote_waitlist(waitlist_id: int, table_id: int, db: AsyncSession = Depends(get_db)):
    entry = await db.get(WaitlistEntry, waitlist_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Waitlist entry not found")
    if entry.status != WaitlistStatus.WAITING:
        raise HTTPException(status_code=400, detail="Waitlist entry is not active")

    table = await _validate_table_for_branch(table_id, entry.branch_id, db)
    if table.status == TableStatus.OCCUPIED:
        raise HTTPException(status_code=409, detail="Table already occupied")
    if entry.party_size > table.seats:
        raise HTTPException(status_code=400, detail="Party size exceeds table capacity")

    table.status = TableStatus.OCCUPIED
    entry.status = WaitlistStatus.SEATED
    await db.commit()
    await db.refresh(entry)
    return entry


@router.post("/tables/{table_id}/release")
async def release_table(table_id: int, db: AsyncSession = Depends(get_db)):
    table = await db.get(RestaurantTable, table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    table.status = TableStatus.AVAILABLE
    await db.commit()
    return {"table_id": table.id, "status": table.status}


@router.get("/orders", response_model=OrderCursorPage)
async def list_orders(branch_id: int, cursor: int | None = None, limit: int = 50, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    statement = select(Order).where(Order.branch_id == branch_id)
    if cursor:
        statement = statement.where(Order.id < cursor)
    orders = (
        await db.execute(statement.order_by(Order.id.desc()).limit(limit))
    ).scalars().all()
    return _cursor_result(orders, limit)




@router.get("/bills")
async def list_bills(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(
            select(Bill).join(Order, Order.id == Bill.order_id).where(Order.branch_id == branch_id).order_by(Bill.id.desc())
        )
    ).scalars().all()


@router.get("/bills/{bill_id}", response_model=BillRead)
async def get_bill(bill_id: int, db: AsyncSession = Depends(get_db)):
    bill = await db.get(Bill, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


@router.patch("/shifts/{shift_id}")
async def update_shift_status(shift_id: int, payload: ShiftStatusPatch, db: AsyncSession = Depends(get_db)):
    shift = await db.get(Shift, shift_id)
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    shift.status = payload.status
    await db.commit()
    await db.refresh(shift)
    return shift


@router.post("/accounting-exports", response_model=AccountingExportRead, status_code=status.HTTP_201_CREATED)
async def create_accounting_export(payload: AccountingExportCreate, request: Request, db: AsyncSession = Depends(get_db)):
    replay = await _idempotency_replay(request, db)
    if replay:
        return replay
    await _get_branch_or_404(payload.branch_id, db)

    summary = (
        await db.execute(
            select(
                func.coalesce(func.sum(Bill.total_amount), 0.0),
                func.coalesce(func.sum(Bill.paid_amount), 0.0),
                func.count(Bill.id),
            )
            .join(Order, Order.id == Bill.order_id)
            .where(Order.branch_id == payload.branch_id)
        )
    ).one()

    export = AccountingExport(
        branch_id=payload.branch_id,
        business_date=payload.business_date,
        payload_json=(
            '{"gross_sales": %.2f, "collected_sales": %.2f, "bill_count": %d}'
            % (float(summary[0] or 0.0), float(summary[1] or 0.0), int(summary[2] or 0))
        ),
        status=AccountingExportStatus.GENERATED,
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    payload_out = export.model_dump()
    await _store_idempotency(request, db, status.HTTP_201_CREATED, payload_out)
    await db.commit()
    return payload_out


@router.get("/accounting-exports", response_model=list[AccountingExportRead])
async def list_accounting_exports(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(
            select(AccountingExport).where(AccountingExport.branch_id == branch_id).order_by(AccountingExport.created_at.desc())
        )
    ).scalars().all()


@router.post("/day-close", response_model=DayCloseRead, status_code=status.HTTP_201_CREATED)
async def open_day_close(payload: DayCloseCreate, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(payload.branch_id, db)
    existing = (
        await db.execute(
            select(DayClose).where(DayClose.branch_id == payload.branch_id, DayClose.business_date == payload.business_date)
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="Day-close already exists for business date")
    record = DayClose(**payload.model_dump(), status=DayCloseStatus.OPEN)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.patch("/day-close/{day_close_id}/finalize", response_model=DayCloseRead)
async def finalize_day_close(day_close_id: int, payload: DayCloseFinalize, db: AsyncSession = Depends(get_db)):
    record = await db.get(DayClose, day_close_id)
    if not record:
        raise HTTPException(status_code=404, detail="Day-close record not found")
    if record.status == DayCloseStatus.CLOSED:
        raise HTTPException(status_code=409, detail="Day-close already finalized")

    open_drawers = (
        await db.execute(
            select(func.count(CashDrawerSession.id)).where(
                CashDrawerSession.branch_id == record.branch_id,
                CashDrawerSession.status == DrawerStatus.OPEN,
            )
        )
    ).one()[0]
    open_bills = (
        await db.execute(
            select(func.count(Bill.id))
            .join(Order, Order.id == Bill.order_id)
            .where(Order.branch_id == record.branch_id, Bill.status != BillStatus.PAID)
        )
    ).one()[0]
    if open_drawers or open_bills:
        raise HTTPException(
            status_code=409,
            detail=f"Day-close blocked: open_drawers={open_drawers}, open_bills={open_bills}",
        )

    record.status = DayCloseStatus.CLOSED
    record.closed_by = payload.closed_by
    record.notes = payload.notes or record.notes
    record.closed_at = datetime.utcnow()
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/day-close", response_model=list[DayCloseRead])
async def list_day_close(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)
    return (
        await db.execute(select(DayClose).where(DayClose.branch_id == branch_id).order_by(DayClose.business_date.desc()))
    ).scalars().all()


@router.get("/reports/branch-operations")
async def branch_operations_report(branch_id: int, db: AsyncSession = Depends(get_db)):
    await _get_branch_or_404(branch_id, db)

    orders_count = (await db.execute(select(func.count(Order.id)).where(Order.branch_id == branch_id))).one()[0]
    open_tickets = (
        await db.execute(
            select(func.count(KitchenTicket.id))
            .join(OrderItem, OrderItem.id == KitchenTicket.order_item_id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.branch_id == branch_id,
                KitchenTicket.status.in_([KitchenTicketStatus.QUEUED, KitchenTicketStatus.IN_PREPARATION]),
            )
        )
    ).one()[0]
    gross_sales = (
        await db.execute(
            select(func.coalesce(func.sum(Bill.total_amount), 0.0))
            .join(Order, Order.id == Bill.order_id)
            .where(Order.branch_id == branch_id)
        )
    ).one()[0]
    collected_sales = (
        await db.execute(
            select(func.coalesce(func.sum(Bill.paid_amount), 0.0))
            .join(Order, Order.id == Bill.order_id)
            .where(Order.branch_id == branch_id)
        )
    ).one()[0]
    low_stock_count = (
        await db.execute(
            select(func.count(Ingredient.id)).where(
                Ingredient.branch_id == branch_id,
                Ingredient.quantity_on_hand <= Ingredient.reorder_threshold,
            )
        )
    ).one()[0]

    return {
        "branch_id": branch_id,
        "orders_count": orders_count,
        "open_tickets": open_tickets,
        "gross_sales": float(gross_sales or 0.0),
        "collected_sales": float(collected_sales or 0.0),
        "low_stock_count": low_stock_count,
        "generated_at": datetime.utcnow(),
    }


@router.patch("/admin/branch-policies/{policy_id}")
async def update_branch_policy(policy_id: int, payload: BranchPolicyPatch, db: AsyncSession = Depends(get_db)):
    policy = await db.get(BranchPolicy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.value = payload.value
    policy.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(policy)
    return policy
