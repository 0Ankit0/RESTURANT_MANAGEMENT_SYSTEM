import pytest
from httpx import AsyncClient


class TestLogout:
    """Test logout endpoint."""
    
    @pytest.mark.asyncio
    async def test_logout_requires_auth(self, client: AsyncClient):
        """Test logout requires authentication."""
        response = await client.post("/api/v1/auth/logout/")
        
        assert response.status_code == 401
