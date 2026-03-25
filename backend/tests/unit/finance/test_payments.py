"""
Unit tests for the finance payment endpoints.
Uses mocked httpx calls so no real network traffic is made.
"""
import base64
import hashlib
import hmac
import json
import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.finance.models.payment import PaymentProvider, PaymentStatus, PaymentTransaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esewa_sig(message: str, secret: str = "8gBm/:&EnhH.1/q") -> str:
    sig = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(sig).decode()


def _esewa_signed_message(
    signed_field_names: str,
    payload: dict[str, str],
    *,
    include_field_names: bool = True,
) -> str:
    fields = [field.strip() for field in signed_field_names.split(",") if field.strip()]
    if include_field_names:
        return ",".join(f"{field}={payload[field]}" for field in fields)
    return ",".join(payload[field] for field in fields)


def _esewa_callback_data(transaction_uuid: str, total_amount: int = 100) -> str:
    """Build a valid base64-encoded eSewa callback data blob."""
    product_code = "EPAYTEST"
    signed_field_names = "transaction_code,status,total_amount,transaction_uuid,product_code,signed_field_names"
    fields_values = {
        "transaction_code": "TXNCODE123",
        "status": "COMPLETE",
        "total_amount": str(total_amount),
        "transaction_uuid": transaction_uuid,
        "product_code": product_code,
        "signed_field_names": signed_field_names,
    }
    message = _esewa_signed_message(signed_field_names, fields_values)
    sig = _esewa_sig(message)
    fields_values["signature"] = sig
    return base64.b64encode(json.dumps(fields_values).encode()).decode()


# ---------------------------------------------------------------------------
# Khalti tests
# ---------------------------------------------------------------------------

class TestKhaltiPayment:
    """Tests for Khalti payment initiate + verify flow."""

    @pytest.mark.unit
    async def test_khalti_initiate_success(self, client: AsyncClient, db_session: AsyncSession):
        """Initiating a Khalti payment should return a payment_url and pidx."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pidx": "test_pidx_abc123",
            "payment_url": "https://test-pay.khalti.com/?pidx=test_pidx_abc123",
            "expires_at": "2024-12-31T23:59:59",
            "expires_in": 1800,
        }
        mock_response.text = json.dumps(mock_response.json.return_value)

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("src.apps.finance.services.khalti.httpx.AsyncClient", return_value=mock_client):
            resp = await client.post(
                "/api/v1/payments/initiate/",
                json={
                    "provider": "khalti",
                    "amount": 1000,
                    "purchase_order_id": "ORDER-001",
                    "purchase_order_name": "Test Order",
                    "return_url": "http://localhost:3000/payment/callback",
                    "website_url": "http://localhost:3000",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "khalti"
        assert data["status"] == "initiated"
        assert data["payment_url"] == "https://test-pay.khalti.com/?pidx=test_pidx_abc123"
        assert data["provider_pidx"] == "test_pidx_abc123"
        assert data["transaction_id"] is not None

    @pytest.mark.unit
    async def test_khalti_initiate_includes_phone_customer_info(self, client: AsyncClient):
        """Khalti initiate should send customer_info.phone per the current API contract."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pidx": "test_pidx_customer_001",
            "payment_url": "https://test-pay.khalti.com/?pidx=test_pidx_customer_001",
        }
        mock_response.text = json.dumps(mock_response.json.return_value)

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("src.apps.finance.services.khalti.httpx.AsyncClient", return_value=mock_client):
            resp = await client.post(
                "/api/v1/payments/initiate/",
                json={
                    "provider": "khalti",
                    "amount": 1000,
                    "purchase_order_id": "ORDER-CUSTOMER-001",
                    "purchase_order_name": "Customer Order",
                    "return_url": "http://localhost:3000/payment/callback",
                    "website_url": "http://localhost:3000",
                    "customer_name": "Test User",
                    "customer_email": "test@example.com",
                    "customer_phone": "9800000000",
                },
            )

        assert resp.status_code == 200
        _, kwargs = mock_client.post.await_args
        assert kwargs["json"]["customer_info"] == {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "9800000000",
        }
        assert kwargs["headers"]["Authorization"].startswith("Key ")

    @pytest.mark.unit
    async def test_khalti_initiate_transport_error_has_message(self, client: AsyncClient):
        """Transport-level Khalti errors should surface a useful 502 detail."""
        request = httpx.Request("POST", "https://dev.khalti.com/api/v2/epayment/initiate/")
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ReadError("", request=request))

        with patch("src.apps.finance.services.khalti.httpx.AsyncClient", return_value=mock_client):
            resp = await client.post(
                "/api/v1/payments/initiate/",
                json={
                    "provider": "khalti",
                    "amount": 1000,
                    "purchase_order_id": "ORDER-ERR-READ",
                    "purchase_order_name": "Read Error Order",
                    "return_url": "http://localhost:3000/payment/callback",
                },
            )

        assert resp.status_code == 502
        assert "Khalti initiation request failed" in resp.json()["detail"]
        assert "configured host" in resp.json()["detail"]
        assert "ReadError" in resp.json()["detail"]

    @pytest.mark.unit
    async def test_khalti_initiate_minimum_amount_guard(self, client: AsyncClient):
        """Khalti initiate should fail fast for amounts below NPR 10."""
        resp = await client.post(
            "/api/v1/payments/initiate/",
            json={
                "provider": "khalti",
                "amount": 999,
                "purchase_order_id": "ORDER-LOW-AMOUNT",
                "purchase_order_name": "Low Amount Order",
                "return_url": "http://localhost:3000/payment/callback",
            },
        )

        assert resp.status_code == 400
        assert "at least 1000 paisa" in resp.json()["detail"]

    @pytest.mark.unit
    async def test_khalti_initiate_provider_error(self, client: AsyncClient):
        """When Khalti returns an error, endpoint should return 400."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 400
        mock_response.text = '{"detail": "Invalid amount"}'

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("src.apps.finance.services.khalti.httpx.AsyncClient", return_value=mock_client):
            resp = await client.post(
                "/api/v1/payments/initiate/",
                json={
                    "provider": "khalti",
                    "amount": 1000,
                    "purchase_order_id": "ORDER-ERR",
                    "purchase_order_name": "Bad Order",
                    "return_url": "http://localhost:3000/callback",
                },
            )

        assert resp.status_code == 400

    @pytest.mark.unit
    async def test_khalti_verify_success(self, client: AsyncClient, db_session: AsyncSession):
        """Verifying a Khalti payment should update the transaction to COMPLETED."""
        # Pre-create a transaction record as if initiation already happened
        tx = PaymentTransaction(
            provider=PaymentProvider.KHALTI,
            amount=1000,
            purchase_order_id="ORDER-001",
            purchase_order_name="Test Order",
            return_url="http://localhost:3000/callback",
            website_url="http://localhost:3000",
            status=PaymentStatus.INITIATED,
            provider_pidx="test_pidx_abc123",
        )
        db_session.add(tx)
        await db_session.commit()
        await db_session.refresh(tx)

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pidx": "test_pidx_abc123",
            "total_amount": 1000,
            "status": "Completed",
            "transaction_id": "KHALTI_TXN_XYZ",
            "fee": 30,
            "refunded": False,
        }

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("src.apps.finance.services.khalti.httpx.AsyncClient", return_value=mock_client):
            resp = await client.post(
                "/api/v1/payments/verify/",
                json={
                    "provider": "khalti",
                    "pidx": "test_pidx_abc123",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["provider_transaction_id"] == "KHALTI_TXN_XYZ"
        assert data["transaction_id"] == tx.id

    @pytest.mark.unit
    async def test_khalti_verify_missing_pidx(self, client: AsyncClient):
        """Verifying without pidx should return 400."""
        resp = await client.post(
            "/api/v1/payments/verify/",
            json={"provider": "khalti"},
        )
        assert resp.status_code == 400

    @pytest.mark.unit
    async def test_khalti_verify_cancelled(self, client: AsyncClient, db_session: AsyncSession):
        """Khalti 'User canceled' status should map to CANCELLED."""
        tx = PaymentTransaction(
            provider=PaymentProvider.KHALTI,
            amount=500,
            purchase_order_id="ORDER-CANCEL",
            purchase_order_name="Cancelled Order",
            return_url="http://localhost:3000/callback",
            website_url="",
            status=PaymentStatus.INITIATED,
            provider_pidx="pidx_cancel",
        )
        db_session.add(tx)
        await db_session.commit()
        await db_session.refresh(tx)

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pidx": "pidx_cancel",
            "total_amount": 500,
            "status": "User canceled",
            "transaction_id": None,
            "fee": 0,
            "refunded": False,
        }

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("src.apps.finance.services.khalti.httpx.AsyncClient", return_value=mock_client):
            resp = await client.post(
                "/api/v1/payments/verify/",
                json={"provider": "khalti", "pidx": "pidx_cancel"},
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"


# ---------------------------------------------------------------------------
# eSewa tests
# ---------------------------------------------------------------------------

class TestEsewaPayment:
    """Tests for eSewa payment initiate + verify flow."""

    @pytest.mark.unit
    async def test_esewa_initiate_success(self, client: AsyncClient, db_session: AsyncSession):
        """Initiating an eSewa payment returns form_fields with a valid signature."""
        resp = await client.post(
            "/api/v1/payments/initiate/",
            json={
                "provider": "esewa",
                "amount": 100,
                "purchase_order_id": "ESEWA-ORDER-001",
                "purchase_order_name": "Test eSewa Order",
                "return_url": "http://localhost:3000/payment/esewa/callback",
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "esewa"
        assert data["status"] == "initiated"
        assert data["payment_url"] is not None
        assert "form_fields" in data["extra"]

        form_fields = data["extra"]["form_fields"]
        assert form_fields["product_code"] == "EPAYTEST"
        assert form_fields["total_amount"] == 100
        assert form_fields["signed_field_names"] == "total_amount,transaction_uuid,product_code"
        assert "signature" in form_fields

        # Verify the signature is correct
        message = _esewa_signed_message(
            form_fields["signed_field_names"],
            {
                "total_amount": str(form_fields["total_amount"]),
                "transaction_uuid": form_fields["transaction_uuid"],
                "product_code": form_fields["product_code"],
            },
        )
        expected_sig = _esewa_sig(message)
        assert form_fields["signature"] == expected_sig

    @pytest.mark.unit
    async def test_esewa_verify_success(self, client: AsyncClient, db_session: AsyncSession):
        """Valid eSewa callback data should verify successfully."""
        transaction_uuid = "esewa-uuid-test-001"

        # Pre-create a transaction as if initiation happened
        tx = PaymentTransaction(
            provider=PaymentProvider.ESEWA,
            amount=100,
            purchase_order_id="ESEWA-ORDER-001",
            purchase_order_name="Test eSewa Order",
            return_url="http://localhost:3000/callback",
            website_url="",
            status=PaymentStatus.INITIATED,
            provider_pidx=transaction_uuid,
        )
        db_session.add(tx)
        await db_session.commit()
        await db_session.refresh(tx)

        # Build the callback data blob
        callback_data = _esewa_callback_data(transaction_uuid, total_amount=100)

        # Mock the eSewa status API call
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "product_code": "EPAYTEST",
            "transaction_uuid": transaction_uuid,
            "total_amount": "100",
            "status": "COMPLETE",
            "ref_id": "ESEWA_REF_001",
        }

        mock_get_client = MagicMock()
        mock_get_client.__aenter__ = AsyncMock(return_value=mock_get_client)
        mock_get_client.__aexit__ = AsyncMock(return_value=False)
        mock_get_client.get = AsyncMock(return_value=mock_response)

        with patch("src.apps.finance.services.esewa.httpx.AsyncClient", return_value=mock_get_client):
            resp = await client.post(
                "/api/v1/payments/verify/",
                json={
                    "provider": "esewa",
                    "data": callback_data,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["transaction_id"] == tx.id

    @pytest.mark.unit
    async def test_esewa_verify_invalid_signature(self, client: AsyncClient, db_session: AsyncSession):
        """Tampered eSewa callback data should return 400."""
        bad_payload = base64.b64encode(json.dumps({
            "transaction_code": "X",
            "status": "COMPLETE",
            "total_amount": "100",
            "transaction_uuid": "uuid-tampered",
            "product_code": "EPAYTEST",
            "signed_field_names": "transaction_code,status,total_amount,transaction_uuid,product_code,signed_field_names",
            "signature": "INVALIDSIGNATURE==",
        }).encode()).decode()

        resp = await client.post(
            "/api/v1/payments/verify/",
            json={"provider": "esewa", "data": bad_payload},
        )
        assert resp.status_code == 400

    @pytest.mark.unit
    async def test_esewa_verify_missing_data(self, client: AsyncClient):
        """Verifying eSewa without data param should return 400."""
        resp = await client.post(
            "/api/v1/payments/verify/",
            json={"provider": "esewa"},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Generic transaction CRUD tests
# ---------------------------------------------------------------------------

class TestTransactionCRUD:
    """Tests for GET /payments/ and GET /payments/{id}/."""

    @pytest.mark.unit
    async def test_get_transaction_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/payments/99999/")
        assert resp.status_code == 404

    @pytest.mark.unit
    async def test_get_transaction_success(self, client: AsyncClient, db_session: AsyncSession):
        tx = PaymentTransaction(
            provider=PaymentProvider.KHALTI,
            amount=500,
            purchase_order_id="TX-READ-001",
            purchase_order_name="Read Test",
            return_url="http://localhost:3000/cb",
            website_url="",
            status=PaymentStatus.COMPLETED,
        )
        db_session.add(tx)
        await db_session.commit()
        await db_session.refresh(tx)

        resp = await client.get(f"/api/v1/payments/{tx.id}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["purchase_order_id"] == "TX-READ-001"
        assert data["status"] == "completed"

    @pytest.mark.unit
    async def test_list_transactions(self, client: AsyncClient, db_session: AsyncSession):
        for i in range(3):
            db_session.add(PaymentTransaction(
                provider=PaymentProvider.ESEWA,
                amount=100 * (i + 1),
                purchase_order_id=f"LIST-{i}",
                purchase_order_name=f"Order {i}",
                return_url="http://localhost/cb",
                website_url="",
                status=PaymentStatus.PENDING,
            ))
        await db_session.commit()

        resp = await client.get("/api/v1/payments/?provider=esewa&limit=10")
        assert resp.status_code == 200
        assert len(resp.json()) >= 3

    @pytest.mark.unit
    async def test_initiate_invalid_amount(self, client: AsyncClient):
        """amount=0 should be rejected by schema validation."""
        resp = await client.post(
            "/api/v1/payments/initiate/",
            json={
                "provider": "khalti",
                "amount": 0,
                "purchase_order_id": "BAD",
                "purchase_order_name": "Bad",
                "return_url": "http://localhost/cb",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.unit
    async def test_unsupported_provider(self, client: AsyncClient):
        """Using a disabled provider should return 503."""
        # Stripe and PayPal are disabled by default (STRIPE_ENABLED=False)
        resp = await client.post(
            "/api/v1/payments/initiate/",
            json={
                "provider": "stripe",
                "amount": 1000,
                "purchase_order_id": "STR-001",
                "purchase_order_name": "Stripe Order",
                "return_url": "http://localhost/cb",
            },
        )
        assert resp.status_code == 503  # disabled, not unsupported


# ---------------------------------------------------------------------------
# Provider enabled/disabled flag tests
# ---------------------------------------------------------------------------

class TestProviderFlags:
    """Test that the ENABLED flags gate access correctly."""

    @pytest.mark.unit
    async def test_list_enabled_providers(self, client: AsyncClient):
        """By default only khalti and esewa are enabled."""
        resp = await client.get("/api/v1/payments/providers/")
        assert resp.status_code == 200
        providers = resp.json()
        assert "khalti" in providers
        assert "esewa" in providers
        assert "stripe" not in providers
        assert "paypal" not in providers

    @pytest.mark.unit
    async def test_disabled_provider_returns_503(self, client: AsyncClient):
        """Disabled providers should return 503, not 400."""
        for provider in ("stripe", "paypal"):
            resp = await client.post(
                "/api/v1/payments/initiate/",
                json={
                    "provider": provider,
                    "amount": 1000,
                    "purchase_order_id": f"{provider}-order",
                    "purchase_order_name": "Test",
                    "return_url": "http://localhost/cb",
                },
            )
            assert resp.status_code == 503, f"{provider} should be 503 when disabled"

    @pytest.mark.unit
    async def test_stripe_enabled_flag(self, client: AsyncClient, db_session: AsyncSession):
        """When STRIPE_ENABLED=True the provider should be reachable."""
        mock_session = MagicMock()
        mock_session.id = "cs_test_abc123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_abc123"
        mock_session.payment_status = "unpaid"

        import src.apps.finance.api.v1.payment as payment_module
        from src.apps.finance.services.stripe import StripeService

        original = dict(payment_module._PROVIDERS)
        payment_module._PROVIDERS[PaymentProvider.STRIPE] = StripeService()

        with patch(
            "src.apps.finance.services.stripe.stripe.checkout.Session.create",
            return_value=mock_session,
        ):
            resp = await client.post(
                "/api/v1/payments/initiate/",
                json={
                    "provider": "stripe",
                    "amount": 1000,
                    "purchase_order_id": "STR-ENABLED-001",
                    "purchase_order_name": "Stripe Test",
                    "return_url": "http://localhost/cb",
                },
            )

        payment_module._PROVIDERS.clear()
        payment_module._PROVIDERS.update(original)

        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "stripe"
        assert data["provider_pidx"] == "cs_test_abc123"

    @pytest.mark.unit
    async def test_paypal_enabled_flag(self, client: AsyncClient, db_session: AsyncSession):
        """When PAYPAL_ENABLED=True the provider should be reachable."""
        mock_payment = MagicMock()
        mock_payment.id = "PAY-test123"
        mock_payment.state = "created"
        mock_payment.error = None
        mock_link = MagicMock()
        mock_link.rel = "approval_url"
        mock_link.href = "https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-test"
        mock_payment.links = [mock_link]
        mock_payment.create.return_value = True

        import src.apps.finance.api.v1.payment as payment_module
        from src.apps.finance.services.paypal import PayPalService

        original = dict(payment_module._PROVIDERS)
        payment_module._PROVIDERS[PaymentProvider.PAYPAL] = PayPalService()

        with patch(
            "src.apps.finance.services.paypal.paypalrestsdk.Payment",
            return_value=mock_payment,
        ):
            resp = await client.post(
                "/api/v1/payments/initiate/",
                json={
                    "provider": "paypal",
                    "amount": 1000,
                    "purchase_order_id": "PP-ENABLED-001",
                    "purchase_order_name": "PayPal Test",
                    "return_url": "http://localhost/cb",
                },
            )

        payment_module._PROVIDERS.clear()
        payment_module._PROVIDERS.update(original)

        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "paypal"
        assert data["provider_pidx"] == "PAY-test123"
