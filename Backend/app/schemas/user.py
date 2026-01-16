"""
app/schemas/user.py
DESCRIPTION: Pydantic DTOs for user endpoints.
Using pydantic v2's ConfigDict to enable reading from ORM models via from_attributes.
"""
from pydantic import BaseModel
from pydantic import ConfigDict

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str | None = None

class UserRead(BaseModel):
    id: int
    username: str
    full_name: str | None
    role: str

    # pydantic v2: enable reading from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)
