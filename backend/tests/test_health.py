import pytest
from httpx import AsyncClient
from unittest.mock import patch

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    with patch("app.database.get_session") as mock_session:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_session.assert_not_called()

@pytest.mark.asyncio
async def test_ready_endpoint_healthy(client: AsyncClient):
    # Depending on how /ready is implemented, we might need to mock dependencies
    with patch("app.database.get_session"), patch("app.redis_client.get_redis"):
        # The fake redis ping returns True
        # For db we might need to mock session.execute
        pass
    
    # Simple approach, rely on the fake_redis and mock_session from client fixture
    # but we need the DB check to pass. Let's mock the check if necessary.
    with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
        mock_execute.return_value = True
        response = await client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
