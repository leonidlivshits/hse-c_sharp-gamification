from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AnswerCreate(BaseModel):
    user_id: int
    test_id: int
    question_id: int
    # payload: for MCQ: choice id (as int), for open: text
    answer_payload: str

class AnswerRead(BaseModel):
    id: int
    user_id: int
    test_id: int
    question_id: int
    answer_payload: str
    score: float | None
    graded_by: int | None
    graded_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
