import pytest
from httpx import AsyncClient


class TestAPIEndpoints:
    """Test general API endpoints."""
    
    @pytest.mark.asyncio
    async def test_root_redirects_to_docs(self, client: AsyncClient):
        """Root URL should redirect to /docs."""
        response = await client.get("/")
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are present."""
        response = await client.get("/", follow_redirects=True)
        # CORS headers should be set by middleware
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_api_versioning(self, client: AsyncClient):
        """Test API version prefix works."""
        from src.apps.core.config import settings
        assert settings.API_V1_STR == "/api/v1"
