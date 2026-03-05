from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.user import UserCreate, UserRead
from app.services import user_service
from app.repositories import user_repo
from app.models.user import User as UserModel

router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    Uses user_service.register_user which should validate uniqueness, hash password, etc.
    """
    try:
        user = await user_service.register_user(db, payload.username, payload.password, payload.full_name)
    except ValueError as e:
        # service may raise ValueError for validation (e.g. username exists)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")
    return user


@router.get("/", response_model=List[UserRead])
async def list_users(limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    List users (basic).
    """
    users = await user_repo.list_users(db, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get user by id. Returns 404 if not found.
    """
    user = await db.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user