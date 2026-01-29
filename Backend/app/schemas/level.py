from pydantic import BaseModel, ConfigDict

class LevelRead(BaseModel):
    id: int
    name: str
    required_points: int
    description: str | None

    model_config = ConfigDict(from_attributes=True)
