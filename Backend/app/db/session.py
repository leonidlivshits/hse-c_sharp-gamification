"""
app/db/session.py
DESCRIPTION: async SQLAlchemy engine & async_sessionmaker using settings.get_database_url()
- Uses SQLAlchemy 2.0 async engine (asyncpg).
- Export Base, engine, AsyncSessionLocal.
"""
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

Base = declarative_base()

DATABASE_URL = settings.get_database_url()

# create async engine
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    # pool size / tuning can be added here per env
)

# session factory
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
