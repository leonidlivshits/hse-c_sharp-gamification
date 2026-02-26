"""
tests/unit/test_smoke.py
DESCRIPTION: minimal pytest smoke test (async).
"""
import pytest
pytestmark = pytest.mark.asyncio
import asyncio

@pytest.mark.asyncio
async def test_smoke():
    assert 1 + 1 == 2
