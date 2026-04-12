from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from sqlmodel import select

from src.apps.core.config import settings
from src.apps.finance.models.payment import PaymentStatus, PaymentTransaction
from src.apps.finance.services.base import BasePaymentProvider
from src.db.session import async_session_factory


class FinanceReconciliationWorker:
    """Periodic worker to reconcile stale PENDING/INITIATED payment transactions."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._shutdown = asyncio.Event()
        self.interval_seconds = 60
        self.max_retry = 5
        self.stale_after = timedelta(minutes=15)

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._shutdown.clear()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if not self._task:
            return
        self._shutdown.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run_loop(self) -> None:
        while not self._shutdown.is_set():
            try:
                await self.reconcile_once(limit=50)
            except Exception:
                # best-effort background worker
                pass
            try:
                await asyncio.wait_for(self._shutdown.wait(), timeout=self.interval_seconds)
            except asyncio.TimeoutError:
                continue

    async def reconcile_once(self, *, limit: int = 25) -> int:
        from src.apps.finance.api.v1.payment import _PROVIDERS

        now = datetime.now()
        cutoff = now - self.stale_after

        async with async_session_factory() as db:
            rows = await db.execute(
                select(PaymentTransaction)
                .where(PaymentTransaction.status.in_([PaymentStatus.PENDING, PaymentStatus.INITIATED]))
                .where(PaymentTransaction.updated_at <= cutoff)
                .where(PaymentTransaction.retry_count < self.max_retry)
                .order_by(PaymentTransaction.updated_at.asc())
                .limit(limit)
            )
            candidates = list(rows.scalars().all())

            processed = 0
            for tx in candidates:
                provider: BasePaymentProvider | None = _PROVIDERS.get(tx.provider)
                if provider is None:
                    continue

                tx.last_reconciled_at = now
                tx.retry_count += 1
                tx.reconcile_after = now + timedelta(minutes=min(tx.retry_count * 5, 30))

                if tx.provider_pidx:
                    try:
                        from src.apps.finance.schemas.payment import VerifyPaymentRequest

                        await provider.verify_payment(
                            VerifyPaymentRequest(provider=tx.provider, pidx=tx.provider_pidx),
                            db,
                        )
                    except Exception:
                        if tx.retry_count >= self.max_retry and tx.status in {
                            PaymentStatus.PENDING,
                            PaymentStatus.INITIATED,
                        }:
                            tx.status = PaymentStatus.FAILED
                            tx.failure_reason = "Auto-failed after reconciliation retry limit"
                            tx.updated_at = now
                elif tx.retry_count >= self.max_retry:
                    tx.status = PaymentStatus.FAILED
                    tx.failure_reason = "Auto-failed: missing provider reference for reconciliation"
                    tx.updated_at = now

                db.add(tx)
                processed += 1

            await db.commit()
            return processed


finance_reconciliation_worker = FinanceReconciliationWorker()
