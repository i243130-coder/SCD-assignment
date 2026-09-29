import pytest
from httpx import AsyncClient
from unittest.mock import patch
from tests.conftest import make_complaint
from app.providers.triage.simulated import SimulatedTriage
from app.providers.triage.rules import RuleBasedTriage

@pytest.mark.asyncio
async def test_simulated_provider_deterministic():
    provider = SimulatedTriage()
    result1 = await provider.triage("Water leak", "Main St")
    result2 = await provider.triage("Water leak", "Main St")
    assert result1.category == result2.category
    assert result1.priority == result2.priority

@pytest.mark.asyncio
async def test_rules_provider_water_keywords():
    provider = RuleBasedTriage()
    result = await provider.triage("The water pipe is broken", "Block A")
    assert result.category == "water"

@pytest.mark.asyncio
async def test_provider_failure_triggers_fallback(client: AsyncClient):
    with patch("app.services.complaint_service.ComplaintRepository.create") as mock_create, \
         patch("app.providers.triage.simulated.SimulatedTriage.triage") as mock_triage:
        
        # Simulate provider failure
        mock_triage.side_effect = Exception("Provider failed")
        
        # The service should fallback to rules provider
        mock_create.side_effect = lambda c: make_complaint(**{k: getattr(c, k) for k in ['text', 'location', 'category', 'priority', 'status', 'triaged_by']})
        
        response = await client.post(
            "/api/complaints",
            json={"text": "Water pipe is broken badly", "location": "123 Main St"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["triaged_by"] == "rules:fallback"

@pytest.mark.asyncio
async def test_malformed_output_handled(client: AsyncClient):
    with patch("app.services.complaint_service.ComplaintRepository.create") as mock_create, \
         patch("app.providers.triage.simulated.SimulatedTriage.triage") as mock_triage:
        
        # Simulate malformed output (e.g. ValueError during parsing inside provider, or similar)
        # We can just raise ValueError to simulate it
        mock_triage.side_effect = ValueError("Malformed output")
        
        mock_create.side_effect = lambda c: make_complaint(**{k: getattr(c, k) for k in ['text', 'location', 'category', 'priority', 'status', 'triaged_by']})
        
        response = await client.post(
            "/api/complaints",
            json={"text": "Electric wire fell down", "location": "Downtown"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "fallback" in data["triaged_by"] or "rules" in data["triaged_by"]
