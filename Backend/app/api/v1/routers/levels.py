from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories import level_repo

router = APIRouter()


@router.get("/", status_code=200)
async def list_levels(db: AsyncSession = Depends(get_db)):
    levels = await level_repo.list_levels(db)
    return [{"id": l.id, "name": l.name, "required_points": l.required_points, "description": l.description} for l in levels]


@router.get("/by-points", status_code=200)
async def get_current_level(points: int, db: AsyncSession = Depends(get_db)):
    lvl = await level_repo.get_current_level_for_points(db, points)
    if not lvl:
        raise HTTPException(status_code=404, detail="Level not found")
    return {"id": lvl.id, "name": lvl.name, "required_points": lvl.required_points, "description": lvl.description}
