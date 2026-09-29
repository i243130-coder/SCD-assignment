import pytest
from httpx import AsyncClient
from unittest.mock import patch
from tests.conftest import make_complaint
import uuid

@pytest.mark.asyncio
async def test_valid_transition_open_to_in_progress(client: AsyncClient):
    c_id = uuid.uuid4()
    with patch("app.services.complaint_service.ComplaintRepository.get_by_id") as mock_get, \
         patch("app.services.complaint_service.ComplaintRepository.update") as mock_update:
        
        mock_get.return_value = make_complaint(id=c_id, status="open")
        mock_update.return_value = make_complaint(id=c_id, status="in_progress")
        
        response = await client.patch(
            f"/api/complaints/{c_id}/status",
            json={"status": "in_progress"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"

@pytest.mark.asyncio
async def test_valid_transition_in_progress_to_resolved(client: AsyncClient):
    c_id = uuid.uuid4()
    with patch("app.services.complaint_service.ComplaintRepository.get_by_id") as mock_get, \
         patch("app.services.complaint_service.ComplaintRepository.update") as mock_update:
        
        mock_get.return_value = make_complaint(id=c_id, status="in_progress")
        mock_update.return_value = make_complaint(id=c_id, status="resolved")
        
        response = await client.patch(
            f"/api/complaints/{c_id}/status",
            json={"status": "resolved"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

@pytest.mark.asyncio
async def test_invalid_transition_open_to_resolved(client: AsyncClient):
    c_id = uuid.uuid4()
    with patch("app.services.complaint_service.ComplaintRepository.get_by_id") as mock_get:
        
        mock_get.return_value = make_complaint(id=c_id, status="open")
        
        response = await client.patch(
            f"/api/complaints/{c_id}/status",
            json={"status": "resolved"}
        )
        assert response.status_code == 409
        assert "Cannot transition from 'open' to 'resolved'" in response.json()["detail"]

@pytest.mark.asyncio
async def test_terminal_state_rejected(client: AsyncClient):
    c_id = uuid.uuid4()
    with patch("app.services.complaint_service.ComplaintRepository.get_by_id") as mock_get:
        
        mock_get.return_value = make_complaint(id=c_id, status="rejected")
        
        response = await client.patch(
            f"/api/complaints/{c_id}/status",
            json={"status": "open"}
        )
        assert response.status_code == 409
        assert "Cannot transition from 'rejected' to 'open'" in response.json()["detail"]
