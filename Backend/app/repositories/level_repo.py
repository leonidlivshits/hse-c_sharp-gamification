# app/repositories/level_repo.py
from sqlalchemy import select
from app.models.level import Level

async def list_levels(session):
    q = select(Level).order_by(Level.required_points)
    res = await session.execute(q)
    return res.scalars().all()

async def get_current_level_for_points(session, points: int):
    # get highest level where required_points <= points
    q = select(Level).where(Level.required_points <= points).order_by(Level.required_points.desc()).limit(1)
    res = await session.execute(q)
    return res.scalars().first()
