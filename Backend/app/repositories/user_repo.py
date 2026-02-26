"""
app/repositories/user_repo.py
DESCRIPTION: DB access layer for users. Contains only a couple of helpers.
"""
from sqlalchemy import select
from app.models.user import User

async def get_user_by_username(session, username: str):
    q = select(User).where(User.username == username)
    res = await session.execute(q)
    return res.scalars().first()

async def list_users(session, limit: int = 100):
    q = select(User).limit(limit)
    res = await session.execute(q)
    return res.scalars().all()

async def create_user(session, username: str, password_hash: str, full_name: str | None = None):
    user = User(username=username, password_hash=password_hash, full_name=full_name)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user