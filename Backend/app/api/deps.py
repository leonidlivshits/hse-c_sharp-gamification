# app/api/deps.py
"""
Dependency helpers for FastAPI.
Provides get_db() as an async generator (FastAPI compatible).
"""
from typing import AsyncGenerator
from app.db.session import AsyncSessionLocal

async def get_db() -> AsyncGenerator:
    """
    Provide a DB session to FastAPI endpoints.
    Use as: db = Depends(get_db)
    This function must be an async generator (yield) — FastAPI will cleanup automatically.
    """
    async with AsyncSessionLocal() as session:
        yield session
