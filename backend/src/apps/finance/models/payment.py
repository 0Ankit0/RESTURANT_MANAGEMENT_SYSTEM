from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class PaymentProvider(str, Enum):
    KHALTI = "khalti"
    ESEWA = "esewa"
    STRIPE = "stripe"
    PAYPAL = "paypal"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    INITIATED = "initiated"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in {
            PaymentStatus.COMPLETED,
            PaymentStatus.FAILED,
            PaymentStatus.REFUNDED,
            PaymentStatus.CANCELLED,
        }


ALLOWED_PAYMENT_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.PENDING: {PaymentStatus.INITIATED, PaymentStatus.FAILED, PaymentStatus.CANCELLED},
    PaymentStatus.INITIATED: {PaymentStatus.PENDING, PaymentStatus.COMPLETED, PaymentStatus.FAILED, PaymentStatus.CANCELLED},
    PaymentStatus.COMPLETED: {PaymentStatus.REFUNDED},
    PaymentStatus.FAILED: {PaymentStatus.PENDING, PaymentStatus.INITIATED},
    PaymentStatus.REFUNDED: set(),
    PaymentStatus.CANCELLED: set(),
}


def transition_payment_status(
    current: PaymentStatus,
    target: PaymentStatus,
) -> bool:
    """
    Canonical payment status transition rules shared by all providers.

    This function is intentionally provider-agnostic and should be the only
    transition gate used by service/API layers.
    """
    if current == target:
        return True
    return target in ALLOWED_PAYMENT_TRANSITIONS.get(current, set())


class PaymentTransactionBase(SQLModel):
    """Fields shared between table model and validation schemas."""
    provider: PaymentProvider = Field(
        description="Payment gateway provider"
    )
    amount: int = Field(
        description="Amount in the smallest currency unit (e.g. paisa for NPR)"
    )
    currency: str = Field(
        default="NPR",
        max_length=3,
        description="ISO 4217 currency code"
    )
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING,
        description="Current lifecycle status of the transaction"
    )
    purchase_order_id: str = Field(
        index=True,
        max_length=255,
        description="Your internal order/reference ID"
    )
    purchase_order_name: str = Field(
        max_length=255,
        description="Human-readable order description"
    )
    # Provider-assigned identifiers
    provider_transaction_id: Optional[str] = Field(
        default=None,
        index=True,
        max_length=255,
        description="Transaction ID assigned by the payment provider after initiation"
    )
    provider_pidx: Optional[str] = Field(
        default=None,
        index=True,
        max_length=255,
        description="Khalti pidx or eSewa refId — provider's unique payment index"
    )
    # Redirect / callback URLs
    return_url: str = Field(
        max_length=500,
        description="URL the provider redirects the user to after payment"
    )
    website_url: str = Field(
        default="",
        max_length=500,
        description="Merchant website URL (required by some providers)"
    )
    # Optional FK to the platform user who initiated the payment
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="user.id",
        description="Platform user who initiated the payment (nullable for guest checkout)"
    )
    # Extra provider-specific data stored as JSON string
    extra_data: Optional[str] = Field(
        default=None,
        description="JSON-serialized provider-specific metadata"
    )
    failure_reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable reason when status is FAILED"
    )


class PaymentTransaction(PaymentTransactionBase, table=True):
    __tablename__ = "payment_transactions" # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    retry_count: int = Field(default=0, ge=0)
    reconcile_after: Optional[datetime] = Field(default=None, index=True)
    last_reconciled_at: Optional[datetime] = Field(default=None)
    processing_lease_until: Optional[datetime] = Field(default=None, index=True)
    processing_lease_owner: Optional[str] = Field(default=None, max_length=100)
    raw_callback_payload: Optional[str] = Field(
        default=None,
        description="Most recent raw callback payload snapshot for audit",
    )

    def can_transition_to(self, target: PaymentStatus) -> bool:
        return transition_payment_status(self.status, target)


class PaymentWebhookBase(SQLModel):
    """Raw webhook / callback payload received from a payment provider."""
    provider: PaymentProvider = Field(description="Provider that sent the webhook")
    event_type: str = Field(
        default="callback",
        max_length=100,
        description="Provider event type (e.g. payment.completed)"
    )
    transaction_id: Optional[int] = Field(
        default=None,
        foreign_key="payment_transactions.id",
        description="Linked transaction (resolved after matching)"
    )
    raw_payload: str = Field(
        description="Raw JSON payload from the provider"
    )
    is_verified: bool = Field(
        default=False,
        description="Whether the webhook signature/data has been verified"
    )
    ip_address: Optional[str] = Field(
        default=None,
        max_length=45,
        description="IP address the webhook was received from"
    )
    delivery_id: Optional[str] = Field(
        default=None,
        max_length=255,
        index=True,
        description="Provider delivery/event identifier for idempotency",
    )
    payload_hash: Optional[str] = Field(
        default=None,
        max_length=128,
        index=True,
        description="SHA-256 hash of raw payload for duplicate detection",
    )


class PaymentWebhook(PaymentWebhookBase, table=True):
    __tablename__ = "payment_webhooks" # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    received_at: datetime = Field(default_factory=datetime.now)
