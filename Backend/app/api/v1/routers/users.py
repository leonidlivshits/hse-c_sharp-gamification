"""
app/api/v1/routers/users.py
DESCRIPTION: simple user CRUD endpoints (minimal, for demo).
"""
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate, UserRead
from app.api.deps import get_db
from app.services import user_service
from app.repositories import user_repo

router = APIRouter()

@router.post("/", response_model=UserRead)
async def create_user(payload: UserCreate, db=Depends(get_db)):
    try:
        user = await user_service.register_user(db, payload.username, payload.password, payload.full_name)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[UserRead])
async def list_users(db=Depends(get_db)):
    users = await user_repo.list_users(db)
    return users
