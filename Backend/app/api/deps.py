# app/api/deps.py
"""
app/api/deps.py
DESCRIPTION: dependency utilities (DB session) for FastAPI.
"""
from contextlib import asynccontextmanager
from app.db.session import AsyncSessionLocal

@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
