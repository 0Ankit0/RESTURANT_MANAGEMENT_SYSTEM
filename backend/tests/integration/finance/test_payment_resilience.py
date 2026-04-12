import hashlib
import hmac
import json
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.core.config import settings
from src.apps.finance.models.payment import PaymentProvider, PaymentStatus, PaymentTransaction, PaymentWebhook
from src.apps.finance.services.reconciliation_worker import finance_reconciliation_worker


@pytest.mark.integration
async def test_khalti_webhook_tampering_rejected(client: AsyncClient, db_session: AsyncSession):
    payload = {"event": "payment.completed", "pidx": "px_1"}
    raw = json.dumps(payload)

    res = await client.post(
        "/api/v1/payments/webhook/khalti/",
        content=raw,
        headers={"X-Signature": "bad-signature", "X-Event-Id": "evt-1"},
    )

    assert res.status_code == 400

    rows = (await db_session.execute(
        select(PaymentWebhook).where(PaymentWebhook.delivery_id == "evt-1")
    )).scalars().all()
    assert len(rows) == 1
    assert rows[0].is_verified is False


@pytest.mark.integration
async def test_duplicate_webhook_delivery_idempotent(client: AsyncClient, db_session: AsyncSession):
    payload = {"event": "payment.completed", "pidx": "px_2"}
    raw = json.dumps(payload)
    signature = hmac.new(settings.KHALTI_SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()

    first = await client.post(
        "/api/v1/payments/webhook/khalti/",
        content=raw,
        headers={"X-Signature": signature, "X-Event-Id": "evt-dup"},
    )
    second = await client.post(
        "/api/v1/payments/webhook/khalti/",
        content=raw,
        headers={"X-Signature": signature, "X-Event-Id": "evt-dup"},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    rows = (await db_session.execute(
        select(PaymentWebhook).where(PaymentWebhook.delivery_id == "evt-dup")
    )).scalars().all()
    assert len(rows) == 1


@pytest.mark.integration
async def test_stale_pending_reconciliation_auto_fails(db_session: AsyncSession):
    tx = PaymentTransaction(
        provider=PaymentProvider.KHALTI,
        amount=1000,
        purchase_order_id="ORDER-STALE",
        purchase_order_name="stale",
        return_url="https://localhost/callback",
        website_url="https://localhost",
        status=PaymentStatus.PENDING,
        retry_count=4,
        updated_at=datetime.now() - timedelta(hours=2),
    )
    db_session.add(tx)
    await db_session.commit()

    processed = await finance_reconciliation_worker.reconcile_once(limit=20)
    assert processed >= 1

    await db_session.refresh(tx)
    assert tx.status == PaymentStatus.FAILED
    assert "Auto-failed" in (tx.failure_reason or "")


@pytest.mark.integration
async def test_refund_rerun_idempotency(client: AsyncClient, db_session: AsyncSession):
    tx = PaymentTransaction(
        provider=PaymentProvider.KHALTI,
        amount=1000,
        purchase_order_id="ORDER-REFUND",
        purchase_order_name="refund",
        return_url="https://localhost/callback",
        website_url="https://localhost",
        status=PaymentStatus.COMPLETED,
        provider_pidx="refund-pidx",
    )
    db_session.add(tx)
    await db_session.commit()
    await db_session.refresh(tx)

    from src.apps.iam.utils.hashid import encode_id

    encoded_id = encode_id(tx.id)
    first = await client.post(
        f"/api/v1/payments/refunds/{encoded_id}/rerun/",
        headers={"Idempotency-Key": "refund-key-1"},
    )
    replay = await client.post(
        f"/api/v1/payments/refunds/{encoded_id}/rerun/",
        headers={"Idempotency-Key": "refund-key-1"},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.headers.get("X-Idempotent-Replay") == "true"
