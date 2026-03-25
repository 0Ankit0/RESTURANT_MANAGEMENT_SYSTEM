import pytest
from httpx import AsyncClient


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_nonexistent_endpoint(self, client: AsyncClient):
        """Test accessing nonexistent endpoint."""
        response = await client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_missing_authentication(self, client: AsyncClient):
        """Test accessing protected endpoint without authentication."""
        response = await client.post("/api/v1/auth/logout/")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_malformed_request(self, client: AsyncClient):
        """Test API handles malformed requests."""
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            json={"invalid": "data"}
        )
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_invalid_json(self, client: AsyncClient):
        """Test API handles invalid JSON."""
        response = await client.post(
            "/api/v1/auth/login/?set_cookie=false",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
