from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories import user_repo
from app.schemas.user import UserCreate, UserRead  # если есть

router = APIRouter()


def _user_to_dict(u) -> dict:
    return {
        "id": getattr(u, "id", None),
        "username": getattr(u, "username", None),
        "full_name": getattr(u, "full_name", None),
        "role": getattr(u, "role", None),
        "created_at": getattr(u, "created_at", None),
    }


@router.post("/", response_model=UserRead | dict, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # password hashing should happen in service layer; repo expects password_hash
        # assume user_service.register_user exists; if not, use user_repo.create_user with pre-hashed password.
        from app.services.user_service import register_user  # safe lazy import
        user = await register_user(db, payload.username, payload.password, payload.full_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _user_to_dict(user)


@router.get("/", response_model=list[UserRead] | list[dict])
async def list_users(db: AsyncSession = Depends(get_db)):
    users = await user_repo.list_users(db)
    return [_user_to_dict(u) for u in users]
