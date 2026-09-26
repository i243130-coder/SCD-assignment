import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_session
from app.redis_client import get_redis
from app.providers.triage.factory import reset_provider

# Create mock session and redis
class FakeRedis:
    def __init__(self):
        self._store = {}
    async def get(self, key): 
        if isinstance(key, bytes):
            key = key.decode()
        val = self._store.get(key)
        if isinstance(val, str):
            return val.encode()
        return val
    async def set(self, key, value): 
        if isinstance(key, bytes):
            key = key.decode()
        if isinstance(value, bytes):
            value = value.decode()
        self._store[key] = value
    async def setex(self, key, ttl, value):
        if isinstance(key, bytes):
            key = key.decode()
        if isinstance(value, bytes):
            value = value.decode()
        self._store[key] = value
    async def delete(self, key): 
        if isinstance(key, bytes):
            key = key.decode()
        self._store.pop(key, None)
    async def incr(self, key): 
        if isinstance(key, bytes):
            key = key.decode()
        self._store[key] = int(self._store.get(key, 0)) + 1
        return self._store[key]
    async def expire(self, key, ttl, nx=False): pass
    async def ttl(self, key): return 60
    async def eval(self, script, numkeys, *args): return -1  # allow all requests
    async def ping(self): return True
    async def aclose(self): pass

# Mock complaint for repository returns
def make_complaint(**overrides):
    defaults = {
        'id': uuid.uuid4(),
        'text': 'Water pipe burst near the main road causing flooding',
        'location': 'Block 5, Gulshan',
        'reporter_contact': None,
        'category': 'water',
        'priority': 'high',
        'status': 'open',
        'ai_summary': '[Simulated] Issue reported',
        'triaged_by': 'simulated',
        'triage_latency_ms': 5,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock(**defaults)
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock

@pytest.fixture
def mock_session():
    session = AsyncMock()
    return session

@pytest.fixture
def fake_redis():
    return FakeRedis()

@pytest.fixture
async def client(mock_session, fake_redis):
    app.dependency_overrides[get_session] = lambda: mock_session
    app.dependency_overrides[get_redis] = lambda: fake_redis
    import os
    os.environ["TRIAGE_PROVIDER"] = "simulated"
    reset_provider()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
        
    app.dependency_overrides.clear()
    reset_provider()

@pytest.fixture
def sample_complaint():
    return make_complaint()
