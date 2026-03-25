"""
Khalti payment gateway integration (v2 API).

Sandbox credentials (from Khalti documentation):
  Public key : test_public_key_dc74e0fd57cb46cd93832aee0a390234
  Secret key : test_secret_key_dc74e0fd57cb46cd93832aee0a390234
  Base URL   : https://a.khalti.com/api/v2/

Test card (Khalti wallet):
  Mobile : 9800000000 / 9800000001 … 9800000005
  MPIN   : 1111
  OTP    : 987654
"""
import json
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.core.config import settings
from src.apps.core.http import default_timeout
from src.apps.finance.models.payment import PaymentProvider, PaymentStatus, PaymentTransaction
from src.apps.finance.schemas.payment import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from src.apps.finance.services.base import BasePaymentProvider


def _describe_http_error(exc: httpx.HTTPError) -> str:
    """Build a stable error message for otherwise-empty httpx exceptions."""
    error_type = exc.__class__.__name__
    request_url = str(exc.request.url) if exc.request is not None else None
    message = str(exc).strip() or repr(exc)
    if request_url:
        return f"{error_type} while calling {request_url}: {message}"
    return f"{error_type}: {message}"


def _normalize_base_url(url: str) -> str:
    return url if url.endswith("/") else f"{url}/"


class KhaltiService(BasePaymentProvider):
    """Khalti v2 payment provider."""

    BASE_URL: str = settings.KHALTI_BASE_URL

    def _candidate_base_urls(self) -> list[str]:
        """Return the configured Khalti base URL only."""
        return [_normalize_base_url(self.BASE_URL)]

    async def _post_khalti(
        self,
        path: str,
        payload: dict,
    ) -> httpx.Response:
        """POST to Khalti, retrying on transport-level failures across known hosts."""
        last_error: str | None = None
        for base_url in self._candidate_base_urls():
            try:
                async with httpx.AsyncClient() as client:
                    return await client.post(
                        f"{base_url}{path}",
                        json=payload,
                        headers={
                            "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
                            "Content-Type": "application/json",
                        },
                        timeout=default_timeout(30),
                    )
            except httpx.HTTPError as exc:
                last_error = _describe_http_error(exc)
                continue
        raise RuntimeError(
            "Khalti request failed for the configured host. "
            f"Last error: {last_error or 'Unknown transport error.'}"
        )

    # ------------------------------------------------------------------ #
    # Initiate                                                             #
    # ------------------------------------------------------------------ #

    async def initiate_payment(
        self,
        request: InitiatePaymentRequest,
        db: AsyncSession,
    ) -> InitiatePaymentResponse:
        """
        Call Khalti /epayment/initiate/ and persist a transaction record.

        Returns the ``payment_url`` the client should redirect the user to.
        """
        if request.amount < 1000:
            raise ValueError("Khalti amount must be at least 1000 paisa (NPR 10).")

        customer_info: dict = {}
        if request.customer_name:
            customer_info["name"] = request.customer_name
        if request.customer_email:
            customer_info["email"] = request.customer_email
        if request.customer_phone:
            customer_info["phone"] = request.customer_phone

        payload: dict = {
            "return_url": request.return_url,
            "website_url": request.website_url or settings.SERVER_HOST,
            "amount": request.amount,
            "purchase_order_id": request.purchase_order_id,
            "purchase_order_name": request.purchase_order_name,
        }
        if customer_info:
            payload["customer_info"] = customer_info

        try:
            resp = await self._post_khalti("epayment/initiate/", payload)
        except RuntimeError as exc:
            raise RuntimeError(f"Khalti initiation request failed: {exc}") from exc

        if resp.status_code != 200:
            error_detail = resp.text
            tx = PaymentTransaction(
                provider=PaymentProvider.KHALTI,
                amount=request.amount,
                purchase_order_id=request.purchase_order_id,
                purchase_order_name=request.purchase_order_name,
                return_url=request.return_url,
                website_url=request.website_url,
                status=PaymentStatus.FAILED,
                failure_reason=f"Initiation failed: {error_detail}",
                user_id=None,
            )
            db.add(tx)
            await db.commit()
            await db.refresh(tx)
            raise ValueError(f"Khalti initiation failed ({resp.status_code}): {error_detail}")

        data = resp.json()
        pidx: str = data["pidx"]
        payment_url: str = data["payment_url"]

        tx = PaymentTransaction(
            provider=PaymentProvider.KHALTI,
            amount=request.amount,
            purchase_order_id=request.purchase_order_id,
            purchase_order_name=request.purchase_order_name,
            return_url=request.return_url,
            website_url=request.website_url,
            status=PaymentStatus.INITIATED,
            provider_pidx=pidx,
            extra_data=json.dumps(data),
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)

        return InitiatePaymentResponse(
            transaction_id=tx.id,
            provider=PaymentProvider.KHALTI,
            status=PaymentStatus.INITIATED,
            payment_url=payment_url,
            provider_pidx=pidx,
            extra=data,
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
        Call Khalti /epayment/lookup/ with the pidx to verify the payment.

        Khalti sends ``pidx`` as a query parameter to the return_url after
        the user completes (or cancels) payment.
        """
        pidx = request.pidx
        if not pidx:
            raise ValueError("pidx is required for Khalti verification")

        try:
            resp = await self._post_khalti("epayment/lookup/", {"pidx": pidx})
        except RuntimeError as exc:
            raise RuntimeError(f"Khalti lookup request failed: {exc}") from exc

        if resp.status_code != 200:
            raise ValueError(f"Khalti lookup failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        khalti_status: str = data.get("status", "")
        transaction_id_provider: str = data.get("transaction_id", "")

        status_map = {
            "Completed": PaymentStatus.COMPLETED,
            "Pending": PaymentStatus.PENDING,
            "Expired": PaymentStatus.FAILED,
            "User canceled": PaymentStatus.CANCELLED,
            "Refunded": PaymentStatus.REFUNDED,
        }
        our_status = status_map.get(khalti_status, PaymentStatus.FAILED)

        from sqlmodel import select
        result = await db.execute(
            select(PaymentTransaction).where(PaymentTransaction.provider_pidx == pidx)
        )
        tx: PaymentTransaction | None = result.scalars().first()

        if tx is None:
            raise ValueError(f"No transaction found for Khalti pidx={pidx}")

        tx.status = our_status
        tx.provider_transaction_id = transaction_id_provider
        tx.extra_data = json.dumps(data)
        tx.updated_at = datetime.now()
        db.add(tx)
        await db.commit()
        await db.refresh(tx)

        return VerifyPaymentResponse(
            transaction_id=tx.id,
            provider=PaymentProvider.KHALTI,
            status=our_status,
            amount=data.get("total_amount"),
            provider_transaction_id=transaction_id_provider,
            extra=data,
        )
