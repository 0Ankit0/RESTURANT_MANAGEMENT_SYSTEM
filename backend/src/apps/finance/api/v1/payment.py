"""
Finance payment API endpoints (v1).

POST /payments/initiate     — initiate a payment with any provider
POST /payments/verify       — verify / process a provider callback
GET  /payments/{id}         — retrieve a stored transaction record
GET  /payments/             — list transactions (authenticated users)
"""
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, col

from src.apps.core.config import settings

from src.apps.finance.models.payment import (
    PaymentProvider,
    PaymentStatus,
    PaymentTransaction,
    PaymentWebhook,
)
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
from src.apps.finance.services.reconciliation_worker import finance_reconciliation_worker
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


async def _verify_from_callback(
    provider: PaymentProvider,
    db: AsyncSession,
    analytics: AnalyticsService,
    *,
    pidx: str | None = None,
    oid: str | None = None,
    refId: str | None = None,
    data: str | None = None,
) -> VerifyPaymentResponse:
    raw_snapshot = json.dumps(
        {"pidx": pidx, "oid": oid, "refId": refId, "data": data},
        default=str,
    )
    payload = VerifyPaymentRequest(
        provider=provider,
        pidx=pidx,
        oid=oid,
        refId=refId,
        data=data,
    )
    result = await _get_provider(provider).verify_payment(payload, db)
    tx = await db.get(PaymentTransaction, result.transaction_id)
    if tx is not None:
        tx.raw_callback_payload = raw_snapshot
        db.add(tx)
        await db.commit()
    event = (
        PaymentEvents.PAYMENT_COMPLETED
        if result.status == PaymentStatus.COMPLETED
        else PaymentEvents.PAYMENT_FAILED
    )
    await analytics.capture(
        str(result.transaction_id),
        event,
        {"provider": provider.value, "status": result.status.value, "transaction_id": result.transaction_id},
    )
    return result


def _payload_hash(raw_payload: str) -> str:
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()


def _hmac_signature(secret: str, payload: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


async def _record_webhook(
    db: AsyncSession,
    *,
    provider: PaymentProvider,
    event_type: str,
    raw_payload: str,
    verified: bool,
    ip_address: str | None,
    delivery_id: str | None,
    transaction_id: int | None = None,
) -> PaymentWebhook:
    payload_hash = _payload_hash(raw_payload)
    duplicate_result = await db.execute(
        select(PaymentWebhook).where(
            PaymentWebhook.provider == provider,
            PaymentWebhook.payload_hash == payload_hash,
            PaymentWebhook.delivery_id == delivery_id,
        )
    )
    existing = duplicate_result.scalars().first()
    if existing:
        return existing

    row = PaymentWebhook(
        provider=provider,
        event_type=event_type,
        transaction_id=transaction_id,
        raw_payload=raw_payload,
        is_verified=verified,
        ip_address=ip_address,
        delivery_id=delivery_id,
        payload_hash=payload_hash,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def _apply_processing_lease(
    db: AsyncSession,
    tx: PaymentTransaction,
    *,
    owner: str,
    seconds: int = 60,
) -> None:
    now = datetime.now()
    if tx.processing_lease_until and tx.processing_lease_until > now:
        raise HTTPException(status_code=409, detail="Transaction is already being processed")
    tx.processing_lease_owner = owner
    tx.processing_lease_until = now + timedelta(seconds=seconds)
    db.add(tx)
    await db.commit()
    await db.refresh(tx)


async def _clear_processing_lease(db: AsyncSession, tx: PaymentTransaction) -> None:
    tx.processing_lease_owner = None
    tx.processing_lease_until = None
    db.add(tx)
    await db.commit()


@router.get("/callback/khalti/", response_model=VerifyPaymentResponse)
async def khalti_callback(
    pidx: str = Query(...),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> VerifyPaymentResponse:
    return await _verify_from_callback(PaymentProvider.KHALTI, db, analytics, pidx=pidx)


@router.get("/callback/esewa/", response_model=VerifyPaymentResponse)
async def esewa_callback(
    data: str = Query(...),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> VerifyPaymentResponse:
    return await _verify_from_callback(PaymentProvider.ESEWA, db, analytics, data=data)


@router.get("/callback/stripe/", response_model=VerifyPaymentResponse)
async def stripe_callback(
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> VerifyPaymentResponse:
    return await _verify_from_callback(PaymentProvider.STRIPE, db, analytics, pidx=session_id)


@router.get("/callback/paypal/", response_model=VerifyPaymentResponse)
async def paypal_callback(
    paymentId: str = Query(...),
    PayerID: str = Query(...),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> VerifyPaymentResponse:
    return await _verify_from_callback(PaymentProvider.PAYPAL, db, analytics, pidx=paymentId, oid=PayerID)


@router.post("/reconcile/{transaction_id}/", response_model=VerifyPaymentResponse)
async def reconcile_transaction(
    transaction_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> VerifyPaymentResponse:
    """
    Retry-safe reconciliation for pending/failed verification states.
    """
    decoded_id = decode_id_or_404(transaction_id)
    tx = await db.get(PaymentTransaction, decoded_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.provider_pidx is None and tx.provider != PaymentProvider.ESEWA:
        raise HTTPException(status_code=400, detail="Missing provider reference for reconciliation")

    callback_data = request.query_params.get("data")
    if tx.provider == PaymentProvider.ESEWA and not callback_data:
        raise HTTPException(
            status_code=400,
            detail="eSewa reconciliation requires callback `data` query parameter.",
        )

    return await _verify_from_callback(
        tx.provider,
        db,
        analytics,
        pidx=tx.provider_pidx,
        data=callback_data,
    )


@router.post("/reconcile/run")
async def reconcile_pending_transactions() -> dict[str, int]:
    processed = await finance_reconciliation_worker.reconcile_once(limit=100)
    return {"processed": processed}


@router.post("/retry/{transaction_id}/", response_model=VerifyPaymentResponse)
async def retry_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> VerifyPaymentResponse:
    decoded_id = decode_id_or_404(transaction_id)
    tx = await db.get(PaymentTransaction, decoded_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    await _apply_processing_lease(db, tx, owner="manual_retry")
    try:
        return await _verify_from_callback(
            tx.provider,
            db,
            analytics,
            pidx=tx.provider_pidx,
        )
    finally:
        await _clear_processing_lease(db, tx)


@router.post("/refunds/{transaction_id}/rerun/")
async def refund_rerun(
    transaction_id: str,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")

    decoded_id = decode_id_or_404(transaction_id)
    tx = await db.get(PaymentTransaction, decoded_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    key = f"refund-rerun:{idempotency_key}"
    if tx.processing_lease_owner == key and tx.processing_lease_until and tx.processing_lease_until > datetime.now():
        response.headers["X-Idempotent-Replay"] = "true"
        return {"transaction_id": transaction_id, "status": "completed"}

    await _apply_processing_lease(db, tx, owner=key, seconds=120)
    try:
        if tx.status != PaymentStatus.COMPLETED:
            raise HTTPException(status_code=409, detail="Only completed transactions can be refunded")
        tx.status = PaymentStatus.REFUNDED
        tx.failure_reason = None
        tx.updated_at = datetime.now()
        db.add(tx)
        await db.commit()
        return {"transaction_id": transaction_id, "status": "completed"}
    finally:
        await _clear_processing_lease(db, tx)


@router.post("/webhook/stripe/")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    raw_payload = (await request.body()).decode("utf-8")
    verified = False
    event_type = "unknown"
    delivery_id = request.headers.get("Stripe-Event-Id")
    try:
        if not stripe_signature:
            raise ValueError("Missing Stripe-Signature header")
        event = stripe.Webhook.construct_event(raw_payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET)
        verified = True
        event_type = event.get("type", "unknown")
    except Exception:
        await _record_webhook(
            db,
            provider=PaymentProvider.STRIPE,
            event_type=event_type,
            raw_payload=raw_payload,
            verified=False,
            ip_address=request.client.host if request.client else None,
            delivery_id=delivery_id,
        )
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature")

    row = await _record_webhook(
        db,
        provider=PaymentProvider.STRIPE,
        event_type=event_type,
        raw_payload=raw_payload,
        verified=verified,
        ip_address=request.client.host if request.client else None,
        delivery_id=delivery_id,
    )
    return {"accepted": True, "webhook_id": row.id, "event_type": event_type}


@router.post("/webhook/khalti/")
async def khalti_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    x_event_id: str | None = Header(default=None, alias="X-Event-Id"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    raw_payload = (await request.body()).decode("utf-8")
    event_type = "callback"
    if x_signature != _hmac_signature(settings.KHALTI_SECRET_KEY, raw_payload):
        await _record_webhook(
            db,
            provider=PaymentProvider.KHALTI,
            event_type=event_type,
            raw_payload=raw_payload,
            verified=False,
            ip_address=request.client.host if request.client else None,
            delivery_id=x_event_id,
        )
        raise HTTPException(status_code=400, detail="Invalid Khalti webhook signature")
    row = await _record_webhook(
        db,
        provider=PaymentProvider.KHALTI,
        event_type=event_type,
        raw_payload=raw_payload,
        verified=True,
        ip_address=request.client.host if request.client else None,
        delivery_id=x_event_id,
    )
    return {"accepted": True, "webhook_id": row.id}


@router.post("/webhook/esewa/")
async def esewa_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    x_event_id: str | None = Header(default=None, alias="X-Event-Id"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    raw_payload = (await request.body()).decode("utf-8")
    expected = _hmac_signature(settings.ESEWA_SECRET_KEY, raw_payload)
    if x_signature != expected:
        await _record_webhook(
            db,
            provider=PaymentProvider.ESEWA,
            event_type="callback",
            raw_payload=raw_payload,
            verified=False,
            ip_address=request.client.host if request.client else None,
            delivery_id=x_event_id,
        )
        raise HTTPException(status_code=400, detail="Invalid eSewa webhook signature")
    row = await _record_webhook(
        db,
        provider=PaymentProvider.ESEWA,
        event_type="callback",
        raw_payload=raw_payload,
        verified=True,
        ip_address=request.client.host if request.client else None,
        delivery_id=x_event_id,
    )
    return {"accepted": True, "webhook_id": row.id}


@router.post("/webhook/paypal/")
async def paypal_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    x_event_id: str | None = Header(default=None, alias="X-Event-Id"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    raw_payload = (await request.body()).decode("utf-8")
    expected = _hmac_signature(settings.PAYPAL_CLIENT_SECRET, raw_payload)
    if x_signature != expected:
        await _record_webhook(
            db,
            provider=PaymentProvider.PAYPAL,
            event_type="callback",
            raw_payload=raw_payload,
            verified=False,
            ip_address=request.client.host if request.client else None,
            delivery_id=x_event_id,
        )
        raise HTTPException(status_code=400, detail="Invalid PayPal webhook signature")
    row = await _record_webhook(
        db,
        provider=PaymentProvider.PAYPAL,
        event_type="callback",
        raw_payload=raw_payload,
        verified=True,
        ip_address=request.client.host if request.client else None,
        delivery_id=x_event_id,
    )
    return {"accepted": True, "webhook_id": row.id}


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
