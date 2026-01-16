"""
app/health/endpoints.py
DESCRIPTION: liveness and readiness endpoints. Extend checks as needed.
"""
from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import engine
from app.cache.redis_client import redis_client

router = APIRouter()

@router.get("/live")
async def liveness():
    return {"status": "ok"}

@router.get("/ready")
async def readiness():
    # basic checks: DB connect and redis ping
    try:
        async with engine.connect() as conn:
            # use sa.text to avoid "Not an executable object" error
            await conn.execute(text("SELECT 1"))
        r = await redis_client.get()
        await r.ping()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "reason": str(e)}
