from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AnalyticsRead(BaseModel):
    user_id: int
    total_points: float
    tests_taken: int
    last_active: datetime | None
    streak_days: int
    current_level_id: int | None

    model_config = ConfigDict(from_attributes=True)
