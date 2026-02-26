from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class AnalyticsRead(BaseModel):
    user_id: int
    total_points: float
    tests_taken: int
    last_active: datetime | None
    streak_days: int
    current_level_id: int | None

    model_config = ConfigDict(from_attributes=True)

class LeaderboardEntry(BaseModel):
    user_id: int
    username: str
    total_points: float

    model_config = ConfigDict(from_attributes=True)

class TestSummary(BaseModel):
    test_id: int
    total_questions: int
    total_attempts: int
    avg_score: float | None

    model_config = ConfigDict(from_attributes=True)

class QuestionStats(BaseModel):
    question_id: int
    attempts: int
    avg_score: float | None
    correct_count: int
    correct_rate: float | None
    distinct_users: int

    model_config = ConfigDict(from_attributes=True)