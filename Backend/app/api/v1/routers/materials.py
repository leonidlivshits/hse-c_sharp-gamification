from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories import material_repo

router = APIRouter()


def _material_to_dict(m):
    return {
        "id": getattr(m, "id", None),
        "title": getattr(m, "title", None),
        "description": getattr(m, "description", None),
        "content_url": getattr(m, "content_url", None),
        "published_at": getattr(m, "published_at", None),
        "author_id": getattr(m, "author_id", None),
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def list_materials(limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    items = await material_repo.list_materials(db, limit=limit, offset=offset)
    return [_material_to_dict(m) for m in items]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_material(payload: dict, db: AsyncSession = Depends(get_db)):
    # payload: {title, description?, content_url?, author_id?}
    try:
        obj = await material_repo.create_material(
            db,
            title=payload["title"],
            description=payload.get("description"),
            content_url=payload.get("content_url"),
            author_id=payload.get("author_id"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _material_to_dict(obj)
