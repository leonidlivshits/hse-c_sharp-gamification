"""
app/schemas/user.py
DESCRIPTION: Pydantic DTOs for user endpoints.
"""
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str | None = None

class UserRead(BaseModel):
    id: int
    username: str
    full_name: str | None
    role: str

    class Config:
        orm_mode = True
