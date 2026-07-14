import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.admin import setup_admin
from app.api.v1.routers import (
    ai,
    analytics,
    analytics_levels,
    answers,
    auth,
    choices,
    groups,
    levels,
    materials,
    questions,
    tests,
    users,
)
from app.cache import redis_cache
from app.core.config import settings
from app.db.session import Base, engine
from app.health.endpoints import router as health_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_metrics import RequestMetricsMiddleware
from app.observability.prometheus_router import router as prometheus_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        max_wait = 60
        interval = 2
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

        if settings.db_auto_create:
            try:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("Database schema ensured (create_all)")
            except OperationalError as exc:
                logger.warning("Skipping create_all because DB not available: %s", exc)
            except Exception as exc:
                logger.warning("create_all skipped: %s", exc)

        try:
            await redis_cache.initialize()
            logger.info("Redis cache initialized")
        except Exception as exc:
            logger.warning("Redis init failed: %s", exc)

        try:
            yield
        finally:
            try:
                await redis_cache.close()
            except Exception:
                pass
            await engine.dispose()

    app = FastAPI(title="HSE Gamification Backend", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    if settings.monitoring_enabled:
        app.add_middleware(RequestMetricsMiddleware)

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(prometheus_router, tags=["metrics"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(materials.router, prefix="/api/v1/materials", tags=["materials"])
    app.include_router(tests.router, prefix="/api/v1/tests", tags=["tests"])
    app.include_router(answers.router, prefix="/api/v1/answers", tags=["answers"])
    app.include_router(choices.router, prefix="/api/v1/choices", tags=["choices"])
    app.include_router(levels.router, prefix="/api/v1/levels", tags=["levels"])
    app.include_router(questions.router, prefix="/api/v1/questions", tags=["questions"])
    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
    app.include_router(analytics_levels.router, prefix="/api/v1/analytics", tags=["analytics"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
    app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
    setup_admin(app)
    return app


app = create_app()
