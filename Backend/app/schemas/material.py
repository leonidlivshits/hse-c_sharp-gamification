from pydantic import BaseModel, ConfigDict
from datetime import datetime

class MaterialCreate(BaseModel):
    title: str
    description: str | None = None
    content_url: str | None = None
    author_id: int | None = None

class MaterialRead(BaseModel):
    id: int
    title: str
    description: str | None
    content_url: str | None
    published_at: datetime | None
    author_id: int | None

    model_config = ConfigDict(from_attributes=True)
