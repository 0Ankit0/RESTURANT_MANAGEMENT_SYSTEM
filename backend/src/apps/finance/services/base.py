"""Abstract base class for all payment provider integrations."""
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.finance.models.payment import PaymentTransaction
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
