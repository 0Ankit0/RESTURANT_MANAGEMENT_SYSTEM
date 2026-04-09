from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class TableStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    OUT_OF_SERVICE = "out_of_service"


class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SEATED = "seated"
    CANCELLED = "cancelled"


class OrderSource(str, Enum):
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"


class KitchenTicketStatus(str, Enum):
    QUEUED = "queued"
    IN_PREPARATION = "in_preparation"
    READY = "ready"
    SERVED = "served"
    DELAYED = "delayed"
    VOIDED = "voided"


class PurchaseOrderStatus(str, Enum):
    OPEN = "open"
    PARTIAL = "partial"
    RECEIVED = "received"


class BillStatus(str, Enum):
    OPEN = "open"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"


class ShiftStatus(str, Enum):
    SCHEDULED = "scheduled"
    STARTED = "started"
    CLOSED = "closed"


class DrawerStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class WaitlistStatus(str, Enum):
    WAITING = "waiting"
    SEATED = "seated"
    CANCELLED = "cancelled"


class AccountingExportStatus(str, Enum):
    GENERATED = "generated"
    SENT = "sent"


class DayCloseStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class StockCountSessionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class StockTransferLifecycleStatus(str, Enum):
    REQUESTED = "requested"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    REJECTED = "rejected"


class AccountingExportRetryStatus(str, Enum):
    QUEUED = "queued"
    COMPLETED = "completed"
    FAILED = "failed"



class Branch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=120, index=True)
    tax_rate: float = Field(default=0.0, ge=0)
    service_charge_rate: float = Field(default=0.0, ge=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RestaurantTable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    code: str = Field(max_length=32, index=True)
    seats: int = Field(default=2, ge=1)
    status: TableStatus = Field(default=TableStatus.AVAILABLE)


class Reservation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    guest_name: str = Field(max_length=120)
    guest_phone: str = Field(max_length=40)
    party_size: int = Field(ge=1)
    reservation_time: datetime
    table_id: Optional[int] = Field(default=None, foreign_key="restauranttable.id")
    status: ReservationStatus = Field(default=ReservationStatus.PENDING)
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MenuItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=120, index=True)
    price: float = Field(ge=0)
    is_available: bool = Field(default=True)


class Ingredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=120, index=True)
    unit: str = Field(max_length=20, default="unit")
    quantity_on_hand: float = Field(default=0.0)
    reorder_threshold: float = Field(default=0.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    table_id: Optional[int] = Field(default=None, foreign_key="restauranttable.id")
    waiter_id: Optional[int] = Field(default=None)
    order_source: OrderSource = Field(default=OrderSource.DINE_IN)
    status: OrderStatus = Field(default=OrderStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id", index=True)
    menu_item_id: int = Field(foreign_key="menuitem.id", index=True)
    quantity: int = Field(ge=1)
    course_no: int = Field(default=1, ge=1)
    notes: Optional[str] = Field(default=None, max_length=500)
    line_total: float = Field(default=0.0, ge=0)


class KitchenTicket(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_item_id: int = Field(foreign_key="orderitem.id", index=True)
    station: str = Field(default="main", max_length=60)
    status: KitchenTicketStatus = Field(default=KitchenTicketStatus.QUEUED)
    priority: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StockLedgerEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id", index=True)
    change_qty: float
    reason: str = Field(max_length=120)
    reference_type: str = Field(max_length=80)
    reference_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PurchaseOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    status: PurchaseOrderStatus = Field(default=PurchaseOrderStatus.OPEN)
    created_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PurchaseOrderLine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    purchase_order_id: int = Field(foreign_key="purchaseorder.id", index=True)
    ingredient_id: int = Field(foreign_key="ingredient.id")
    ordered_qty: float = Field(ge=0)
    received_qty: float = Field(default=0, ge=0)
    unit_cost: float = Field(default=0, ge=0)


class Bill(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id", unique=True, index=True)
    subtotal: float = Field(default=0, ge=0)
    tax_amount: float = Field(default=0, ge=0)
    service_charge: float = Field(default=0, ge=0)
    total_amount: float = Field(default=0, ge=0)
    paid_amount: float = Field(default=0, ge=0)
    status: BillStatus = Field(default=BillStatus.OPEN)


class Settlement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bill_id: int = Field(foreign_key="bill.id", index=True)
    payment_method: str = Field(max_length=32)
    amount: float = Field(ge=0)
    cashier_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CashDrawerSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    cashier_id: Optional[int] = None
    opening_balance: float = Field(default=0)
    closing_balance: Optional[float] = Field(default=None)
    status: DrawerStatus = Field(default=DrawerStatus.OPEN)
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None


class Shift(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    staff_user_id: int
    role: str = Field(max_length=64)
    starts_at: datetime
    ends_at: datetime
    status: ShiftStatus = Field(default=ShiftStatus.SCHEDULED)


class BranchPolicy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    key: str = Field(max_length=80, index=True)
    value: str = Field(max_length=500)
    updated_at: datetime = Field(default_factory=datetime.utcnow)




class BranchPaymentMethod(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    code: str = Field(max_length=40)
    display_name: str = Field(max_length=80)
    is_active: bool = Field(default=True)


class BranchPrinter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=80)
    target: str = Field(max_length=200)
    zone: Optional[str] = Field(default=None, max_length=80)
    is_active: bool = Field(default=True)


class KitchenStation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=80)
    code: str = Field(max_length=40)
    is_expo: bool = Field(default=False)
    is_active: bool = Field(default=True)


class PrivilegedActionAudit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    action: str = Field(max_length=120, index=True)
    actor_user_id: Optional[int] = Field(default=None, index=True)
    resource_type: str = Field(max_length=80)
    resource_id: Optional[int] = Field(default=None)
    payload_json: Optional[str] = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WaitlistEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    guest_name: str = Field(max_length=120)
    guest_phone: str = Field(max_length=40)
    party_size: int = Field(ge=1)
    status: WaitlistStatus = Field(default=WaitlistStatus.WAITING)
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AccountingExport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    business_date: datetime
    payload_json: str = Field(max_length=4000)
    status: AccountingExportStatus = Field(default=AccountingExportStatus.GENERATED)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IdempotencyRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(max_length=120, index=True)
    endpoint: str = Field(max_length=200, index=True)
    status_code: int = Field(default=200)
    response_json: str = Field(max_length=12000)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ServiceZone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=120)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TableGroup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=120)
    table_ids_csv: str = Field(max_length=500, default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AttendanceRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    staff_user_id: int
    shift_id: Optional[int] = Field(default=None, foreign_key="shift.id")
    check_in_at: datetime = Field(default_factory=datetime.utcnow)
    check_out_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=300)


class DayClose(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    business_date: datetime
    status: DayCloseStatus = Field(default=DayCloseStatus.OPEN)
    closed_by: Optional[int] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None


class Vendor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=120, index=True)
    contact_name: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=40)
    email: Optional[str] = Field(default=None, max_length=120)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GoodsReceipt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    purchase_order_id: Optional[int] = Field(default=None, foreign_key="purchaseorder.id")
    vendor_id: Optional[int] = Field(default=None, foreign_key="vendor.id")
    notes: Optional[str] = Field(default=None, max_length=500)
    received_at: datetime = Field(default_factory=datetime.utcnow)


class MenuCategory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=120)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class ModifierGroup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=120)
    min_select: int = Field(default=0, ge=0)
    max_select: int = Field(default=1, ge=1)
    is_required: bool = Field(default=False)


class ModifierOption(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    modifier_group_id: int = Field(foreign_key="modifiergroup.id", index=True)
    name: str = Field(max_length=120)
    extra_price: float = Field(default=0, ge=0)
    is_active: bool = Field(default=True)


class TaxRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=120)
    rate: float = Field(default=0, ge=0)
    version: int = Field(default=1, ge=1)
    is_active: bool = Field(default=True)
    effective_from: datetime = Field(default_factory=datetime.utcnow)


class DiscountApproval(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    bill_id: int = Field(foreign_key="bill.id", index=True)
    requested_by: int
    approved_by: Optional[int] = None
    discount_amount: float = Field(default=0, ge=0)
    reason: str = Field(max_length=300)
    status: str = Field(default="pending", max_length=30)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Refund(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    bill_id: int = Field(foreign_key="bill.id", index=True)
    settlement_id: Optional[int] = Field(default=None, foreign_key="settlement.id")
    amount: float = Field(default=0, ge=0)
    reason: Optional[str] = Field(default=None, max_length=300)
    approved_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Recipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    name: str = Field(max_length=120)
    version: int = Field(default=1, ge=1)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RecipeItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id", index=True)
    ingredient_id: int = Field(foreign_key="ingredient.id", index=True)
    quantity: float = Field(gt=0)


class StockTransfer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_branch_id: int = Field(foreign_key="branch.id", index=True)
    to_branch_id: int = Field(foreign_key="branch.id", index=True)
    from_ingredient_id: int = Field(foreign_key="ingredient.id", index=True)
    to_ingredient_id: int = Field(foreign_key="ingredient.id", index=True)
    quantity: float = Field(gt=0)  # requested quantity
    shipped_qty: float = Field(default=0, ge=0)
    received_qty: float = Field(default=0, ge=0)
    discrepancy_notes: Optional[str] = Field(default=None, max_length=400)
    status: str = Field(default=StockTransferLifecycleStatus.REQUESTED, max_length=20)
    approved_by: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StockCountSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    status: StockCountSessionStatus = Field(default=StockCountSessionStatus.DRAFT)
    opened_by: Optional[int] = None
    submitted_by: Optional[int] = None
    approved_by: Optional[int] = None
    rejection_reason: Optional[str] = Field(default=None, max_length=300)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None


class StockCountLine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="stockcountsession.id", index=True)
    ingredient_id: int = Field(foreign_key="ingredient.id", index=True)
    expected_qty: float = Field(default=0, ge=0)
    counted_qty: float = Field(default=0, ge=0)
    variance_qty: float = Field(default=0)
    notes: Optional[str] = Field(default=None, max_length=300)


class DayCloseChecklistItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    day_close_id: int = Field(foreign_key="dayclose.id", index=True)
    item_key: str = Field(max_length=120)
    is_required: bool = Field(default=True)
    is_checked: bool = Field(default=False)
    checked_by: Optional[int] = None
    checked_at: Optional[datetime] = None


class AccountingExportRetry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    accounting_export_id: int = Field(foreign_key="accountingexport.id", index=True)
    requested_by: Optional[int] = None
    status: AccountingExportRetryStatus = Field(default=AccountingExportRetryStatus.QUEUED)
    message: Optional[str] = Field(default=None, max_length=400)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class KitchenTicketEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="kitchenticket.id", index=True)
    from_status: KitchenTicketStatus
    to_status: KitchenTicketStatus
    updated_by: Optional[int] = None
    pass_seconds: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrderEditApproval(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id", index=True)
    requested_by: int
    approved_by: Optional[int] = None
    reason: str = Field(max_length=300)
    status: str = Field(default="pending", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
