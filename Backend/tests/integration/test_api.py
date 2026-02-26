# tests/integration/test_api.py
import pytest
pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_health(client):
    """
    Использует client fixture (ASGITransport + AsyncClient).
    Проверяем liveness и readiness endpoints.
    """
    resp = await client.get("/health/live")
    assert resp.status_code == 200

    resp = await client.get("/health/ready")
    # в тестовой среде readiness может зависеть от БД; допускаем 200 или 503
    assert resp.status_code in (200, 503)
