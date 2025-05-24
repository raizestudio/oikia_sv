import pytest

from config import Settings

settings = Settings()


class TestInfoRoutes:
    """Test suite for /info route."""

    @pytest.mark.asyncio
    async def test_health_no_auth(self, client):
        """Test with unauthorized requests are rejected."""
        response = await client.get("/info", headers={"X-API-KEY": "invalid_key"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Could not validate credentials"}

    @pytest.mark.asyncio
    async def test_info_client(self, client, test_client):
        """Test access with a valid API key."""
        api_key, client_id = test_client
        response = await client.get("/info", headers={"X-API-KEY": api_key})
        assert response.status_code == 200
        assert response.json() == {"name": settings.app_name, "version": settings.app_version, "version_api": settings.app_api_version, "client": client_id}

    @pytest.mark.asyncio
    async def test_info_user(self, client, test_token):
        """Test access with a valid Bearer token."""
        token, user_id = test_token
        response = await client.get("/info", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == {"name": settings.app_name, "version": settings.app_version, "version_api": settings.app_api_version, "user": user_id}
