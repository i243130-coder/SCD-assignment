import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from tests.conftest import make_complaint

@pytest.mark.asyncio
async def test_rate_limit_allows_within_limit(client: AsyncClient):
    """Rate limiter allows requests when under the limit (FakeRedis.eval returns -1)."""
    # FakeRedis.eval returns -1 by default (allow), so requests should go through.
    # We just need to verify the request doesn't get a 429.
    with patch("app.services.complaint_service.ComplaintRepository.create", new_callable=AsyncMock) as mock_create:
        from tests.conftest import make_complaint
        mock_create.return_value = make_complaint()
        
        response = await client.post(
            "/api/complaints",
            json={"text": "Water pipe burst loudly near the road", "location": "123 Main"}
        )
        # Should not be rate limited — any status except 429 is acceptable
        assert response.status_code != 429

@pytest.mark.asyncio
async def test_rate_limit_blocks_over_limit(client: AsyncClient):
    with patch("tests.conftest.FakeRedis.eval", new_callable=AsyncMock) as mock_eval:
        mock_eval.return_value = 30  # Retry after 30s
        
        response = await client.post(
            "/api/complaints",
            json={"text": "Water pipe burst loudly", "location": "123 Main"}
        )
        assert response.status_code == 429
        assert response.headers.get("Retry-After") == "30"
