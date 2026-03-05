from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.test_ import TestCreate, TestRead
from app.repositories import test_repo

router = APIRouter()


@router.get("/", response_model=List[TestRead], status_code=status.HTTP_200_OK)
async def list_tests(published_only: bool = True, limit: int = 100, db: AsyncSession = Depends(get_db)):
    items = await test_repo.list_tests(db, published_only=published_only, limit=limit)
    return items


@router.get("/{test_id}", response_model=TestRead, status_code=status.HTTP_200_OK)
async def get_test(test_id: int, db: AsyncSession = Depends(get_db)):
    t = await test_repo.get_test(db, test_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    return t


@router.post("/", response_model=TestRead, status_code=status.HTTP_201_CREATED)
async def create_test(payload: TestCreate, db: AsyncSession = Depends(get_db)):
    test = await test_repo.create_test(
        db,
        title=payload.title,
        description=payload.description,
        time_limit_minutes=payload.time_limit_minutes,
        max_score=payload.max_score,
        material_id=payload.material_id,
    )
    return test


@router.get("/{test_id}/summary", status_code=status.HTTP_200_OK)
async def test_summary(test_id: int, db: AsyncSession = Depends(get_db)):
    summary = await test_repo.get_test_summary(db, test_id)
    return summary