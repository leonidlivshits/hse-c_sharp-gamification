# app/api/v1/routers/answers.py
"""
app/api/v1/routers/answers.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.answer import AnswerCreate, AnswerRead
from app.services.answer_service import submit_answer

router = APIRouter()  # ← убран prefix="/"


@router.post("/", response_model=AnswerRead, status_code=status.HTTP_201_CREATED)
async def create_answer(payload: AnswerCreate, db: AsyncSession = Depends(get_db)):
    """
    Submit an answer (MCQ or open). Returns the saved (and possibly auto-graded) answer.
    - payload.answer_payload: for MCQ should be a stringified choice id, e.g. "12"
    """
    ans = await submit_answer(db, payload.user_id, payload.test_id, payload.question_id, payload.answer_payload)
    if not ans:
        raise HTTPException(status_code=500, detail="Failed to submit answer")
    return ans