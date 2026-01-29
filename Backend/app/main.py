"""
app/main.py
DESCRIPTION: FastAPI application factory with resilient startup:
- waits for DB availability with retries
- creates tables in dev (create_all) -- keep only for dev convenience
- initializes redis client
NOTE: remove create_all in production and use alembic migrations.
"""
import asyncio
import logging

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.health.endpoints import router as health_router
from app.api.v1.routers import users, materials, tests as tests_router
from app.db.session import engine, Base
from app.cache.redis_client import redis_client

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="HSE Gamification Backend (dev)")

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(materials.router, prefix="/api/v1/materials", tags=["materials"])
    app.include_router(tests_router.router, prefix="/api/v1/tests", tags=["tests"])

    @app.on_event("startup")
    async def on_startup():
        # Retry loop for DB availability.
        max_wait = 60  # seconds total
        interval = 2   # seconds between tries
        waited = 0
        last_exc = None
        while waited < max_wait:
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                logger.info("Database is available")
                break
            except Exception as exc:
                last_exc = exc
                logger.warning("Database not ready, retrying in %s seconds: %s", interval, exc)
                await asyncio.sleep(interval)
                waited += interval
        else:
            logger.error("Could not connect to database after %s seconds: %s", max_wait, last_exc)
            # don't raise — keep app running (readiness probe will be unhealthy).
            # If you need fail-fast in CI/prod, raise here.

        # For development convenience only: create tables if DB accessible
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schema ensured (create_all)")
        except OperationalError as e:
            logger.warning("Skipping create_all because DB not available: %s", e)
        except Exception as e:
            logger.warning("create_all skipped: %s", e)

        # init redis
        try:
            await redis_client.initialize()
            logger.info("Redis client initialized")
        except Exception as e:
            logger.warning("Redis init failed: %s", e)

    @app.on_event("shutdown")
    async def on_shutdown():
        try:
            await redis_client.close()
        except Exception:
            pass
        await engine.dispose()

    return app


app = create_app()
