"""
Stripe payment gateway integration using the official `stripe` Python SDK.

Test credentials (from https://dashboard.stripe.com/test/apikeys):
  Secret key      : sk_test_... (from your Stripe dashboard → Test mode)
  Webhook secret  : whsec_...  (from Stripe CLI: `stripe listen --print-secret`)

Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET in your .env / Settings.

Test cards (https://stripe.com/docs/testing#cards):
  Success          : 4242 4242 4242 4242  exp: any future date  CVC: any 3 digits
  Auth required    : 4000 0025 0000 3155
  Decline          : 4000 0000 0000 9995

Flow:
  1. POST /payments/initiate/ → creates a Stripe Checkout Session → returns payment_url
  2. User pays at payment_url
  3. Stripe redirects to return_url?session_id={CHECKOUT_SESSION_ID}
  4. POST /payments/verify/ with provider=stripe and pidx=<session_id>
"""
import json
from datetime import datetime

import stripe
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

# Stripe status → our enum
_STATUS_MAP: dict[str, PaymentStatus] = {
    "complete": PaymentStatus.COMPLETED,
    "open": PaymentStatus.PENDING,
    "expired": PaymentStatus.FAILED,
}


class StripeService(BasePaymentProvider):
    """Stripe payment provider using the official stripe-python SDK."""

    def __init__(self) -> None:
        stripe.api_key = settings.STRIPE_SECRET_KEY

    # ------------------------------------------------------------------ #
    # Initiate                                                             #
    # ------------------------------------------------------------------ #

    async def initiate_payment(
        self,
        request: InitiatePaymentRequest,
        db: AsyncSession,
    ) -> InitiatePaymentResponse:
        """
        Create a Stripe Checkout Session and persist a transaction record.

        Returns the hosted ``payment_url`` (``session.url``) the client
        should redirect the user to.
        """
        # Build success / cancel URLs — append session_id placeholder so the
        # frontend can read it back after the redirect.
        success_url = f"{request.return_url}?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = request.return_url

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": request.amount,  # Stripe expects cents
                        "product_data": {"name": request.purchase_order_name},
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "purchase_order_id": request.purchase_order_id,
            },
        )

        tx = PaymentTransaction(
            provider=PaymentProvider.STRIPE,
            amount=request.amount,
            currency="usd",
            purchase_order_id=request.purchase_order_id,
            purchase_order_name=request.purchase_order_name,
            return_url=request.return_url,
            website_url=request.website_url,
            status=PaymentStatus.INITIATED,
            provider_pidx=session.id,          # Stripe session ID
            extra_data=json.dumps({
                "session_id": session.id,
                "payment_status": session.payment_status,
            }),
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)

        return InitiatePaymentResponse(
            transaction_id=tx.id,
            provider=PaymentProvider.STRIPE,
            status=PaymentStatus.INITIATED,
            payment_url=session.url,
            provider_pidx=session.id,
            extra={"session_id": session.id},
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
        Retrieve a Stripe Checkout Session and update the transaction.

        Stripe appends ``?session_id=<id>`` to the success_url — pass that
        as ``pidx`` in the verify request.
        """
        session_id = request.pidx
        if not session_id:
            raise ValueError("session_id (pidx) is required for Stripe verification")

        session = stripe.checkout.Session.retrieve(session_id)

        our_status = _STATUS_MAP.get(session.status, PaymentStatus.FAILED)
        # Also check payment_status for completed sessions
        if session.status == "complete" and session.payment_status == "paid":
            our_status = PaymentStatus.COMPLETED

        result = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.provider_pidx == session_id
            )
        )
        tx: PaymentTransaction | None = result.scalars().first()

        if tx is None:
            raise ValueError(f"No transaction found for Stripe session_id={session_id}")

        tx.status = our_status
        tx.provider_transaction_id = session.payment_intent
        tx.extra_data = json.dumps({
            "session_id": session.id,
            "status": session.status,
            "payment_status": session.payment_status,
            "payment_intent": session.payment_intent,
        })
        tx.updated_at = datetime.now()
        db.add(tx)
        await db.commit()
        await db.refresh(tx)

        return VerifyPaymentResponse(
            transaction_id=tx.id,
            provider=PaymentProvider.STRIPE,
            status=our_status,
            amount=tx.amount,
            provider_transaction_id=session.payment_intent,
            extra={
                "session_id": session.id,
                "payment_status": session.payment_status,
            },
        )
