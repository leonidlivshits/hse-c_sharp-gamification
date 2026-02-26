from pydantic import BaseModel, ConfigDict
from datetime import datetime

class TestCreate(BaseModel):
    __test__ = False 
    title: str
    description: str | None = None
    time_limit_minutes: int | None = None
    max_score: int | None = None
    published: bool = False
    material_id: int | None = None

class TestRead(BaseModel):
    __test__ = False 
    id: int
    title: str
    description: str | None
    time_limit_minutes: int | None
    max_score: int | None
    published: bool
    published_at: datetime | None
    material_id: int | None

    model_config = ConfigDict(from_attributes=True)
