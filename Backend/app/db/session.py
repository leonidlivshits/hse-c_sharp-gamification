"""
app/db/session.py
DESCRIPTION: async SQLAlchemy engine & sessionmaker.
"""
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

Base = declarative_base()

# Async engine for SQLAlchemy 2.0
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    future=True,
    echo=False,
    # pool sizing can be tuned per env
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
