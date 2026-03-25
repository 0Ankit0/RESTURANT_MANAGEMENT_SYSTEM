"""
eSewa payment gateway integration (v2 API).

Sandbox credentials (from eSewa documentation):
  Merchant code (product_code) : EPAYTEST
  Secret key                   : 8gBm/:&EnhH.1/q
  Form endpoint                : https://rc-epay.esewa.com.np/api/epay/main/v2/form
  Verify endpoint              : https://rc-epay.esewa.com.np/api/epay/transaction/status/

Test eSewa account:
  eSewa ID (mobile) : 9806800001 / 9806800002 / 9806800003 / 9806800004 / 9806800005
  Password          : Nepal@123
  OTP               : 123456

Signature algorithm:
  HMAC-SHA256(
      "total_amount=<value>,transaction_uuid=<value>,product_code=<value>",
      secret_key,
  )
"""
import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.core.config import settings
from src.apps.core.http import default_timeout, retry_async
from src.apps.finance.models.payment import PaymentProvider, PaymentStatus, PaymentTransaction
from src.apps.finance.schemas.payment import (
    EsewaCallbackData,
    EsewaInitiateData,
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from src.apps.finance.services.base import BasePaymentProvider


def _compute_esewa_signature(message: str, secret: str) -> str:
    """Return base64-encoded HMAC-SHA256 of *message* using *secret*."""
    sig = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(sig).decode("utf-8")


def _build_esewa_signed_message(
    signed_field_names: str,
    payload: dict[str, object],
    *,
    include_field_names: bool = True,
) -> str:
    """Build the message string used for eSewa HMAC signing."""
    fields = [field.strip() for field in signed_field_names.split(",") if field.strip()]
    if include_field_names:
        return ",".join(f"{field}={payload.get(field, '')}" for field in fields)
    return ",".join(str(payload.get(field, "")) for field in fields)


class EsewaService(BasePaymentProvider):
    """eSewa v2 payment provider."""

    FORM_URL: str = settings.ESEWA_BASE_URL + "main/v2/form"
    STATUS_URL: str = settings.ESEWA_BASE_URL + "transaction/status/"

    # ------------------------------------------------------------------ #
    # Initiate                                                             #
    # ------------------------------------------------------------------ #

    async def initiate_payment(
        self,
        request: InitiatePaymentRequest,
        db: AsyncSession,
    ) -> InitiatePaymentResponse:
        """
        Build eSewa form data (including the HMAC signature) and persist
        a PaymentTransaction record.

        eSewa v2 does NOT use a server-side redirect — the client must
        submit an HTML form POST to the eSewa endpoint.  We return all
        required form fields in ``extra`` so the frontend can render or
        auto-submit the form.
        """
        transaction_uuid = str(uuid.uuid4())
        total_amount = request.amount  # eSewa expects rupees (not paisa)

        signed_field_names = "total_amount,transaction_uuid,product_code"
        signing_payload = {
            "total_amount": total_amount,
            "transaction_uuid": transaction_uuid,
            "product_code": settings.ESEWA_MERCHANT_CODE,
        }
        message = _build_esewa_signed_message(signed_field_names, signing_payload)
        signature = _compute_esewa_signature(message, settings.ESEWA_SECRET_KEY)

        form_data = EsewaInitiateData(
            amount=request.amount,
            tax_amount=0,
            total_amount=total_amount,
            transaction_uuid=transaction_uuid,
            product_code=settings.ESEWA_MERCHANT_CODE,
            product_service_charge=0,
            product_delivery_charge=0,
            success_url=request.return_url,
            failure_url=request.return_url,
            signed_field_names=signed_field_names,
            signature=signature,
        )

        tx = PaymentTransaction(
            provider=PaymentProvider.ESEWA,
            amount=request.amount,
            purchase_order_id=request.purchase_order_id,
            purchase_order_name=request.purchase_order_name,
            return_url=request.return_url,
            website_url=request.website_url,
            status=PaymentStatus.INITIATED,
            provider_pidx=transaction_uuid,
            extra_data=json.dumps(form_data.model_dump()),
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)
        assert tx.id is not None

        return InitiatePaymentResponse(
            transaction_id=tx.id,
            provider=PaymentProvider.ESEWA,
            status=PaymentStatus.INITIATED,
            payment_url=self.FORM_URL,
            provider_pidx=transaction_uuid,
            extra={
                "form_action": self.FORM_URL,
                "form_fields": form_data.model_dump(),
                "note": (
                    "Submit these fields as an HTML form POST to `form_action`. "
                    "eSewa will redirect the user back to success_url / failure_url."
                ),
            },
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
        Verify eSewa payment from callback data.

        eSewa v2 sends a base64-encoded JSON object as the ``data`` query
        parameter to the success_url.  We decode it, verify the signature,
        then call the eSewa status API to double-check.
        """
        if not request.data:
            raise ValueError("eSewa callback 'data' parameter is required for verification")

        # ------ decode callback -------------------------------------------
        try:
            decoded = json.loads(base64.b64decode(request.data).decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"Failed to decode eSewa callback data: {exc}") from exc

        cb = EsewaCallbackData(**decoded)

        # ------ verify signature ------------------------------------------
        if cb.signed_field_names and cb.signature:
            message = _build_esewa_signed_message(cb.signed_field_names, decoded)
            expected_sig = _compute_esewa_signature(message, settings.ESEWA_SECRET_KEY)
            legacy_message = _build_esewa_signed_message(
                cb.signed_field_names,
                decoded,
                include_field_names=False,
            )
            legacy_sig = _compute_esewa_signature(legacy_message, settings.ESEWA_SECRET_KEY)
            if cb.signature not in {expected_sig, legacy_sig}:
                raise ValueError("eSewa callback signature verification failed")

        # ------ double-check via status API --------------------------------
        transaction_uuid = cb.transaction_uuid
        if not transaction_uuid:
            raise ValueError("transaction_uuid missing from eSewa callback")

        async with httpx.AsyncClient() as client:
            resp = await retry_async(
                lambda: client.get(
                    self.STATUS_URL,
                    params={
                        "product_code": settings.ESEWA_MERCHANT_CODE,
                        "transaction_uuid": transaction_uuid,
                        "total_amount": cb.total_amount,
                    },
                    timeout=default_timeout(30),
                )
            )

        esewa_status_data: dict = {}
        if resp.status_code == 200:
            esewa_status_data = resp.json()

        # Map eSewa status → our enum
        esewa_status_str = (
            esewa_status_data.get("status") or cb.status or ""
        ).upper()
        status_map = {
            "COMPLETE": PaymentStatus.COMPLETED,
            "PENDING": PaymentStatus.PENDING,
            "FULL_REFUND": PaymentStatus.REFUNDED,
            "PARTIAL_REFUND": PaymentStatus.REFUNDED,
            "AMBIGUOUS": PaymentStatus.FAILED,
            "NOT_FOUND": PaymentStatus.FAILED,
            "CANCELED": PaymentStatus.CANCELLED,
        }
        our_status = status_map.get(esewa_status_str, PaymentStatus.FAILED)

        # ------ update transaction ----------------------------------------
        from sqlmodel import select
        result = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.provider_pidx == transaction_uuid
            )
        )
        tx: PaymentTransaction | None = result.scalars().first()

        if tx is None:
            raise ValueError(f"No transaction found for eSewa transaction_uuid={transaction_uuid}")

        tx.status = our_status
        tx.provider_transaction_id = cb.transaction_code or esewa_status_data.get("ref_id")
        tx.extra_data = json.dumps({
            "callback": decoded,
            "status_api": esewa_status_data,
        })
        tx.updated_at = datetime.now()
        db.add(tx)
        await db.commit()
        await db.refresh(tx)
        assert tx.id is not None

        return VerifyPaymentResponse(
            transaction_id=tx.id,
            provider=PaymentProvider.ESEWA,
            status=our_status,
            amount=tx.amount,
            provider_transaction_id=tx.provider_transaction_id,
            extra={
                "callback": decoded,
                "status_api": esewa_status_data,
            },
        )
