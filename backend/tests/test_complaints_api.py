import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from tests.conftest import make_complaint
import uuid

@pytest.mark.asyncio
async def test_create_complaint_success(client: AsyncClient):
    with patch("app.services.complaint_service.ComplaintRepository.create") as mock_create:
        mock_create.return_value = make_complaint()
        response = await client.post(
            "/api/complaints",
            json={
                "text": "Water pipe burst near the main road causing flooding",
                "location": "Block 5, Gulshan"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "water"
        assert data["priority"] == "high"
        assert data["status"] == "open"

@pytest.mark.asyncio
async def test_get_complaint_by_id(client: AsyncClient):
    c_id = uuid.uuid4()
    with patch("app.routes.complaints.ComplaintRepository.get_by_id") as mock_get:
        mock_get.return_value = make_complaint(id=c_id)
        response = await client.get(f"/api/complaints/{c_id}")
        assert response.status_code == 200
        assert response.json()["id"] == str(c_id)

@pytest.mark.asyncio
async def test_get_complaint_not_found(client: AsyncClient):
    with patch("app.routes.complaints.ComplaintRepository.get_by_id") as mock_get:
        mock_get.return_value = None
        response = await client.get(f"/api/complaints/{uuid.uuid4()}")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_list_complaints_pagination(client: AsyncClient):
    with patch("app.routes.complaints.ComplaintRepository.list_complaints") as mock_list:
        mock_list.return_value = ([make_complaint(), make_complaint()], 2)
        response = await client.get("/api/complaints?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 10
