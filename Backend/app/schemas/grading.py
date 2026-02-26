# app/schemas/grading.py
from pydantic import BaseModel, ConfigDict

class GradeRequest(BaseModel):
    answer_id: int
    grader_id: int
    score: float
    comment: str | None = None

class GradeResponse(BaseModel):
    answer_id: int
    score: float

    model_config = ConfigDict(from_attributes=True)
