"""
app/main.py
DESCRIPTION: FastAPI application factory. Minimal startup/shutdown wiring:
 - Initializes DB engine and creates tables on startup (for dev only).
 - Initializes Redis client on startup.
 - Includes routers.
TODO: Replace create_all with migrations (alembic) in production.
"""
from fastapi import FastAPI
from app.core.config import settings
from app.health.endpoints import router as health_router
from app.api.v1.routers import users, materials, tests as tests_router
from app.db.session import engine, Base
from app.cache.redis_client import redis_client

def create_app() -> FastAPI:
    app = FastAPI(title="HSE Gamification Backend (dev)")
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(materials.router, prefix="/api/v1/materials", tags=["materials"])
    app.include_router(tests_router.router, prefix="/api/v1/tests", tags=["tests"])

    @app.on_event("startup")
    async def on_startup():
        # create DB tables (development convenience)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # init redis client
        await redis_client.initialize()

    @app.on_event("shutdown")
    async def on_shutdown():
        await redis_client.close()
        await engine.dispose()

    return app

app = create_app()
