import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complaint_text_too_short(client: AsyncClient):
    response = await client.post(
        "/api/complaints",
        json={
            "text": "Too short",
            "location": "Main Street"
        }
    )
    assert response.status_code == 422
    assert "String should have at least 10 characters" in response.text or "text" in response.text

@pytest.mark.asyncio
async def test_complaint_text_too_long(client: AsyncClient):
    response = await client.post(
        "/api/complaints",
        json={
            "text": "A" * 2001,
            "location": "Main Street"
        }
    )
    assert response.status_code == 422
    assert "String should have at most 2000 characters" in response.text or "text" in response.text

@pytest.mark.asyncio
async def test_complaint_location_too_short(client: AsyncClient):
    response = await client.post(
        "/api/complaints",
        json={
            "text": "This is a valid text longer than 10 chars",
            "location": "ab"
        }
    )
    assert response.status_code == 422
    assert "String should have at least 3 characters" in response.text or "location" in response.text
