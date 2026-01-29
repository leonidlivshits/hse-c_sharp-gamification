"""
tests/integration/test_api.py
DESCRIPTION: minimal integration test placeholder (requires running app).
"""
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health/live")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
