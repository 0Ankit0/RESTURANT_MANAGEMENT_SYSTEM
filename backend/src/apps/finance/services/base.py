"""Abstract base class and shared contract helpers for payment providers."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.finance.models.payment import (
    PaymentStatus,
    PaymentTransaction,
    transition_payment_status,
)
from src.apps.finance.schemas.payment import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)


class BasePaymentProvider(ABC):
    """
    Every payment provider must implement these two methods.

    - ``initiate_payment``: creates a transaction record, calls the
      provider's API, and returns the payment URL (or form data) for
      the client to redirect the user to.

    - ``verify_payment``: processes the provider callback / webhook,
      verifies the payment, and updates the transaction record.
    """

    @abstractmethod
    async def initiate_payment(
        self,
        request: InitiatePaymentRequest,
        db: AsyncSession,
    ) -> InitiatePaymentResponse:
        """
        Initiate a new payment with the provider.

        Should:
        1. Persist a ``PaymentTransaction`` row with status=INITIATED.
        2. Call the provider API.
        3. Return an ``InitiatePaymentResponse`` containing the payment URL.
        """

    @abstractmethod
    async def verify_payment(
        self,
        request: VerifyPaymentRequest,
        db: AsyncSession,
    ) -> VerifyPaymentResponse:
        """
        Verify/confirm a payment after the provider callback.

        Should:
        1. Look up the existing ``PaymentTransaction``.
        2. Call the provider verification API or validate the signature.
        3. Update the transaction status.
        4. Return a ``VerifyPaymentResponse``.
        """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    async def _get_transaction(
        self, db: AsyncSession, transaction_id: int
    ) -> PaymentTransaction:
        """Fetch a transaction by PK; raise ValueError if not found."""
        tx = await db.get(PaymentTransaction, transaction_id)
        if tx is None:
            raise ValueError(f"PaymentTransaction {transaction_id} not found")
        return tx

    def map_error(self, exc: Exception) -> ValueError:
        """Normalize provider exceptions into API-safe ValueErrors."""
        message = str(exc).strip() or repr(exc)
        return ValueError(f"{self.__class__.__name__}: {message}")

    def ensure_transition_allowed(
        self,
        tx: PaymentTransaction,
        target_status: PaymentStatus,
    ) -> None:
        """Guard transaction state transitions from service code."""
        if not transition_payment_status(tx.status, target_status):
            raise ValueError(
                f"Invalid transition {tx.status.value} -> {target_status.value} "
                f"for transaction {tx.id}"
            )

    def apply_transition(
        self,
        tx: PaymentTransaction,
        target_status: PaymentStatus,
        *,
        failure_reason: str | None = None,
    ) -> None:
        """Apply guarded state transition and standard bookkeeping."""
        self.ensure_transition_allowed(tx, target_status)
        tx.status = target_status
        tx.updated_at = datetime.now()
        if target_status == PaymentStatus.FAILED:
            tx.failure_reason = failure_reason or tx.failure_reason
        elif target_status == PaymentStatus.COMPLETED:
            tx.failure_reason = None

    async def reconcile_transaction(
        self,
        tx: PaymentTransaction,
        db: AsyncSession,
        *,
        allowed_current: Iterable[PaymentStatus] = (
            PaymentStatus.PENDING,
            PaymentStatus.INITIATED,
            PaymentStatus.FAILED,
        ),
    ) -> PaymentTransaction:
        """
        Retry-safe reconciliation entrypoint used by callbacks.

        If a transaction is already final, reconciliation is a no-op.
        """
        if tx.status in {PaymentStatus.COMPLETED, PaymentStatus.REFUNDED, PaymentStatus.CANCELLED}:
            return tx
        if tx.status not in set(allowed_current):
            raise ValueError(
                f"Transaction {tx.id} in state {tx.status.value} is not reconcilable"
            )
        db.add(tx)
        return tx
