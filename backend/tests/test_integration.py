import pytest
from httpx import AsyncClient
from unittest.mock import patch
from tests.conftest import make_complaint
import uuid

@pytest.mark.asyncio
async def test_full_complaint_lifecycle(client: AsyncClient):
    c_id = uuid.uuid4()
    
    # We will simulate the DB holding a complaint state
    db_state = {}
    
    def mock_create(complaint):
        db_state[complaint.id] = complaint
        return complaint
        
    def mock_get(complaint_id):
        return db_state.get(complaint_id)
        
    def mock_update(complaint_id, status):
        if complaint_id in db_state:
            db_state[complaint_id].status = status
            return db_state[complaint_id]
        return None

    with patch("app.services.complaint_service.ComplaintRepository.create", side_effect=mock_create), \
         patch("app.routes.complaints.ComplaintRepository.get_by_id", side_effect=mock_get), \
         patch("app.services.complaint_service.ComplaintRepository.get_by_id", side_effect=mock_get), \
         patch("app.services.complaint_service.ComplaintRepository.update_status", side_effect=mock_update):
        
        # 1. Create
        response = await client.post(
            "/api/complaints",
            json={"text": "Water pipe leak in my street", "location": "Main St"}
        )
        assert response.status_code == 201
        data = response.json()
        complaint_id = uuid.UUID(data["id"])
        assert data["status"] == "open"
        assert data["category"] is not None
        
        # 2. Get
        response = await client.get(f"/api/complaints/{complaint_id}")
        assert response.status_code == 200
        assert response.json()["id"] == str(complaint_id)
        assert response.json()["status"] == "open"
        
        # 3. Update Status
        response = await client.patch(
            f"/api/complaints/{complaint_id}/status",
            json={"status": "in_progress"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
        
        # 4. Verify Update
        response = await client.get(f"/api/complaints/{complaint_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
