import pytest
from httpx import AsyncClient
from unittest.mock import patch
from tests.conftest import make_complaint

@pytest.mark.asyncio
async def test_stats_cache_miss_then_hit(client: AsyncClient):
    with patch("app.repositories.complaint_repo.ComplaintRepository.get_stats") as mock_stats:
        mock_stats.return_value = {
            "categories": [{"category": "water", "count": 1}],
            "priorities": [{"priority": "high", "count": 1}],
            "total": 1
        }
        
        # First call (Miss)
        response1 = await client.get("/api/stats")
        assert response1.status_code == 200
        assert response1.headers.get("X-Cache") == "MISS"
        
        # Second call (Hit)
        response2 = await client.get("/api/stats")
        assert response2.status_code == 200
        assert response2.headers.get("X-Cache") == "HIT"

@pytest.mark.asyncio
async def test_cache_invalidation_on_write(client: AsyncClient):
    with patch("app.repositories.complaint_repo.ComplaintRepository.get_stats") as mock_stats, \
         patch("app.services.complaint_service.ComplaintRepository.create") as mock_create:
        
        mock_stats.return_value = {
            "categories": [],
            "priorities": [],
            "total": 0
        }
        mock_create.return_value = make_complaint()
        
        # Get stats -> MISS, caches it
        r1 = await client.get("/api/stats")
        assert r1.headers.get("X-Cache") == "MISS"
        
        # Create complaint -> invalidates cache
        await client.post("/api/complaints", json={"text": "Water pipe broken loudly near house", "location": "123 Main"})
        
        # Get stats again -> MISS (because cache was invalidated)
        r2 = await client.get("/api/stats")
        assert r2.headers.get("X-Cache") == "MISS"
