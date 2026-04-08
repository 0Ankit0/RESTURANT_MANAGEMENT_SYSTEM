from datetime import datetime
from pydantic import BaseModel, Field

from src.apps.restaurant.models import (
    AccountingExportRetryStatus,
    AccountingExportStatus,
    BillStatus,
    DayCloseStatus,
    DrawerStatus,
    KitchenTicketStatus,
    OrderSource,
    OrderStatus,
    PurchaseOrderStatus,
    ReservationStatus,
    StockCountSessionStatus,
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


class ServiceZoneCreate(BaseModel):
    name: str


class ServiceZoneRead(BaseModel):
    id: int
    branch_id: int
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class TableGroupCreate(BaseModel):
    name: str
    table_ids: list[int] = Field(default_factory=list)


class TableGroupRead(BaseModel):
    id: int
    branch_id: int
    name: str
    table_ids_csv: str

    model_config = {"from_attributes": True}


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


class MenuCategoryCreate(BaseModel):
    name: str
    display_order: int = 0


class MenuCategoryRead(BaseModel):
    id: int
    branch_id: int
    name: str
    display_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class ModifierGroupCreate(BaseModel):
    name: str
    min_select: int = Field(default=0, ge=0)
    max_select: int = Field(default=1, ge=1)
    is_required: bool = False


class ModifierGroupRead(BaseModel):
    id: int
    branch_id: int
    name: str
    min_select: int
    max_select: int
    is_required: bool

    model_config = {"from_attributes": True}


class ModifierOptionCreate(BaseModel):
    name: str
    extra_price: float = Field(default=0, ge=0)


class ModifierOptionRead(BaseModel):
    id: int
    modifier_group_id: int
    name: str
    extra_price: float
    is_active: bool

    model_config = {"from_attributes": True}


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


class VendorCreate(BaseModel):
    name: str
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None


class VendorRead(BaseModel):
    id: int
    branch_id: int
    name: str
    contact_name: str | None
    phone: str | None
    email: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class GoodsReceiptCreate(BaseModel):
    branch_id: int
    purchase_order_id: int | None = None
    vendor_id: int | None = None
    notes: str | None = None


class GoodsReceiptRead(BaseModel):
    id: int
    branch_id: int
    purchase_order_id: int | None
    vendor_id: int | None
    notes: str | None
    received_at: datetime

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


class TaxRuleCreate(BaseModel):
    branch_id: int
    name: str
    rate: float = Field(default=0, ge=0)
    effective_from: datetime | None = None


class TaxRuleRead(BaseModel):
    id: int
    branch_id: int
    name: str
    rate: float
    version: int
    is_active: bool
    effective_from: datetime

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
    updated_by: int | None = None


class InventoryAdjustmentCreate(BaseModel):
    ingredient_id: int
    change_qty: float
    reason: str


class RecipeItemCreate(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0)


class RecipeCreate(BaseModel):
    branch_id: int
    name: str
    items: list[RecipeItemCreate]


class RecipeRead(BaseModel):
    id: int
    branch_id: int
    name: str
    version: int
    is_active: bool

    model_config = {"from_attributes": True}


class StockTransferCreate(BaseModel):
    from_branch_id: int
    to_branch_id: int
    from_ingredient_id: int
    to_ingredient_id: int
    quantity: float = Field(gt=0)


class StockTransferAction(BaseModel):
    approved_by: int | None = None
    action: str = "mark_in_transit"
    shipped_qty: float | None = Field(default=None, gt=0)
    received_qty: float | None = Field(default=None, gt=0)
    discrepancy_notes: str | None = None


class StockTransferRead(BaseModel):
    id: int
    from_branch_id: int
    to_branch_id: int
    from_ingredient_id: int
    to_ingredient_id: int
    quantity: float
    shipped_qty: float
    received_qty: float
    discrepancy_notes: str | None
    status: str
    approved_by: int | None

    model_config = {"from_attributes": True}


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


class AttendanceCreate(BaseModel):
    branch_id: int
    staff_user_id: int
    shift_id: int | None = None
    notes: str | None = None


class AttendanceCheckout(BaseModel):
    notes: str | None = None


class AttendanceRead(BaseModel):
    id: int
    branch_id: int
    staff_user_id: int
    shift_id: int | None
    check_in_at: datetime
    check_out_at: datetime | None
    notes: str | None

    model_config = {"from_attributes": True}


class BranchPolicyCreate(BaseModel):
    key: str
    value: str


class BranchPolicyPatch(BaseModel):
    value: str


class DiscountApprovalCreate(BaseModel):
    branch_id: int
    bill_id: int
    requested_by: int
    discount_amount: float = Field(default=0, ge=0)
    reason: str


class DiscountApprovalAction(BaseModel):
    approved_by: int
    status: str = "approved"


class DiscountApprovalRead(BaseModel):
    id: int
    branch_id: int
    bill_id: int
    requested_by: int
    approved_by: int | None
    discount_amount: float
    reason: str
    status: str

    model_config = {"from_attributes": True}


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


class RefundCreate(BaseModel):
    branch_id: int
    bill_id: int
    settlement_id: int | None = None
    amount: float = Field(gt=0)
    reason: str | None = None
    approved_by: int | None = None


class RefundRead(BaseModel):
    id: int
    branch_id: int
    bill_id: int
    settlement_id: int | None
    amount: float
    reason: str | None
    approved_by: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DayCloseCreate(BaseModel):
    branch_id: int
    business_date: datetime
    notes: str | None = None


class DayCloseFinalize(BaseModel):
    closed_by: int | None = None
    notes: str | None = None


class DayCloseRead(BaseModel):
    id: int
    branch_id: int
    business_date: datetime
    status: DayCloseStatus
    closed_by: int | None
    notes: str | None
    closed_at: datetime | None

    model_config = {"from_attributes": True}


class StockCountSessionCreate(BaseModel):
    branch_id: int
    opened_by: int | None = None


class StockCountLineUpsert(BaseModel):
    ingredient_id: int
    counted_qty: float = Field(ge=0)
    notes: str | None = None


class StockCountReviewAction(BaseModel):
    reviewer_id: int | None = None
    action: str = "approve"
    rejection_reason: str | None = None


class StockCountSessionRead(BaseModel):
    id: int
    branch_id: int
    status: StockCountSessionStatus
    opened_by: int | None
    submitted_by: int | None
    approved_by: int | None
    rejection_reason: str | None

    model_config = {"from_attributes": True}


class AccountingExportRetryCreate(BaseModel):
    requested_by: int | None = None
    reason: str | None = None


class AccountingExportRetryRead(BaseModel):
    id: int
    accounting_export_id: int
    requested_by: int | None
    status: AccountingExportRetryStatus
    message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class DayCloseChecklistCreate(BaseModel):
    item_key: str
    is_required: bool = True


class DayCloseChecklistRead(BaseModel):
    id: int
    day_close_id: int
    item_key: str
    is_required: bool
    is_checked: bool
    checked_by: int | None
    checked_at: datetime | None

    model_config = {"from_attributes": True}


class DayCloseChecklistCheck(BaseModel):
    checked_by: int | None = None
    is_checked: bool = True


class OrderEditApprovalCreate(BaseModel):
    order_id: int
    requested_by: int
    reason: str


class OrderEditApprovalAction(BaseModel):
    approved_by: int | None = None
    status: str = "approved"


class OrderEditApprovalRead(BaseModel):
    id: int
    order_id: int
    requested_by: int
    approved_by: int | None
    reason: str
    status: str

    model_config = {"from_attributes": True}


class OrderPatchWithApproval(OrderPatch):
    edit_approval_id: int | None = None
