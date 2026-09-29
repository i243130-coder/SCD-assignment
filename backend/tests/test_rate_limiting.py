import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from tests.conftest import make_complaint

@pytest.mark.asyncio
async def test_rate_limit_allows_within_limit(client: AsyncClient, mock_session):
    # When redis eval returns -1 (allowed), request proceeds
    complaint_obj = make_complaint()
    with patch("app.services.complaint_service.ComplaintRepository.create", return_value=complaint_obj):
        response = await client.post(
            "/api/complaints",
            json={"text": "Water pipe burst loudly", "location": "123 Main"}
        )
        assert response.status_code == 201

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
