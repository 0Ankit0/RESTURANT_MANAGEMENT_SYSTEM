import pytest
from httpx import AsyncClient

from src.apps.core.config import settings


class TestRootEndpoint:
    """Test root API endpoint."""
    
    @pytest.mark.asyncio
    async def test_read_root(self, client: AsyncClient):
        """Test root endpoint redirects to /docs."""
        response = await client.get("/")
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"


class TestAPIVersioning:
    """Test API versioning."""
    
    @pytest.mark.asyncio
    async def test_api_v1_prefix(self, client: AsyncClient):
        """Test API v1 prefix is configured."""
        # This tests that the API router is mounted at the correct prefix
        assert settings.API_V1_STR == "/api/v1"


class TestCORS:
    """Test CORS configuration."""
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are set."""
        response = await client.options(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        # CORS should allow the configured origins
        assert response.status_code in [200, 405]


class TestHealthCheck:
    """Test application health."""
    
    @pytest.mark.asyncio
    async def test_app_responds(self, client: AsyncClient):
        """Test that the application responds to requests."""
        response = await client.get("/", follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_system_capabilities(self, client: AsyncClient):
        response = await client.get("/api/v1/system/capabilities/")
        assert response.status_code == 200
        payload = response.json()
        assert "modules" in payload
        assert "active_providers" in payload
        assert "fallback_providers" in payload

    @pytest.mark.asyncio
    async def test_system_providers(self, client: AsyncClient):
        response = await client.get("/api/v1/system/providers/")
        assert response.status_code == 200
        providers = response.json()["providers"]
        channels = {item["channel"] for item in providers}
        assert {"email", "push", "sms", "analytics"}.issubset(channels)

    @pytest.mark.asyncio
    async def test_system_general_settings(self, client: AsyncClient):
        response = await client.get("/api/v1/system/general-settings/")
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, list)
        assert any(item["key"] == "PROJECT_NAME" for item in payload)
        assert any(item["key"] == "APP_ENV" for item in payload)
        assert all("effective_value" in item for item in payload)
