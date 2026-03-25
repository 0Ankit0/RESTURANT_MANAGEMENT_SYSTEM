"""
Finance payment API endpoints (v1).

POST /payments/initiate     — initiate a payment with any provider
POST /payments/verify       — verify / process a provider callback
GET  /payments/{id}         — retrieve a stored transaction record
GET  /payments/             — list transactions (authenticated users)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, col

from src.apps.core.config import settings

from src.apps.finance.models.payment import PaymentProvider, PaymentTransaction
from src.apps.finance.schemas.payment import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    PaymentTransactionRead,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from src.apps.finance.services.base import BasePaymentProvider
from src.apps.finance.services.esewa import EsewaService
from src.apps.finance.services.khalti import KhaltiService
from src.apps.finance.services.stripe import StripeService
from src.apps.finance.services.paypal import PayPalService
from src.apps.iam.api.deps import get_db
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.analytics.dependencies import get_analytics
from src.apps.analytics.service import AnalyticsService
from src.apps.analytics.events import PaymentEvents

router = APIRouter()

# ---------------------------------------------------------------------------
# Provider registry — built at startup, respects per-provider enabled flags
# ---------------------------------------------------------------------------

def _build_registry() -> dict[PaymentProvider, BasePaymentProvider]:
    registry: dict[PaymentProvider, BasePaymentProvider] = {}
    if settings.KHALTI_ENABLED:
        registry[PaymentProvider.KHALTI] = KhaltiService()
    if settings.ESEWA_ENABLED:
        registry[PaymentProvider.ESEWA] = EsewaService()
    if settings.STRIPE_ENABLED:
        registry[PaymentProvider.STRIPE] = StripeService()
    if settings.PAYPAL_ENABLED:
        registry[PaymentProvider.PAYPAL] = PayPalService()
    return registry

_PROVIDERS: dict[PaymentProvider, BasePaymentProvider] = _build_registry()


def _describe_exception(exc: Exception) -> str:
    """Format exceptions so blank provider errors remain actionable."""
    message = str(exc).strip()
    if message:
        return message
    return f"{exc.__class__.__name__}: {exc!r}"


def _get_provider(provider: PaymentProvider) -> BasePaymentProvider:
    svc = _PROVIDERS.get(provider)
    if svc is None:
        # Distinguish "disabled" from "unknown"
        known = {p.value for p in PaymentProvider}
        if provider.value in known:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment provider '{provider}' is currently disabled.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment provider '{provider}' is not supported.",
        )
    return svc


# ---------------------------------------------------------------------------
# List enabled providers
# ---------------------------------------------------------------------------

@router.get("/providers/", response_model=list[str])
async def list_enabled_providers() -> list[str]:
    """Return the list of currently enabled payment providers."""
    return [p.value for p in _PROVIDERS]


# ---------------------------------------------------------------------------
# Initiate payment
# ---------------------------------------------------------------------------

@router.post("/initiate/", response_model=InitiatePaymentResponse)
async def initiate_payment(
    request_body: InitiatePaymentRequest,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> InitiatePaymentResponse:
    """
    Initiate a new payment with the specified provider.

    Returns the payment URL (Khalti) or form fields (eSewa) the client
    should use to redirect / submit the user to the provider's checkout.
    """
    provider_svc = _get_provider(request_body.provider)
    try:
        result = await provider_svc.initiate_payment(request_body, db)
        distinct_id = str(result.transaction_id)
        await analytics.capture(
            distinct_id,
            PaymentEvents.PAYMENT_INITIATED,
            {
                "provider": request_body.provider.value,
                "amount": request_body.amount,
                "purchase_order_id": request_body.purchase_order_id,
                "transaction_id": result.transaction_id,
            },
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment provider error: {_describe_exception(exc)}",
        )


# ---------------------------------------------------------------------------
# Verify payment
# ---------------------------------------------------------------------------

@router.post("/verify/", response_model=VerifyPaymentResponse)
async def verify_payment(
    request_body: VerifyPaymentRequest,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> VerifyPaymentResponse:
    """
    Verify a payment after the provider redirects the user back.

    - **Khalti**: send ``provider=khalti`` and ``pidx`` received in callback.
    - **eSewa**: send ``provider=esewa`` and the base64 ``data`` param from callback.
    """
    provider_svc = _get_provider(request_body.provider)
    try:
        result = await provider_svc.verify_payment(request_body, db)
        from src.apps.finance.models.payment import PaymentStatus
        event = (
            PaymentEvents.PAYMENT_COMPLETED
            if result.status == PaymentStatus.COMPLETED
            else PaymentEvents.PAYMENT_FAILED
        )
        await analytics.capture(
            str(result.transaction_id),
            event,
            {
                "provider": request_body.provider.value,
                "status": result.status.value,
                "amount": result.amount,
                "transaction_id": result.transaction_id,
            },
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment provider error: {_describe_exception(exc)}",
        )


# ---------------------------------------------------------------------------
# Retrieve a single transaction
# ---------------------------------------------------------------------------

@router.get("/{transaction_id}/", response_model=PaymentTransactionRead)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
) -> PaymentTransactionRead:
    """Fetch a stored payment transaction by its internal ID."""
    decoded_transaction_id = decode_id_or_404(transaction_id)
    tx = await db.get(PaymentTransaction, decoded_transaction_id)
    if tx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found.",
        )
    return PaymentTransactionRead.model_validate(tx)


# ---------------------------------------------------------------------------
# List transactions (with optional filters)
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[PaymentTransactionRead])
async def list_transactions(
    provider: Optional[PaymentProvider] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[PaymentTransactionRead]:
    """List payment transactions with optional provider filter."""
    query = select(PaymentTransaction).order_by(
        col(PaymentTransaction.id).desc()
    ).limit(limit).offset(offset)

    if provider:
        query = query.where(PaymentTransaction.provider == provider)

    result = await db.execute(query)
    transactions = result.scalars().all()
    return [PaymentTransactionRead.model_validate(tx) for tx in transactions]
