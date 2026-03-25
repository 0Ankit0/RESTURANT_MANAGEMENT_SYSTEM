"""
PayPal payment gateway integration using the official `paypalrestsdk` package.

Sandbox credentials (https://developer.paypal.com/dashboard/applications/sandbox):
  1. Create a sandbox app → copy Client ID and Secret.
  2. Set PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_MODE=sandbox in .env.

Test sandbox accounts (auto-created by PayPal developer dashboard):
  Buyer  : use the personal sandbox account email + password
  Seller : use the business sandbox account

Flow:
  1. POST /payments/initiate/ → creates a PayPal Payment → returns approval_url
  2. User approves at approval_url
  3. PayPal redirects to return_url?paymentId=<id>&PayerID=<id>
  4. POST /payments/verify/ with provider=paypal, pidx=<paymentId>, extra oid=<PayerID>
"""
import json
from datetime import datetime

import paypalrestsdk
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.core.config import settings
from src.apps.finance.models.payment import PaymentProvider, PaymentStatus, PaymentTransaction
from src.apps.finance.schemas.payment import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from src.apps.finance.services.base import BasePaymentProvider

# PayPal state → our enum
_STATUS_MAP: dict[str, PaymentStatus] = {
    "created": PaymentStatus.INITIATED,
    "approved": PaymentStatus.PENDING,
    "failed": PaymentStatus.FAILED,
    "canceled": PaymentStatus.CANCELLED,
    "expired": PaymentStatus.FAILED,
    "pending": PaymentStatus.PENDING,
    "completed": PaymentStatus.COMPLETED,
}


def _get_api() -> paypalrestsdk.Api:
    """Return a configured PayPal API client."""
    return paypalrestsdk.Api({
        "mode": settings.PAYPAL_MODE,
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET,
    })


class PayPalService(BasePaymentProvider):
    """PayPal payment provider using the official paypalrestsdk."""

    # ------------------------------------------------------------------ #
    # Initiate                                                             #
    # ------------------------------------------------------------------ #

    async def initiate_payment(
        self,
        request: InitiatePaymentRequest,
        db: AsyncSession,
    ) -> InitiatePaymentResponse:
        """
        Create a PayPal Payment and return the buyer approval URL.

        PayPal expects amounts in major currency units (e.g. USD dollars,
        not cents).  We store the original ``amount`` (minor units / paisa)
        in the DB and convert to dollars for the PayPal API call.
        """
        # Convert from cents to dollars for PayPal (assumes USD cents input)
        amount_dollars = f"{request.amount / 100:.2f}"

        payment = paypalrestsdk.Payment(
            {
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": request.return_url,
                    "cancel_url": request.return_url,
                },
                "transactions": [
                    {
                        "amount": {
                            "total": amount_dollars,
                            "currency": "USD",
                        },
                        "description": request.purchase_order_name,
                        "invoice_number": request.purchase_order_id,
                    }
                ],
            },
            api=_get_api(),
        )

        if not payment.create():
            error = payment.error or "PayPal payment creation failed"
            tx = PaymentTransaction(
                provider=PaymentProvider.PAYPAL,
                amount=request.amount,
                purchase_order_id=request.purchase_order_id,
                purchase_order_name=request.purchase_order_name,
                return_url=request.return_url,
                website_url=request.website_url,
                status=PaymentStatus.FAILED,
                failure_reason=str(error),
            )
            db.add(tx)
            await db.commit()
            await db.refresh(tx)
            raise ValueError(f"PayPal initiation failed: {error}")

        # Extract the buyer approval URL from PayPal links
        approval_url: str | None = next(
            (link.href for link in payment.links if link.rel == "approval_url"),
            None,
        )

        tx = PaymentTransaction(
            provider=PaymentProvider.PAYPAL,
            amount=request.amount,
            purchase_order_id=request.purchase_order_id,
            purchase_order_name=request.purchase_order_name,
            return_url=request.return_url,
            website_url=request.website_url,
            status=PaymentStatus.INITIATED,
            provider_pidx=payment.id,       # PayPal payment ID (PAY-...)
            extra_data=json.dumps({"payment_id": payment.id, "state": payment.state}),
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)

        return InitiatePaymentResponse(
            transaction_id=tx.id,
            provider=PaymentProvider.PAYPAL,
            status=PaymentStatus.INITIATED,
            payment_url=approval_url,
            provider_pidx=payment.id,
            extra={"payment_id": payment.id},
        )

    # ------------------------------------------------------------------ #
    # Verify                                                               #
    # ------------------------------------------------------------------ #

    async def verify_payment(
        self,
        request: VerifyPaymentRequest,
        db: AsyncSession,
    ) -> VerifyPaymentResponse:
        """
        Execute an approved PayPal payment.

        After the buyer approves, PayPal redirects to:
          return_url?paymentId=PAY-xxx&PayerID=yyy

        Send:
          - ``pidx``  = paymentId  (PAY-xxx)
          - ``oid``   = PayerID    (yyy)
        """
        payment_id = request.pidx
        payer_id = request.oid

        if not payment_id:
            raise ValueError("paymentId (pidx) is required for PayPal verification")
        if not payer_id:
            raise ValueError("PayerID (oid) is required for PayPal verification")

        payment = paypalrestsdk.Payment.find(payment_id, api=_get_api())

        if not payment.execute({"payer_id": payer_id}):
            error = payment.error or "PayPal execution failed"
            raise ValueError(f"PayPal execution failed: {error}")

        sale_id: str | None = None
        try:
            sale_id = payment.transactions[0].related_resources[0].sale.id
        except (AttributeError, IndexError):
            pass

        our_status = _STATUS_MAP.get(payment.state.lower(), PaymentStatus.FAILED)
        if payment.state.lower() == "approved":
            our_status = PaymentStatus.COMPLETED

        result = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.provider_pidx == payment_id
            )
        )
        tx: PaymentTransaction | None = result.scalars().first()

        if tx is None:
            raise ValueError(f"No transaction found for PayPal paymentId={payment_id}")

        tx.status = our_status
        tx.provider_transaction_id = sale_id or payment_id
        tx.extra_data = json.dumps({"payment_id": payment.id, "state": payment.state})
        tx.updated_at = datetime.now()
        db.add(tx)
        await db.commit()
        await db.refresh(tx)

        return VerifyPaymentResponse(
            transaction_id=tx.id,
            provider=PaymentProvider.PAYPAL,
            status=our_status,
            amount=tx.amount,
            provider_transaction_id=tx.provider_transaction_id,
            extra={"payment_id": payment.id, "state": payment.state},
        )
