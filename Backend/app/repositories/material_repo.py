"""
Repository for Material entity.
"""
from sqlalchemy import select
from app.models.material import Material

async def get_material(session, material_id: int):
    q = select(Material).where(Material.id == material_id)
    res = await session.execute(q)
    return res.scalars().first()

async def list_materials(session, limit: int = 100, offset: int = 0):
    q = select(Material).limit(limit).offset(offset)
    res = await session.execute(q)
    return res.scalars().all()

async def create_material(session, title: str, description: str | None = None, content_url: str | None = None, author_id: int | None = None):
    obj = Material(title=title, description=description, content_url=content_url, author_id=author_id)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj
