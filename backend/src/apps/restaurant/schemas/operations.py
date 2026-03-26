from datetime import datetime
from pydantic import BaseModel, Field

from src.apps.restaurant.models import (
    AccountingExportStatus,
    BillStatus,
    DrawerStatus,
    KitchenTicketStatus,
    OrderSource,
    OrderStatus,
    PurchaseOrderStatus,
    ReservationStatus,
    ShiftStatus,
    TableStatus,
    WaitlistStatus,
)


class BranchCreate(BaseModel):
    name: str
    tax_rate: float = Field(default=0.0, ge=0)
    service_charge_rate: float = Field(default=0.0, ge=0)


class BranchRead(BaseModel):
    id: int
    name: str
    tax_rate: float
    service_charge_rate: float
    is_active: bool

    model_config = {"from_attributes": True}


class TableCreate(BaseModel):
    code: str
    seats: int = Field(default=2, ge=1)


class TableRead(BaseModel):
    id: int
    branch_id: int
    code: str
    seats: int
    status: TableStatus

    model_config = {"from_attributes": True}


class MenuItemCreate(BaseModel):
    name: str
    price: float = Field(ge=0)


class MenuItemRead(BaseModel):
    id: int
    branch_id: int
    name: str
    price: float
    is_available: bool

    model_config = {"from_attributes": True}


class IngredientCreate(BaseModel):
    name: str
    unit: str = "unit"
    quantity_on_hand: float = 0.0
    reorder_threshold: float = 0.0


class IngredientRead(BaseModel):
    id: int
    branch_id: int
    name: str
    unit: str
    quantity_on_hand: float
    reorder_threshold: float

    model_config = {"from_attributes": True}




class WaitlistCreate(BaseModel):
    branch_id: int
    guest_name: str
    guest_phone: str
    party_size: int = Field(ge=1)
    notes: str | None = None


class WaitlistRead(BaseModel):
    id: int
    branch_id: int
    guest_name: str
    guest_phone: str
    party_size: int
    status: WaitlistStatus
    notes: str | None

    model_config = {"from_attributes": True}


class ShiftStatusPatch(BaseModel):
    status: ShiftStatus


class AccountingExportCreate(BaseModel):
    branch_id: int
    business_date: datetime


class AccountingExportRead(BaseModel):
    id: int
    branch_id: int
    business_date: datetime
    payload_json: str
    status: AccountingExportStatus

    model_config = {"from_attributes": True}

class ReservationCreate(BaseModel):
    branch_id: int
    guest_name: str
    guest_phone: str
    party_size: int = Field(ge=1)
    reservation_time: datetime
    notes: str | None = None


class ReservationRead(BaseModel):
    id: int
    branch_id: int
    guest_name: str
    guest_phone: str
    party_size: int
    reservation_time: datetime
    table_id: int | None
    status: ReservationStatus
    notes: str | None

    model_config = {"from_attributes": True}


class SeatTableRequest(BaseModel):
    reservation_id: int | None = None
    party_size: int = Field(ge=1)


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(ge=1)
    course_no: int = Field(default=1, ge=1)
    notes: str | None = None


class OrderCreate(BaseModel):
    branch_id: int
    order_source: OrderSource = OrderSource.DINE_IN
    table_id: int | None = None
    waiter_id: int | None = None
    items: list[OrderItemCreate]


class OrderPatch(BaseModel):
    status: OrderStatus | None = None
    items: list[OrderItemCreate] | None = None


class OrderRead(BaseModel):
    id: int
    branch_id: int
    table_id: int | None
    waiter_id: int | None
    order_source: OrderSource
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KitchenTicketRead(BaseModel):
    id: int
    order_item_id: int
    station: str
    status: KitchenTicketStatus
    priority: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class KitchenTicketPatch(BaseModel):
    status: KitchenTicketStatus


class InventoryAdjustmentCreate(BaseModel):
    ingredient_id: int
    change_qty: float
    reason: str


class PurchaseLineCreate(BaseModel):
    ingredient_id: int
    ordered_qty: float = Field(ge=0)
    unit_cost: float = Field(ge=0)


class PurchaseOrderCreate(BaseModel):
    branch_id: int
    created_by: int | None = None
    lines: list[PurchaseLineCreate]


class PurchaseReceiptLine(BaseModel):
    line_id: int
    received_qty: float = Field(gt=0)


class PurchaseReceiptCreate(BaseModel):
    lines: list[PurchaseReceiptLine]


class SettlementItem(BaseModel):
    payment_method: str
    amount: float = Field(gt=0)


class BillSettlementCreate(BaseModel):
    settlements: list[SettlementItem]
    cashier_id: int | None = None


class DrawerSessionCreate(BaseModel):
    cashier_id: int | None = None
    opening_balance: float = Field(default=0, ge=0)


class DrawerCloseRequest(BaseModel):
    closing_balance: float = Field(ge=0)


class ShiftCreate(BaseModel):
    branch_id: int
    staff_user_id: int
    role: str
    starts_at: datetime
    ends_at: datetime
    status: ShiftStatus = ShiftStatus.SCHEDULED


class BranchPolicyCreate(BaseModel):
    key: str
    value: str


class BranchPolicyPatch(BaseModel):
    value: str


class PurchaseOrderResponse(BaseModel):
    id: int
    branch_id: int
    status: PurchaseOrderStatus

    model_config = {"from_attributes": True}


class BillRead(BaseModel):
    id: int
    order_id: int
    subtotal: float
    tax_amount: float
    service_charge: float
    total_amount: float
    paid_amount: float
    status: BillStatus

    model_config = {"from_attributes": True}


class DrawerSessionRead(BaseModel):
    id: int
    branch_id: int
    cashier_id: int | None
    opening_balance: float
    closing_balance: float | None
    status: DrawerStatus

    model_config = {"from_attributes": True}


class WaitlistCursorPage(BaseModel):
    items: list[WaitlistRead]
    next_cursor: int | None = None


class OrderCursorPage(BaseModel):
    items: list[OrderRead]
    next_cursor: int | None = None


class KitchenTicketCursorPage(BaseModel):
    items: list[KitchenTicketRead]
    next_cursor: int | None = None


class ReservationUpdate(BaseModel):
    status: ReservationStatus | None = None
    notes: str | None = None
    table_id: int | None = None
