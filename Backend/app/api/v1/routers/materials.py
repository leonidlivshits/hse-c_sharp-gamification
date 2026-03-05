from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.material import MaterialCreate, MaterialRead
from app.repositories import material_repo

router = APIRouter()


@router.get("/", response_model=List[MaterialRead], status_code=status.HTTP_200_OK)
async def list_materials(limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """
    List published materials (or all, depending on repo implementation).
    """
    items = await material_repo.list_materials(db, limit=limit, offset=offset)
    return items


@router.get("/{material_id}", response_model=MaterialRead, status_code=status.HTTP_200_OK)
async def get_material(material_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a single material by id.
    """
    m = await material_repo.get_material(db, material_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return m


@router.post("/", response_model=MaterialRead, status_code=status.HTTP_201_CREATED)
async def create_material(payload: MaterialCreate, db: AsyncSession = Depends(get_db)):
    """
    Create material. For now no auth check is performed here — consider adding later.
    """
    try:
        m = await material_repo.create_material(
            db,
            title=payload.title,
            description=payload.description,
            content_url=payload.content_url,
            author_id=payload.author_id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return m
