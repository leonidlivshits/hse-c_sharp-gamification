from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories import test_repo

router = APIRouter()


def _test_to_dict(t):
    return {
        "id": getattr(t, "id", None),
        "title": getattr(t, "title", None),
        "description": getattr(t, "description", None),
        "time_limit_minutes": getattr(t, "time_limit_minutes", None),
        "max_score": getattr(t, "max_score", None),
        "published": getattr(t, "published", None),
        "published_at": getattr(t, "published_at", None),
        "material_id": getattr(t, "material_id", None),
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def list_tests(published_only: bool = True, limit: int = 100, db: AsyncSession = Depends(get_db)):
    items = await test_repo.list_tests(db, published_only=published_only, limit=limit)
    return [_test_to_dict(t) for t in items]


@router.get("/{test_id}", status_code=status.HTTP_200_OK)
async def get_test(test_id: int, db: AsyncSession = Depends(get_db)):
    t = await test_repo.get_test(db, test_id)
    if not t:
        raise HTTPException(status_code=404, detail="Test not found")
    return _test_to_dict(t)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_test(payload: dict, db: AsyncSession = Depends(get_db)):
    # payload keys: title, description?, time_limit_minutes?, max_score?, material_id?
    try:
        test = await test_repo.create_test(
            db,
            title=payload["title"],
            description=payload.get("description"),
            time_limit_minutes=payload.get("time_limit_minutes"),
            max_score=payload.get("max_score"),
            material_id=payload.get("material_id"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _test_to_dict(test)


@router.get("/{test_id}/summary", status_code=status.HTTP_200_OK)
async def test_summary(test_id: int, db: AsyncSession = Depends(get_db)):
    summary = await test_repo.test_summary(db, test_id)
    return summary
