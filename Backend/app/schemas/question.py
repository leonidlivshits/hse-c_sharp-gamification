from pydantic import BaseModel, ConfigDict
from typing import List

class ChoiceCreate(BaseModel):
    value: str
    ordinal: int | None = None
    is_correct: bool = False

class ChoiceRead(BaseModel):
    id: int
    question_id: int
    value: str
    ordinal: int | None
    is_correct: bool

    model_config = ConfigDict(from_attributes=True)

class QuestionCreate(BaseModel):
    test_id: int
    text: str
    points: float = 1.0
    is_open_answer: bool = False
    choices: List[ChoiceCreate] | None = None

class QuestionRead(BaseModel):
    id: int
    test_id: int
    text: str
    points: float
    is_open_answer: bool
    choices: List[ChoiceRead] | None = None

    model_config = ConfigDict(from_attributes=True)
